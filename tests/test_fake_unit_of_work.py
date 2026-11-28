"""
Tests for the fake unit of work and its fake repositories.

The fake must stand in for the real unit of work in a service test: keep
rows in memory, commit and roll back as the real one does, refuse the same
nesting, and answer every faked repository method as the SQL does.
"""

import copy
import inspect
import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.mocks.fake_unit_of_work import (
    FakeClientRepository,
    FakeMeetingsRepository,
    FakeNotesRepository,
    FakeSystemStateRepository,
    FakeTaskStatusRepository,
    FakeTimeEntriesRepository,
    FakeUnitOfWork,
)
from workmain.database.models import (
    Meeting,
    Note,
    Project,
    Report,
    ReportRecipient,
    TimeEntry,
)
from workmain.database.repositories.client_repository import ClientRepository
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.reports_repo import ReportsRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.services.unit_of_work import (
    _OPEN_SCOPE_MESSAGE,
    _REENTRY_MESSAGE,
    UnitOfWork,
)

_REENTRY = re.escape(_REENTRY_MESSAGE)
_OPEN_SCOPE = re.escape(_OPEN_SCOPE_MESSAGE)


def _seed_projects(kind: str, db_session: Session, store: dict) -> tuple[int, int, int]:
    """Seed two clients and a project of the first; return both client ids and the project id."""
    if kind == 'real':
        clients = ClientRepository(db_session)
        owner_id = clients.create('ZqvProjectOwner').id
        other_id = clients.create('ZqvProjectOther').id
        project = Project(name='ZqvProject', client_id=owner_id)
        db_session.add(project)
        db_session.flush()
        return owner_id, other_id, project.id
    store['projects'] = {5: {'id': 5, 'client_id': 1}}
    return 1, 2, 5


def _seed_meeting(
    kind: str, db_session: Session, store: dict, title: str, start: datetime
) -> int:
    """Seed a one-hour meeting and return its id."""
    end = start + timedelta(hours=1)
    if kind == 'real':
        return MeetingsRepository(db_session).create(
            title=title, start_time=start, end_time=end,
        ).id
    rows = store.setdefault('meetings', {})
    meeting_id = max(rows, default=0) + 1
    rows[meeting_id] = {
        'id': meeting_id, 'title': title, 'client_id': None, 'start_time': start,
        'end_time': end, 'condensed_summary': None, 'condensed_at': None,
    }
    return meeting_id


def _seed_note(
    kind: str, db_session: Session, store: dict, content: str, meeting_id: int | None = None
) -> int:
    """Seed an internal-only note and return its id."""
    stamp = datetime(2099, 1, 2, 9, 0)
    if kind == 'real':
        return NotesRepository(db_session).create(
            content=content, tags=['internal-only'], meeting_id=meeting_id, created_at=stamp,
        ).id
    rows = store.setdefault('notes', {})
    note_id = max(rows, default=0) + 1
    rows[note_id] = {
        'id': note_id, 'content': content, 'tags': ['internal-only'], 'source': 'ad-hoc',
        'created_at': stamp, 'meeting_id': meeting_id, 'project_id': None, 'client_id': None,
    }
    return note_id


class TestFakeUnitOfWork:
    """The fake keeps rows in memory, commits and rolls back, and is entered once."""

    def test_value_set_is_returned(self) -> None:
        with FakeUnitOfWork() as uow:
            uow.system_state.set('colour', 'blue')
            assert uow.system_state.get('colour') == 'blue'

    def test_normal_exit_sets_committed(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            uow.system_state.set('colour', 'blue')
        assert uow.committed is True
        assert uow.rolled_back is False

    def test_exception_restores_store_and_sets_rolled_back(self) -> None:
        store = {'system_state': {'colour': 'red'}}
        expected = copy.deepcopy(store)
        uow = FakeUnitOfWork(store=store)
        with pytest.raises(ValueError):
            with uow:
                uow.system_state.set('colour', 'blue')
                uow.system_state.set('shape', 'square')
                raise ValueError("leave the fake")
        assert uow.store is store
        assert store == expected
        assert uow.rolled_back is True
        assert uow.committed is False

    def test_keyboard_interrupt_restores_store_and_sets_neither(self) -> None:
        store = {'system_state': {'colour': 'red'}}
        expected = copy.deepcopy(store)
        uow = FakeUnitOfWork(store=store)
        with pytest.raises(KeyboardInterrupt):
            with uow:
                uow.system_state.set('colour', 'blue')
                raise KeyboardInterrupt
        assert store == expected
        assert uow.committed is False
        assert uow.rolled_back is False

    def test_shared_store_carries_committed_write(self) -> None:
        store: dict = {}
        with FakeUnitOfWork(store=store) as first:
            first.system_state.set('colour', 'blue')
        with FakeUnitOfWork(store=store) as second:
            assert second.system_state.get('colour') == 'blue'

    def test_repositories_absent_after_exit(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            pass
        for name in FakeUnitOfWork.REPOSITORIES:
            assert not hasattr(uow, name)

    def test_entered_again_while_open_raises_guard_message(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            with pytest.raises(RuntimeError, match=_REENTRY):
                with uow:
                    pass
            uow.system_state.set('colour', 'blue')
        assert uow.committed is True
        assert uow.store == {'system_state': {'colour': 'blue'}}

    def test_entered_after_exit_raises_guard_message(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            pass
        with pytest.raises(RuntimeError, match=_REENTRY):
            with uow:
                pass


class TestFakeOpenScopeCheck:
    """A non-record fake is refused inside another open fake, and the open state always clears."""

    def test_nested_non_record_raises(self) -> None:
        with FakeUnitOfWork():
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with FakeUnitOfWork():
                    pass

    def test_refused_fake_leaves_store_and_enters_after_outer_exits(self) -> None:
        store = {'system_state': {'colour': 'red'}}
        inner = FakeUnitOfWork(store=store)
        with FakeUnitOfWork(store=store):
            before = copy.deepcopy(store)
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with inner:
                    pass
            assert store == before
        with inner:
            inner.system_state.set('colour', 'blue')
        assert inner.committed is True

    def test_non_record_inside_record_raises(self) -> None:
        with FakeUnitOfWork(record=True):
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with FakeUnitOfWork():
                    pass

    def test_record_inside_open_non_record_enters_and_restores_flag(self) -> None:
        with FakeUnitOfWork():
            with FakeUnitOfWork(record=True) as record:
                record.system_state.set('recorded', 'yes')
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with FakeUnitOfWork():
                    pass

    @pytest.mark.parametrize('record', [False, True])
    def test_clear_after_normal_exit(self, record: bool) -> None:
        with FakeUnitOfWork(record=record):
            pass
        with FakeUnitOfWork() as uow:
            pass
        assert uow.committed is True

    @pytest.mark.parametrize('record', [False, True])
    def test_clear_after_exception(self, record: bool) -> None:
        with pytest.raises(ValueError):
            with FakeUnitOfWork(record=record):
                raise ValueError("leave the fake")
        with FakeUnitOfWork() as uow:
            pass
        assert uow.committed is True

    @pytest.mark.parametrize('record', [False, True])
    def test_clear_after_keyboard_interrupt(self, record: bool) -> None:
        with pytest.raises(KeyboardInterrupt):
            with FakeUnitOfWork(record=record):
                raise KeyboardInterrupt
        with FakeUnitOfWork() as uow:
            pass
        assert uow.committed is True


class TestFakeParity:
    """A fake has nothing the real unit of work or repository lacks."""

    def test_repository_names_are_real(self) -> None:
        assert set(FakeUnitOfWork.REPOSITORIES) <= set(UnitOfWork.REPOSITORIES)

    def test_fake_methods_exist_on_real_with_equal_signatures(self) -> None:
        for name, fake_class in FakeUnitOfWork.REPOSITORIES.items():
            real_class = UnitOfWork.REPOSITORIES[name]
            for method_name, method in inspect.getmembers(fake_class, inspect.isfunction):
                if method_name.startswith('_'):
                    continue
                real_method = getattr(real_class, method_name)
                assert inspect.signature(method, eval_str=True) == inspect.signature(
                    real_method, eval_str=True
                ), method_name


@pytest.mark.parametrize('kind', ['real', 'fake'])
class TestSystemStateContract:
    """Each FakeSystemStateRepository method answers as SystemStateRepository does."""

    @staticmethod
    def _repository(kind: str, db_session: Session) -> SystemStateRepository:
        if kind == 'real':
            return SystemStateRepository(db_session)
        return FakeSystemStateRepository({})

    def test_get_absent_key(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        assert repo.get('absent') is None

    def test_set_then_get(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('colour', 'blue')
        assert repo.get('colour') == 'blue'

    def test_set_overwrites(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('colour', 'blue')
        repo.set('colour', 'green')
        assert repo.get('colour') == 'green'

    def test_delete_present_key(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('colour', 'blue')
        assert repo.delete('colour') is True
        assert repo.get('colour') is None

    def test_delete_absent_key(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        assert repo.delete('absent') is False

    def test_get_bool_of_padded_true(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('flag', 'True ')
        assert repo.get_bool('flag') is True

    def test_get_bool_of_other_value(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('flag', 'yes')
        assert repo.get_bool('flag', default=True) is False

    def test_get_bool_of_absent_key_with_default(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        assert repo.get_bool('absent', default=True) is True

    def test_set_bool(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set_bool('on', True)
        repo.set_bool('off', False)
        assert (repo.get('on'), repo.get('off')) == ('true', 'false')

    def test_get_int(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('count', '42')
        assert repo.get_int('count') == 42

    def test_get_int_of_unparseable_value(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('count', 'many')
        assert repo.get_int('count', default=3) == 3

    def test_get_int_of_absent_key_with_default(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        assert repo.get_int('absent', default=5) == 5

    def test_set_int(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set_int('count', 7)
        assert repo.get('count') == '7'


@pytest.mark.parametrize('kind', ['real', 'fake'])
class TestClientContract:
    """Each FakeClientRepository method answers as ClientRepository does."""

    @staticmethod
    def _repository(kind: str, db_session: Session, store: dict) -> ClientRepository:
        if kind == 'real':
            return ClientRepository(db_session)
        return FakeClientRepository(store)

    def test_create_writes_an_inactive_client(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        client = repo.create('ZqvNew')
        assert client.name == 'ZqvNew'
        assert client.is_active is False
        assert client.created_at.utcoffset() is not None
        assert abs(datetime.now(timezone.utc) - client.created_at) < timedelta(minutes=1)
        assert repo.get_by_id(client.id).name == 'ZqvNew'

    def test_create_refuses_the_reserved_name(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        with pytest.raises(ValueError) as e:
            repo.create(' Internal ')
        assert str(e.value) == (
            "'internal' is a reserved keyword and cannot be used as a client name."
        )

    def test_create_refuses_a_duplicate_in_other_case(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        repo.create('ZqvDup')
        with pytest.raises(ValueError) as e:
            repo.create('zqvDUP')
        assert str(e.value) == "A client named 'zqvDUP' already exists."

    def test_get_by_id_of_unknown_id_is_none(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        assert repo.get_by_id(99999999) is None

    def test_get_by_name_ignores_case_and_padding(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        client = repo.create('ZqvName')
        assert repo.get_by_name('  zqvNAME ').id == client.id

    def test_get_by_name_of_unknown_name_is_none(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        assert repo.get_by_name('ZqvNobody') is None

    def test_find_by_name_fuzzy_matches_substrings_in_name_order(
        self, kind: str, db_session: Session
    ) -> None:
        repo = self._repository(kind, db_session, {})
        repo.create('ZqvMatchb')
        repo.create('ZqvMatchC')
        repo.create('ZqvOther')
        found = repo.find_by_name_fuzzy(' zqvMATCH ')
        assert [c.name for c in found] == ['ZqvMatchC', 'ZqvMatchb']

    def test_list_all_returns_every_client_in_name_order(
        self, kind: str, db_session: Session
    ) -> None:
        repo = self._repository(kind, db_session, {})
        for name in ('Zqvb', 'ZqvC', 'ZqvA'):
            repo.create(name)
        names = [c.name for c in repo.list_all() if c.name.startswith('Zqv')]
        assert names == ['ZqvA', 'ZqvC', 'Zqvb']

    def test_delete_of_unknown_id_is_false(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        assert repo.delete(99999999) is False

    def test_delete_removes_the_client_and_unlinks_its_rows(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        repo = self._repository(kind, db_session, store)
        client = repo.create('ZqvGone')
        other = repo.create('ZqvKept')
        day = date(2099, 1, 1)
        stamp = datetime(2099, 1, 1, 9, 0)
        if kind == 'real':
            meeting = MeetingsRepository(db_session).create(
                title='ZqvMeeting', start_time=stamp, client_id=client.id,
            )
            note = NotesRepository(db_session).create(
                content='ZqvNote', tags=['internal-only'], created_at=stamp, client_id=client.id,
            )
            other_note = NotesRepository(db_session).create(
                content='ZqvNote', tags=['internal-only'], created_at=stamp, client_id=other.id,
            )
            project = Project(name='ZqvProject', client_id=client.id)
            recipient = ReportRecipient(
                report_type='ZqvReport', recipient_type='to', client_id=client.id,
            )
            db_session.add_all([project, recipient])
            db_session.flush()
            report = ReportsRepository(db_session).create(
                report_type='ZqvReport', report_date=day, content='ZqvReport',
                ai_provider='claude', generation_time=1.0, client_id=client.id,
            )
            entry = TimeEntriesRepository(db_session).create(
                note_id=note.id, duration_hours=1.0, entry_date=day,
                entry_time=time(9, 0), client_id=client.id,
            )
            linked = {
                Meeting: meeting.id, Note: note.id, Project: project.id,
                ReportRecipient: recipient.id, Report: report.id, TimeEntry: entry.id,
            }
            other_ids = {Note: other_note.id}
        else:
            store['meetings'] = {1: {'id': 1, 'title': 'ZqvMeeting', 'client_id': client.id}}
            store['notes'] = {
                1: {
                    'id': 1, 'content': 'ZqvNote', 'tags': ['internal-only'],
                    'created_at': stamp, 'meeting_id': None, 'client_id': client.id,
                },
                2: {
                    'id': 2, 'content': 'ZqvNote', 'tags': ['internal-only'],
                    'created_at': stamp, 'meeting_id': None, 'client_id': other.id,
                },
            }
            for table in ('projects', 'report_recipients', 'reports', 'time_entries'):
                store[table] = {1: {'id': 1, 'client_id': client.id}}
            linked = {
                'meetings': 1, 'notes': 1, 'projects': 1,
                'report_recipients': 1, 'reports': 1, 'time_entries': 1,
            }
            other_ids = {'notes': 2}

        assert repo.delete(client.id) is True

        assert repo.get_by_id(client.id) is None
        if kind == 'real':
            db_session.expunge_all()
            unlinked = [
                db_session.query(model).filter(model.id == row_id).one().client_id
                for model, row_id in linked.items()
            ]
            kept = [
                db_session.query(model).filter(model.id == row_id).one().client_id
                for model, row_id in other_ids.items()
            ]
        else:
            unlinked = [store[table][row_id]['client_id'] for table, row_id in linked.items()]
            kept = [store[table][row_id]['client_id'] for table, row_id in other_ids.items()]
        assert unlinked == [None] * 6
        assert kept == [other.id]

    def test_count_linked_records_counts_by_table_in_order(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        repo = self._repository(kind, db_session, store)
        client = repo.create('ZqvCount')
        other = repo.create('ZqvOther')
        day = date(2099, 1, 1)
        stamp = datetime(2099, 1, 1, 9, 0)
        if kind == 'real':
            notes = NotesRepository(db_session)
            MeetingsRepository(db_session).create(
                title='ZqvMeeting', start_time=stamp, client_id=client.id,
            )
            note = notes.create(
                content='ZqvNote', tags=['internal-only'], created_at=stamp, client_id=client.id,
            )
            notes.create(
                content='ZqvNote', tags=['internal-only'], created_at=stamp, client_id=client.id,
            )
            notes.create(
                content='ZqvNote', tags=['internal-only'], created_at=stamp, client_id=other.id,
            )
            db_session.add(
                ReportRecipient(report_type='ZqvReport', recipient_type='to', client_id=client.id)
            )
            db_session.flush()
            ReportsRepository(db_session).create(
                report_type='ZqvReport', report_date=day, content='ZqvReport',
                ai_provider='claude', generation_time=1.0, client_id=client.id,
            )
            TimeEntriesRepository(db_session).create(
                note_id=note.id, duration_hours=1.0, entry_date=day,
                entry_time=time(9, 0), client_id=client.id,
            )
        else:
            store['meetings'] = {1: {'id': 1, 'title': 'ZqvMeeting', 'client_id': client.id}}
            store['notes'] = {
                row_id: {
                    'id': row_id, 'content': 'ZqvNote', 'tags': ['internal-only'],
                    'created_at': stamp, 'meeting_id': None, 'client_id': owner,
                }
                for row_id, owner in ((1, client.id), (2, client.id), (3, other.id))
            }
            store['report_recipients'] = {1: {'id': 1, 'client_id': client.id}}
            store['reports'] = {1: {'id': 1, 'client_id': client.id}}
            store['time_entries'] = {1: {'id': 1, 'client_id': client.id}}

        counts = repo.count_linked_records(client.id)

        assert list(counts.items()) == [
            ('meetings', 1), ('notes', 2), ('projects', 0),
            ('report_recipients', 1), ('reports', 1), ('time_entries', 1),
        ]

    def test_set_active_flags_one_client(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        first = repo.create('ZqvFirst')
        second = repo.create('ZqvSecond')
        repo.set_active(first.id)

        active = repo.set_active(second.id)

        assert (active.id, active.is_active) == (second.id, True)
        assert repo.get_by_id(first.id).is_active is False
        assert repo.get_active().id == second.id

    @pytest.mark.parametrize('target', ['another client', 'the flagged client'])
    def test_set_active_moves_the_flag_without_raising(
        self, kind: str, db_session: Session, target: str
    ) -> None:
        repo = self._repository(kind, db_session, {})
        flagged = repo.create('ZqvFlagged')
        other = repo.create('ZqvOther')
        repo.set_active(flagged.id)
        chosen = other if target == 'another client' else flagged

        repo.set_active(chosen.id)

        assert repo.get_active().id == chosen.id
        assert [repo.get_by_id(c.id).is_active for c in (flagged, other)] == [
            c.id == chosen.id for c in (flagged, other)
        ]

    def test_set_active_of_unknown_id_raises(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        with pytest.raises(ValueError) as e:
            repo.set_active(99999999)
        assert str(e.value) == "No client with ID 99999999."

    def test_clear_active_unflags_the_client(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        client = repo.create('ZqvActive')
        repo.set_active(client.id)

        repo.clear_active()

        assert repo.get_by_id(client.id).is_active is False
        assert repo.get_active() is None

    def test_get_active_returns_the_flagged_client(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        repo.create('ZqvFirst')
        second = repo.create('ZqvSecond')
        repo.set_active(second.id)
        assert repo.get_active().id == second.id

    def test_get_active_with_nothing_active_is_none(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session, {})
        repo.create('ZqvIdle')
        repo.clear_active()
        assert repo.get_active() is None


class TestFakeClientRefusesTwoFlaggedClients:
    """
    FakeClientRepository refuses a store holding two flagged clients, as uq_clients_one_active does.

    The database cannot hold such a store, so the real side is
    tests/test_client_repository.py, which flushes a second flagged client.
    """

    @pytest.mark.parametrize('call', ['get_active', 'clear_active', 'set_active'])
    def test_the_active_client_methods_raise(self, call: str) -> None:
        created = datetime(2099, 1, 1, 9, 0, tzinfo=timezone.utc)
        repo = FakeClientRepository({'clients': {
            1: {'id': 1, 'name': 'ZqvOne', 'is_active': True, 'created_at': created},
            2: {'id': 2, 'name': 'ZqvTwo', 'is_active': True, 'created_at': created},
        }})
        args = (1,) if call == 'set_active' else ()

        with pytest.raises(IntegrityError):
            getattr(repo, call)(*args)


@pytest.mark.parametrize('kind', ['real', 'fake'])
class TestNotesContract:
    """FakeNotesRepository.get_by_id answers as NotesRepository.get_by_id does."""

    @staticmethod
    def _repository(kind: str, db_session: Session, store: dict) -> NotesRepository:
        if kind == 'real':
            return NotesRepository(db_session)
        return FakeNotesRepository(store)

    def test_get_by_id_returns_the_note_with_its_meeting(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        stamp = datetime(2099, 1, 2, 23, 30)
        if kind == 'real':
            meeting_id = MeetingsRepository(db_session).create(
                title='ZqvMeeting', start_time=stamp,
            ).id
            note_id = NotesRepository(db_session).create(
                content='ZqvNote', tags=['carry-forward', 'internal-only'],
                meeting_id=meeting_id, created_at=stamp,
            ).id
            db_session.expunge_all()
        else:
            meeting_id, note_id = 7, 3
            store['meetings'] = {7: {'id': 7, 'title': 'ZqvMeeting', 'client_id': None}}
            store['notes'] = {3: {
                'id': 3, 'content': 'ZqvNote', 'tags': ['carry-forward', 'internal-only'],
                'created_at': stamp, 'meeting_id': 7, 'client_id': None,
            }}

        note = self._repository(kind, db_session, store).get_by_id(note_id)

        assert (note.id, note.content, note.tags) == (
            note_id, 'ZqvNote', ['carry-forward', 'internal-only'],
        )
        assert (note.created_at, note.created_date) == (stamp, date(2099, 1, 2))
        assert (note.meeting_id, note.client_id) == (meeting_id, None)
        assert (note.meeting.id, note.meeting.title) == (meeting_id, 'ZqvMeeting')

    def test_get_by_id_of_a_note_without_a_meeting(self, kind: str, db_session: Session) -> None:
        store: dict = {}
        stamp = datetime(2099, 1, 2, 9, 0)
        if kind == 'real':
            note_id = NotesRepository(db_session).create(
                content='ZqvNote', tags=['internal-only'], created_at=stamp,
            ).id
            db_session.expunge_all()
        else:
            note_id = 3
            store['notes'] = {3: {
                'id': 3, 'content': 'ZqvNote', 'tags': ['internal-only'],
                'created_at': stamp, 'meeting_id': None, 'client_id': None,
            }}

        note = self._repository(kind, db_session, store).get_by_id(note_id)

        assert (note.meeting_id, note.meeting) == (None, None)

    def test_get_by_id_of_unknown_id_is_none(self, kind: str, db_session: Session) -> None:
        assert self._repository(kind, db_session, {}).get_by_id(99999999) is None

    def test_create_writes_the_note_with_its_tags_deduplicated_and_sorted(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        stamp = datetime(2099, 1, 2, 23, 30)
        meeting_id = _seed_meeting(kind, db_session, store, 'ZqvMeeting', stamp)
        repo = self._repository(kind, db_session, store)

        note = repo.create(
            content='ZqvNote', tags=['internal-only', 'carry-forward', 'internal-only'],
            meeting_id=meeting_id, source='meeting', created_at=stamp,
        )

        assert (note.content, note.tags, note.source) == (
            'ZqvNote', ['carry-forward', 'internal-only'], 'meeting',
        )
        assert (note.created_at, note.created_date) == (stamp, date(2099, 1, 2))
        assert (note.meeting_id, note.project_id, note.client_id) == (meeting_id, None, None)
        assert note.meeting.title == 'ZqvMeeting'
        assert repo.get_by_id(note.id).tags == ['carry-forward', 'internal-only']

    def test_create_without_a_time_or_tags_stamps_now_with_no_tags(
        self, kind: str, db_session: Session
    ) -> None:
        note = self._repository(kind, db_session, {}).create(content='ZqvNote', tags=[])

        assert (note.tags, note.source, note.meeting) == ([], 'ad-hoc', None)
        assert note.created_at.tzinfo is None
        assert abs(datetime.now() - note.created_at) < timedelta(minutes=1)

    def test_create_with_its_clients_project_links_it(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        owner_id, _, project_id = _seed_projects(kind, db_session, store)

        note = self._repository(kind, db_session, store).create(
            content='ZqvNote', tags=['internal-only'], project_id=project_id, client_id=owner_id,
        )

        assert (note.project_id, note.client_id) == (project_id, owner_id)

    def test_create_with_another_clients_project_raises(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        owner_id, other_id, project_id = _seed_projects(kind, db_session, store)

        with pytest.raises(ValueError) as e:
            self._repository(kind, db_session, store).create(
                content='ZqvNote', tags=['internal-only'], project_id=project_id,
                client_id=other_id,
            )

        assert str(e.value) == (
            f"Project {project_id} belongs to client {owner_id}, not client {other_id}. "
            "Cannot link note to mismatched project."
        )

    def test_create_with_an_unknown_project_raises(self, kind: str, db_session: Session) -> None:
        store: dict = {}
        owner_id, _, _ = _seed_projects(kind, db_session, store)

        with pytest.raises(ValueError) as e:
            self._repository(kind, db_session, store).create(
                content='ZqvNote', tags=['internal-only'], project_id=99999999,
                client_id=owner_id,
            )

        assert str(e.value) == "Project 99999999 does not exist"


@pytest.mark.parametrize('kind', ['real', 'fake'])
class TestTaskStatusContract:
    """Each FakeTaskStatusRepository method answers as TaskStatusRepository does."""

    @staticmethod
    def _repository(kind: str, db_session: Session, store: dict) -> TaskStatusRepository:
        if kind == 'real':
            return TaskStatusRepository(db_session)
        return FakeTaskStatusRepository(store)

    def test_get_by_note_id_returns_the_task_with_its_note(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        stamp = datetime(2099, 1, 2, 9, 0)
        if kind == 'real':
            meeting_id = MeetingsRepository(db_session).create(
                title='ZqvMeeting', start_time=stamp,
            ).id
            note_id = NotesRepository(db_session).create(
                content='ZqvTask', tags=['carry-forward'], meeting_id=meeting_id, created_at=stamp,
            ).id
            TaskStatusRepository(db_session).create_active(note_id)
            db_session.expunge_all()
        else:
            meeting_id, note_id = 7, 3
            store['meetings'] = {7: {'id': 7, 'title': 'ZqvMeeting', 'client_id': None}}
            store['notes'] = {3: {
                'id': 3, 'content': 'ZqvTask', 'tags': ['carry-forward'],
                'created_at': stamp, 'meeting_id': 7, 'client_id': None,
            }}
            store['task_status'] = {1: {
                'id': 1, 'note_id': 3, 'status': 'active', 'completed_at': None,
                'forwarding_note_id': None, 'created_at': datetime.now(),
                'updated_at': datetime.now(),
            }}

        task = self._repository(kind, db_session, store).get_by_note_id(note_id)

        assert (task.note_id, task.status, task.completed_at, task.forwarding_note_id) == (
            note_id, 'active', None, None,
        )
        assert task.created_at.tzinfo is None
        assert (task.note.content, task.note.created_date) == ('ZqvTask', date(2099, 1, 2))
        assert (task.note.meeting.id, task.note.meeting.title) == (meeting_id, 'ZqvMeeting')

    def test_get_by_note_id_of_a_note_without_a_task_is_none(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        if kind == 'real':
            note_id = NotesRepository(db_session).create(
                content='ZqvNote', tags=['internal-only'], created_at=datetime(2099, 1, 2, 9, 0),
            ).id
        else:
            note_id = 3
            store['notes'] = {3: {
                'id': 3, 'content': 'ZqvNote', 'tags': ['internal-only'],
                'created_at': datetime(2099, 1, 2, 9, 0), 'meeting_id': None, 'client_id': None,
            }}

        assert self._repository(kind, db_session, store).get_by_note_id(note_id) is None

    @pytest.mark.parametrize('status, expected', [
        ('active', ['ZqvActive']),
        ('completed', ['ZqvCompleted']),
        ('dismissed', ['ZqvDismissed']),
        ('all', ['ZqvDismissed', 'ZqvCompleted', 'ZqvActive']),
        (None, ['ZqvDismissed', 'ZqvCompleted', 'ZqvActive']),
    ])
    def test_get_filtered_filters_by_status(
        self, kind: str, db_session: Session, status: str, expected: list
    ) -> None:
        store: dict = {}
        seeds = [('ZqvActive', 'active', 1), ('ZqvCompleted', 'completed', 2),
                 ('ZqvDismissed', 'dismissed', 3)]
        if kind == 'real':
            repo = TaskStatusRepository(db_session)
            for content, task_status, hour in seeds:
                note_id = NotesRepository(db_session).create(
                    content=content, tags=['carry-forward'],
                    created_at=datetime(2099, 1, 2, hour, 0),
                ).id
                repo.create_active(note_id)
                if task_status == 'completed':
                    repo.set_completed(note_id)
                elif task_status == 'dismissed':
                    repo.set_dismissed(note_id)
        else:
            store['notes'] = {
                row_id: {
                    'id': row_id, 'content': content, 'tags': ['carry-forward'],
                    'created_at': datetime(2099, 1, 2, row_id, 0), 'meeting_id': None,
                    'client_id': None,
                }
                for content, _, row_id in seeds
            }
            store['task_status'] = {
                row_id: {
                    'id': row_id, 'note_id': row_id, 'status': task_status,
                    'completed_at': None, 'forwarding_note_id': None,
                    'created_at': datetime.now(), 'updated_at': datetime.now(),
                }
                for _, task_status, row_id in seeds
            }

        tasks = self._repository(kind, db_session, store).get_filtered(status=status, search='zqv')

        assert [task.note.content for task in tasks] == expected

    @pytest.mark.parametrize('status, expected', [
        ('active', 1), ('completed', 1), ('dismissed', 1), ('all', 3), (None, 3),
    ])
    def test_count_filtered_filters_by_status(
        self, kind: str, db_session: Session, status: str, expected: int
    ) -> None:
        store: dict = {}
        seeds = [('ZqvActive', 'active', 1), ('ZqvCompleted', 'completed', 2),
                 ('ZqvDismissed', 'dismissed', 3)]
        if kind == 'real':
            repo = TaskStatusRepository(db_session)
            for content, task_status, hour in seeds:
                note_id = NotesRepository(db_session).create(
                    content=content, tags=['carry-forward'],
                    created_at=datetime(2099, 1, 2, hour, 0),
                ).id
                repo.create_active(note_id)
                if task_status == 'completed':
                    repo.set_completed(note_id)
                elif task_status == 'dismissed':
                    repo.set_dismissed(note_id)
        else:
            store['notes'] = {
                row_id: {
                    'id': row_id, 'content': content, 'tags': ['carry-forward'],
                    'created_at': datetime(2099, 1, 2, row_id, 0), 'meeting_id': None,
                    'client_id': None,
                }
                for content, _, row_id in seeds
            }
            store['task_status'] = {
                row_id: {
                    'id': row_id, 'note_id': row_id, 'status': task_status,
                    'completed_at': None, 'forwarding_note_id': None,
                    'created_at': datetime.now(), 'updated_at': datetime.now(),
                }
                for _, task_status, row_id in seeds
            }

        count = self._repository(kind, db_session, store).count_filtered(
            status=status, search='zqv',
        )

        assert count == expected

    def test_search_and_date_filter_narrow_both_queries(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        seeds = [
            (1, 'Zqv Alpha task', datetime(2099, 1, 3, 9, 0)),
            (2, 'ZQV beta task', datetime(2099, 1, 3, 10, 0)),
            (3, 'zqv gamma task', datetime(2099, 1, 4, 9, 0)),
            (4, 'Unrelated task', datetime(2099, 1, 3, 11, 0)),
        ]
        if kind == 'real':
            repo = TaskStatusRepository(db_session)
            for _, content, stamp in seeds:
                note_id = NotesRepository(db_session).create(
                    content=content, tags=['carry-forward'], created_at=stamp,
                ).id
                repo.create_active(note_id)
        else:
            store['notes'] = {
                row_id: {
                    'id': row_id, 'content': content, 'tags': ['carry-forward'],
                    'created_at': stamp, 'meeting_id': None, 'client_id': None,
                }
                for row_id, content, stamp in seeds
            }
            store['task_status'] = {
                row_id: {
                    'id': row_id, 'note_id': row_id, 'status': 'active',
                    'completed_at': None, 'forwarding_note_id': None,
                    'created_at': datetime.now(), 'updated_at': datetime.now(),
                }
                for row_id, _, _ in seeds
            }
        repo = self._repository(kind, db_session, store)

        tasks = repo.get_filtered(search='zQv', date_filter=date(2099, 1, 3))
        count = repo.count_filtered(search='zQv', date_filter=date(2099, 1, 3))

        assert [task.note.content for task in tasks] == ['ZQV beta task', 'Zqv Alpha task']
        assert count == 2

    @pytest.mark.parametrize('limit, expected', [
        (2, ['ZqvThird', 'ZqvSecond']),
        (0, ['ZqvThird', 'ZqvSecond', 'ZqvFirst']),
    ])
    def test_get_filtered_orders_newest_first_and_applies_the_limit(
        self, kind: str, db_session: Session, limit: int, expected: list
    ) -> None:
        store: dict = {}
        seeds = [(1, 'ZqvSecond', datetime(2099, 1, 2, 9, 0)),
                 (2, 'ZqvFirst', datetime(2099, 1, 1, 9, 0)),
                 (3, 'ZqvThird', datetime(2099, 1, 3, 9, 0))]
        if kind == 'real':
            repo = TaskStatusRepository(db_session)
            for _, content, stamp in seeds:
                note_id = NotesRepository(db_session).create(
                    content=content, tags=['carry-forward'], created_at=stamp,
                ).id
                repo.create_active(note_id)
        else:
            store['notes'] = {
                row_id: {
                    'id': row_id, 'content': content, 'tags': ['carry-forward'],
                    'created_at': stamp, 'meeting_id': None, 'client_id': None,
                }
                for row_id, content, stamp in seeds
            }
            store['task_status'] = {
                row_id: {
                    'id': row_id, 'note_id': row_id, 'status': 'active',
                    'completed_at': None, 'forwarding_note_id': None,
                    'created_at': datetime.now(), 'updated_at': datetime.now(),
                }
                for row_id, _, _ in seeds
            }

        tasks = self._repository(kind, db_session, store).get_filtered(search='zqv', limit=limit)

        assert [task.note.content for task in tasks] == expected

    def test_a_task_whose_note_is_gone_is_neither_listed_nor_counted(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        if kind == 'real':
            notes = NotesRepository(db_session)
            repo = TaskStatusRepository(db_session)
            kept_id = notes.create(
                content='ZqvKept', tags=['carry-forward'], created_at=datetime(2099, 1, 2, 9, 0),
            ).id
            gone_id = notes.create(
                content='ZqvGone', tags=['carry-forward'], created_at=datetime(2099, 1, 2, 10, 0),
            ).id
            repo.create_active(kept_id)
            repo.create_active(gone_id)
            notes.delete(gone_id)
        else:
            store['notes'] = {1: {
                'id': 1, 'content': 'ZqvKept', 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 2, 9, 0), 'meeting_id': None, 'client_id': None,
            }}
            store['task_status'] = {
                row_id: {
                    'id': row_id, 'note_id': row_id, 'status': 'active',
                    'completed_at': None, 'forwarding_note_id': None,
                    'created_at': datetime.now(), 'updated_at': datetime.now(),
                }
                for row_id in (1, 2)
            }
        repo = self._repository(kind, db_session, store)

        tasks = repo.get_filtered(search='zqv')

        assert [task.note.content for task in tasks] == ['ZqvKept']
        assert repo.count_filtered(search='zqv') == 1

    @pytest.mark.parametrize('method, status', [
        ('set_completed', 'completed'),
        ('set_dismissed', 'dismissed'),
    ])
    def test_status_change_sets_status_and_times(
        self, kind: str, db_session: Session, method: str, status: str
    ) -> None:
        store: dict = {}
        if kind == 'real':
            note_id = NotesRepository(db_session).create(
                content='ZqvTask', tags=['carry-forward'], created_at=datetime(2099, 1, 2, 9, 0),
            ).id
            TaskStatusRepository(db_session).create_active(note_id)
        else:
            note_id = 3
            store['notes'] = {3: {
                'id': 3, 'content': 'ZqvTask', 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 2, 9, 0), 'meeting_id': None, 'client_id': None,
            }}
            store['task_status'] = {1: {
                'id': 1, 'note_id': 3, 'status': 'active', 'completed_at': None,
                'forwarding_note_id': None, 'created_at': datetime(2099, 1, 2, 9, 0),
                'updated_at': datetime(2099, 1, 2, 9, 0),
            }}
        repo = self._repository(kind, db_session, store)

        task = getattr(repo, method)(note_id)

        assert (task.note_id, task.status) == (note_id, status)
        assert task.completed_at == task.updated_at
        assert task.completed_at.tzinfo is None
        assert abs(datetime.now() - task.completed_at) < timedelta(minutes=1)
        assert repo.get_by_note_id(note_id).status == status

    @pytest.mark.parametrize('method', ['set_completed', 'set_dismissed'])
    def test_status_change_of_a_note_without_a_task_raises(
        self, kind: str, db_session: Session, method: str
    ) -> None:
        repo = self._repository(kind, db_session, {})
        with pytest.raises(ValueError) as e:
            getattr(repo, method)(99999999)
        assert str(e.value) == "No task_status record exists for note 99999999."

    def test_ensure_active_creates_an_active_task_for_a_note_without_one(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        note_id = _seed_note(kind, db_session, store, 'ZqvTask')
        repo = self._repository(kind, db_session, store)

        task = repo.ensure_active(note_id)

        assert (task.note_id, task.status, task.completed_at, task.forwarding_note_id) == (
            note_id, 'active', None, None,
        )
        assert repo.get_by_note_id(note_id).id == task.id

    def test_ensure_active_of_an_active_task_keeps_the_one_task(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        note_id = _seed_note(kind, db_session, store, 'ZqvTask')
        repo = self._repository(kind, db_session, store)

        first = repo.ensure_active(note_id)
        second = repo.ensure_active(note_id)

        assert (second.id, second.status) == (first.id, 'active')
        assert repo.count_filtered(status='all', search='zqvtask') == 1

    def test_ensure_active_reactivates_a_completed_task(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        note_id = _seed_note(kind, db_session, store, 'ZqvTask')
        repo = self._repository(kind, db_session, store)
        completed = repo.ensure_active(note_id)
        repo.set_completed(note_id)

        task = repo.ensure_active(note_id)

        assert (task.id, task.status, task.completed_at) == (completed.id, 'active', None)
        assert repo.get_by_note_id(note_id).status == 'active'


@pytest.mark.parametrize('kind', ['real', 'fake'])
class TestTimeEntriesContract:
    """Each FakeTimeEntriesRepository method answers as TimeEntriesRepository does."""

    @staticmethod
    def _repository(kind: str, db_session: Session, store: dict) -> TimeEntriesRepository:
        if kind == 'real':
            return TimeEntriesRepository(db_session)
        return FakeTimeEntriesRepository(store)

    def test_create_writes_the_entry_with_its_note(self, kind: str, db_session: Session) -> None:
        store: dict = {}
        start = datetime(2099, 1, 2, 9, 30)
        meeting_id = _seed_meeting(kind, db_session, store, 'ZqvMeeting', start)
        note_id = _seed_note(kind, db_session, store, 'ZqvEntryNote', meeting_id)
        synced = datetime(2099, 1, 2, 12, 0)

        entry = self._repository(kind, db_session, store).create(
            note_id=note_id, duration_hours=1.5, entry_date=date(2099, 1, 2),
            entry_time=time(9, 30), category='meeting', meeting_id=meeting_id,
            clockify_id='zqv-clockify-1', synced_at=synced,
        )

        assert (entry.note_id, entry.duration_hours, entry.entry_date, entry.display_time) == (
            note_id, Decimal('1.5'), date(2099, 1, 2), '09:30',
        )
        assert isinstance(entry.duration_hours, Decimal)
        assert (entry.category, entry.meeting_id, entry.project_id, entry.client_id) == (
            'meeting', meeting_id, None, None,
        )
        assert (entry.clockify_id, entry.synced_at) == ('zqv-clockify-1', synced)
        assert abs(datetime.now() - entry.created_at) < timedelta(minutes=1)
        assert entry.note.content == 'ZqvEntryNote'

    def test_create_with_another_clients_project_raises(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        owner_id, other_id, project_id = _seed_projects(kind, db_session, store)
        note_id = _seed_note(kind, db_session, store, 'ZqvEntryNote')

        with pytest.raises(ValueError) as e:
            self._repository(kind, db_session, store).create(
                note_id=note_id, duration_hours=1.0, entry_date=date(2099, 1, 2),
                entry_time=time(9, 0), project_id=project_id, client_id=other_id,
            )

        assert str(e.value) == (
            f"Project {project_id} belongs to client {owner_id}, not client {other_id}. "
            "Cannot link time entry to mismatched project."
        )

    def test_get_by_meeting_orders_by_date_then_time_with_notes(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        start = datetime(2099, 1, 1, 8, 0)
        meeting_id = _seed_meeting(kind, db_session, store, 'ZqvMeeting', start)
        other_id = _seed_meeting(kind, db_session, store, 'ZqvOtherMeeting', start)
        repo = self._repository(kind, db_session, store)
        seeds = [
            ('ZqvSecondDay', date(2099, 1, 2), time(9, 0), meeting_id),
            ('ZqvLate', date(2099, 1, 1), time(14, 0), meeting_id),
            ('ZqvOther', date(2099, 1, 1), time(7, 0), other_id),
            ('ZqvEarly', date(2099, 1, 1), time(8, 0), meeting_id),
        ]
        for content, entry_date, entry_time, owner in seeds:
            note_id = _seed_note(kind, db_session, store, content, owner)
            repo.create(
                note_id=note_id, duration_hours=1.0, entry_date=entry_date,
                entry_time=entry_time, meeting_id=owner,
            )

        entries = repo.get_by_meeting(meeting_id)

        assert [entry.note.content for entry in entries] == [
            'ZqvEarly', 'ZqvLate', 'ZqvSecondDay',
        ]

    def test_get_by_meeting_of_a_meeting_without_entries_is_empty(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        meeting_id = _seed_meeting(kind, db_session, store, 'ZqvMeeting', datetime(2099, 1, 1))

        assert self._repository(kind, db_session, store).get_by_meeting(meeting_id) == []

    def test_update_repoints_the_note_and_keeps_the_rest(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        first_id = _seed_note(kind, db_session, store, 'ZqvFirst')
        second_id = _seed_note(kind, db_session, store, 'ZqvSecond')
        repo = self._repository(kind, db_session, store)
        created = repo.create(
            note_id=first_id, duration_hours=2.0, entry_date=date(2099, 1, 2),
            entry_time=time(10, 0), category='review',
        )

        entry = repo.update(created.id, note_id=second_id)

        assert (entry.id, entry.note_id, entry.note.content) == (created.id, second_id, 'ZqvSecond')
        assert (entry.duration_hours, entry.entry_time, entry.category) == (
            Decimal('2'), time(10, 0), 'review',
        )

    def test_update_of_unknown_id_is_none(self, kind: str, db_session: Session) -> None:
        assert self._repository(kind, db_session, {}).update(99999999, category='x') is None

    def test_update_to_another_clients_project_raises(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        owner_id, other_id, project_id = _seed_projects(kind, db_session, store)
        note_id = _seed_note(kind, db_session, store, 'ZqvEntryNote')
        repo = self._repository(kind, db_session, store)
        created = repo.create(
            note_id=note_id, duration_hours=1.0, entry_date=date(2099, 1, 2),
            entry_time=time(9, 0), client_id=other_id,
        )

        with pytest.raises(ValueError) as e:
            repo.update(created.id, project_id=project_id)

        assert str(e.value) == (
            f"Project {project_id} belongs to client {owner_id}, not client {other_id}. "
            "Cannot link time entry to mismatched project."
        )


@pytest.mark.parametrize('kind', ['real', 'fake'])
class TestMeetingsContract:
    """Each FakeMeetingsRepository method answers as MeetingsRepository does."""

    @staticmethod
    def _repository(kind: str, db_session: Session, store: dict) -> MeetingsRepository:
        if kind == 'real':
            return MeetingsRepository(db_session)
        return FakeMeetingsRepository(store)

    def test_get_by_id_returns_the_meeting_with_its_times(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        start = datetime(2099, 1, 2, 9, 0)
        meeting_id = _seed_meeting(kind, db_session, store, 'ZqvMeeting', start)

        meeting = self._repository(kind, db_session, store).get_by_id(meeting_id)

        assert (meeting.id, meeting.title, meeting.client_id) == (meeting_id, 'ZqvMeeting', None)
        assert (meeting.start_time, meeting.end_time) == (start, datetime(2099, 1, 2, 10, 0))
        assert (meeting.condensed_summary, meeting.condensed_at) == (None, None)

    def test_get_by_id_of_unknown_id_is_none(self, kind: str, db_session: Session) -> None:
        assert self._repository(kind, db_session, {}).get_by_id(99999999) is None

    def test_set_condensed_summary_sets_both_columns_and_returns_the_meeting(
        self, kind: str, db_session: Session
    ) -> None:
        store: dict = {}
        meeting_id = _seed_meeting(kind, db_session, store, 'ZqvMeeting', datetime(2099, 1, 2))
        repo = self._repository(kind, db_session, store)
        condensed_at = datetime(2099, 1, 2, 17, 0)

        meeting = repo.set_condensed_summary(meeting_id, 'ZqvSummary', condensed_at)

        assert (meeting.id, meeting.condensed_summary, meeting.condensed_at) == (
            meeting_id, 'ZqvSummary', condensed_at,
        )
        again = repo.get_by_id(meeting_id)
        assert (again.condensed_summary, again.condensed_at) == ('ZqvSummary', condensed_at)

    def test_set_condensed_summary_of_unknown_id_is_none(
        self, kind: str, db_session: Session
    ) -> None:
        repo = self._repository(kind, db_session, {})
        assert repo.set_condensed_summary(99999999, 'ZqvSummary', datetime(2099, 1, 2)) is None

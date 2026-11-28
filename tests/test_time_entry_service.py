"""
Tests for workmain/services/time_entry_service.py, on fake_uow.

The operations (create_time_entry, create_paired_time_entry,
link_condensed_note) run inside an entered fake; the use cases
(log_meeting_time, log_task_time) enter the fake themselves. Rows are seeded
into the fake's store in the shapes tests/mocks/fake_unit_of_work.py states.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest

from tests.mocks.fake_unit_of_work import FakeUnitOfWork
from workmain.services import time_entry_service
from workmain.services.exceptions import (
    InvalidTagsError,
    MissingStartTimeError,
    ServiceValidationError,
)

_SENTINEL = date(2099, 1, 1)
_DEFAULT_TIME = time(10, 0)


def _seed_active_client(store: dict, client_id: int) -> None:
    """Seed a flagged clients row, which makes that client the active one."""
    store.setdefault('clients', {})[client_id] = {
        'id': client_id,
        'name': f'Sentinel Client {client_id}',
        'is_active': True,
        'created_at': datetime(2099, 1, 1, 9, 0, tzinfo=timezone.utc),
    }


def _seed_meeting(store: dict, start: datetime, minutes: int = 30, title: str = 'Sentinel') -> int:
    rows = store.setdefault('meetings', {})
    meeting_id = max(rows, default=0) + 1
    rows[meeting_id] = {
        'id': meeting_id, 'title': title, 'client_id': None, 'start_time': start,
        'end_time': start + timedelta(minutes=minutes), 'condensed_summary': None,
        'condensed_at': None,
    }
    return meeting_id


def _seed_note(
    store: dict, content: str, meeting_id: int | None = None, client_id: int | None = None,
    source: str = 'meeting',
) -> int:
    rows = store.setdefault('notes', {})
    note_id = max(rows, default=0) + 1
    rows[note_id] = {
        'id': note_id, 'content': content, 'tags': ['internal-only'], 'source': source,
        'created_at': datetime(2099, 1, 1, 9, 0), 'meeting_id': meeting_id,
        'project_id': None, 'client_id': client_id,
    }
    return note_id


def _seed_entry(
    store: dict, note_id: int, meeting_id: int, entry_date: date, entry_time: time
) -> int:
    rows = store.setdefault('time_entries', {})
    entry_id = max(rows, default=0) + 1
    rows[entry_id] = {
        'id': entry_id, 'note_id': note_id, 'duration_hours': Decimal('0.5'),
        'entry_date': entry_date, 'entry_time': entry_time, 'category': 'meeting',
        'project_id': None, 'meeting_id': meeting_id, 'client_id': None,
        'clockify_id': None, 'synced_at': None, 'created_at': datetime(2099, 1, 1, 9, 0),
    }
    return entry_id


class TestCreateTimeEntry:
    """create_time_entry writes a task's note and its entry on an entered unit of work."""

    def test_writes_the_entry_and_its_task_note(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            entry = time_entry_service.create_time_entry(
                fake_uow, description="Service layer test", duration_hours=1.0,
                entry_time=_DEFAULT_TIME,
            )
        row = fake_uow.store['time_entries'][entry.id]
        note = fake_uow.store['notes'][row['note_id']]
        assert (row['duration_hours'], row['entry_time']) == (Decimal('1.0'), _DEFAULT_TIME)
        assert (note['content'], note['source'], note['meeting_id']) == (
            "Service layer test", "task", None,
        )

    def test_a_missing_start_time_raises_and_writes_nothing(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        with fake_uow:
            with pytest.raises(MissingStartTimeError):
                time_entry_service.create_time_entry(
                    fake_uow, description="No time", duration_hours=1.0, entry_time=None,
                )
        assert fake_uow.store.get('notes', {}) == {}
        assert fake_uow.store.get('time_entries', {}) == {}

    def test_entry_date_defaults_to_today_and_the_note_is_not_backdated(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        with fake_uow:
            entry = time_entry_service.create_time_entry(
                fake_uow, description="Today entry", duration_hours=1.0,
                entry_time=_DEFAULT_TIME,
            )
        assert entry.entry_date == date.today()
        assert fake_uow.store['notes'][entry.note_id]['created_at'].date() == date.today()

    def test_a_backdated_entry_backdates_its_note(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            entry = time_entry_service.create_time_entry(
                fake_uow, description="Backdated entry", duration_hours=1.0,
                entry_time=_DEFAULT_TIME, entry_date=_SENTINEL,
            )
        assert entry.entry_date == _SENTINEL
        assert fake_uow.store['notes'][entry.note_id]['created_at'].date() == _SENTINEL

    @pytest.mark.parametrize('tags', [None, []])
    def test_no_tags_default_to_internal_only(
        self, fake_uow: FakeUnitOfWork, tags: list | None
    ) -> None:
        with fake_uow:
            entry = time_entry_service.create_time_entry(
                fake_uow, description="Default tag", duration_hours=1.0,
                entry_time=_DEFAULT_TIME, tags=tags,
            )
        assert fake_uow.store['notes'][entry.note_id]['tags'] == ["internal-only"]

    def test_an_invalid_tag_raises_and_writes_nothing(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            with pytest.raises(InvalidTagsError) as exc_info:
                time_entry_service.create_time_entry(
                    fake_uow, description="Bad tag", duration_hours=1.0,
                    entry_time=_DEFAULT_TIME, tags=["not-a-tag"],
                )
        assert exc_info.value.invalid_tags == ["not-a-tag"]
        assert fake_uow.store.get('notes', {}) == {}

    def test_the_active_client_is_stamped_on_entry_and_note(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        _seed_active_client(fake_uow.store, 7)
        with fake_uow:
            entry = time_entry_service.create_time_entry(
                fake_uow, description="Attributed entry", duration_hours=1.0,
                entry_time=_DEFAULT_TIME,
            )
        assert entry.client_id == 7
        assert fake_uow.store['notes'][entry.note_id]['client_id'] == 7

    def test_no_active_client_leaves_both_unset(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            entry = time_entry_service.create_time_entry(
                fake_uow, description="Internal entry", duration_hours=1.0,
                entry_time=_DEFAULT_TIME,
            )
        assert entry.client_id is None
        assert fake_uow.store['notes'][entry.note_id]['client_id'] is None

    def test_category_meeting_and_project_go_on_the_entry_alone(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        meeting_id = _seed_meeting(fake_uow.store, datetime(2099, 1, 1, 9, 0))
        with fake_uow:
            entry = time_entry_service.create_time_entry(
                fake_uow, description="Meeting time", duration_hours=1.0,
                entry_time=_DEFAULT_TIME, category="meeting", meeting_id=meeting_id,
                project_id=None,
            )
        assert (entry.category, entry.meeting_id, entry.project_id) == (
            "meeting", meeting_id, None,
        )
        assert fake_uow.store['notes'][entry.note_id]['meeting_id'] is None

    def test_a_carry_forward_entry_makes_its_note_a_task(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            entry = time_entry_service.create_time_entry(
                fake_uow, description="Follow up on vendor contract", duration_hours=0.5,
                entry_time=_DEFAULT_TIME, tags=["carry-forward"],
            )
        tasks = list(fake_uow.store['task_status'].values())
        assert [(t['note_id'], t['status']) for t in tasks] == [(entry.note_id, 'active')]

    def test_no_task_without_carry_forward(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            time_entry_service.create_time_entry(
                fake_uow, description="No CF tag here", duration_hours=0.5,
                entry_time=_DEFAULT_TIME,
            )
        assert fake_uow.store.get('task_status', {}) == {}


class TestCreatePairedTimeEntry:
    """create_paired_time_entry takes the entry's meeting and client from its note."""

    def test_meeting_and_client_come_from_the_note(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store, datetime(2099, 1, 1, 9, 0))
        _seed_note(fake_uow.store, "Sentinel paired", meeting_id=meeting_id, client_id=3)
        _seed_active_client(fake_uow.store, 9)
        with fake_uow:
            note = fake_uow.notes.get_by_id(1)
            entry = time_entry_service.create_paired_time_entry(
                fake_uow, note, duration_hours=1.0, entry_date=_SENTINEL,
                entry_time=_DEFAULT_TIME,
            )
        assert (entry.note_id, entry.meeting_id, entry.client_id) == (1, meeting_id, 3)

    def test_a_clockify_id_stamps_synced_at(self, fake_uow: FakeUnitOfWork) -> None:
        _seed_note(fake_uow.store, "Sentinel clockify")
        with fake_uow:
            entry = time_entry_service.create_paired_time_entry(
                fake_uow, fake_uow.notes.get_by_id(1), duration_hours=1.0,
                entry_date=_SENTINEL, entry_time=_DEFAULT_TIME,
                clockify_id="clockify-sentinel-123",
            )
        assert entry.clockify_id == "clockify-sentinel-123"
        assert abs(datetime.now() - entry.synced_at) < timedelta(minutes=1)

    def test_no_clockify_id_leaves_synced_at_unset(self, fake_uow: FakeUnitOfWork) -> None:
        _seed_note(fake_uow.store, "Sentinel no clockify")
        with fake_uow:
            entry = time_entry_service.create_paired_time_entry(
                fake_uow, fake_uow.notes.get_by_id(1), duration_hours=1.0,
                entry_date=_SENTINEL, entry_time=_DEFAULT_TIME, category='meeting',
            )
        assert (entry.clockify_id, entry.synced_at, entry.category) == (None, None, 'meeting')


class TestLinkCondensedNote:
    """link_condensed_note repoints the meeting's entry on its date, or creates one."""

    def test_creates_an_entry_when_the_meeting_has_none(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store, datetime(2099, 2, 1, 9, 0))
        condensed_id = _seed_note(fake_uow.store, "Summary", meeting_id, source='condensed')
        with fake_uow:
            entry, created = time_entry_service.link_condensed_note(
                fake_uow, meeting_id, fake_uow.notes.get_by_id(condensed_id),
            )
        assert created is True
        assert (entry.note_id, entry.meeting_id, entry.category) == (
            condensed_id, meeting_id, 'meeting',
        )
        assert (entry.entry_date, entry.entry_time, entry.duration_hours) == (
            date(2099, 2, 1), time(9, 0), Decimal('0.5'),
        )

    def test_repoints_the_existing_entry(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store, datetime(2099, 2, 2, 9, 0))
        detail_id = _seed_note(fake_uow.store, "Detail", meeting_id)
        existing_id = _seed_entry(fake_uow.store, detail_id, meeting_id, date(2099, 2, 2), time(9, 0))
        condensed_id = _seed_note(fake_uow.store, "Summary", meeting_id, source='condensed')
        with fake_uow:
            entry, created = time_entry_service.link_condensed_note(
                fake_uow, meeting_id, fake_uow.notes.get_by_id(condensed_id),
            )
        assert (created, entry.id, entry.note_id) == (False, existing_id, condensed_id)
        assert len(fake_uow.store['time_entries']) == 1

    def test_repoints_only_the_earliest_entry_of_that_meeting(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        store = fake_uow.store
        day = date(2099, 2, 3)
        meeting_a = _seed_meeting(store, datetime(2099, 2, 3, 9, 0))
        meeting_b = _seed_meeting(store, datetime(2099, 2, 3, 11, 0))
        late_note = _seed_note(store, "A late", meeting_a)
        late = _seed_entry(store, late_note, meeting_a, day, time(9, 15))
        early = _seed_entry(store, _seed_note(store, "A early", meeting_a), meeting_a, day, time(9, 0))
        other_note = _seed_note(store, "B", meeting_b)
        other = _seed_entry(store, other_note, meeting_b, day, time(11, 0))
        condensed_id = _seed_note(store, "Summary", meeting_a, source='condensed')
        with fake_uow:
            time_entry_service.link_condensed_note(
                fake_uow, meeting_a, fake_uow.notes.get_by_id(condensed_id),
            )
        entries = store['time_entries']
        assert entries[early]['note_id'] == condensed_id
        assert entries[late]['note_id'] == late_note
        assert entries[other]['note_id'] == other_note

    def test_ignores_the_meeting_entries_on_other_dates(self, fake_uow: FakeUnitOfWork) -> None:
        store = fake_uow.store
        meeting_id = _seed_meeting(store, datetime(2099, 2, 4, 9, 0))
        prior_note = _seed_note(store, "Prior day", meeting_id)
        prior = _seed_entry(store, prior_note, meeting_id, date(2099, 2, 3), time(9, 0))
        condensed_id = _seed_note(store, "Summary", meeting_id, source='condensed')
        with fake_uow:
            entry, created = time_entry_service.link_condensed_note(
                fake_uow, meeting_id, fake_uow.notes.get_by_id(condensed_id),
            )
        assert (created, entry.entry_date) == (True, date(2099, 2, 4))
        assert entry.id != prior
        assert store['time_entries'][prior]['note_id'] == prior_note

    def test_an_unknown_meeting_raises_naming_the_id(self, fake_uow: FakeUnitOfWork) -> None:
        condensed_id = _seed_note(fake_uow.store, "Summary", source='condensed')
        with fake_uow:
            with pytest.raises(ServiceValidationError, match="99999"):
                time_entry_service.link_condensed_note(
                    fake_uow, 99999, fake_uow.notes.get_by_id(condensed_id),
                )

    def test_another_clients_project_on_the_existing_entry_raises(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        store = fake_uow.store
        meeting_id = _seed_meeting(store, datetime(2099, 2, 5, 9, 0))
        existing = _seed_entry(
            store, _seed_note(store, "Detail", meeting_id), meeting_id, date(2099, 2, 5), time(9, 0),
        )
        store['time_entries'][existing].update(client_id=2, project_id=5)
        store['projects'] = {5: {'id': 5, 'client_id': 1}}
        condensed_id = _seed_note(store, "Summary", meeting_id, source='condensed')
        with fake_uow:
            with pytest.raises(ValueError, match="Cannot link time entry to mismatched project"):
                time_entry_service.link_condensed_note(
                    fake_uow, meeting_id, fake_uow.notes.get_by_id(condensed_id),
                )


class TestLogMeetingTime:
    """log_meeting_time writes a meeting's note and its paired entry in one unit of work."""

    def test_writes_the_meeting_note_and_its_entry(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store, datetime(2099, 1, 1, 9, 0))
        _seed_active_client(fake_uow.store, 4)
        backdated = datetime(2099, 1, 1, 12, 0)

        result = time_entry_service.log_meeting_time(
            fake_uow, meeting_id, content="Sentinel standup", tags=["client-report"],
            duration_hours=0.5, entry_date=_SENTINEL, entry_time=time(9, 0),
            created_at=backdated,
        )

        assert fake_uow.committed is True
        assert result == time_entry_service.CreatedEntry(
            entry_id=result.entry_id, note_id=result.note_id, content="Sentinel standup",
            duration_hours=Decimal('0.5'), display_time="09:00",
        )
        note = fake_uow.store['notes'][result.note_id]
        entry = fake_uow.store['time_entries'][result.entry_id]
        assert (note['source'], note['meeting_id'], note['tags'], note['created_at']) == (
            'meeting', meeting_id, ["client-report"], backdated,
        )
        assert (entry['note_id'], entry['meeting_id'], entry['client_id'], entry['category']) == (
            result.note_id, meeting_id, 4, 'meeting',
        )

    def test_category_and_project_go_on_the_entry(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store, datetime(2099, 1, 1, 9, 0))
        _seed_active_client(fake_uow.store, 1)
        fake_uow.store['projects'] = {5: {'id': 5, 'client_id': 1}}

        result = time_entry_service.log_meeting_time(
            fake_uow, meeting_id, content="Sentinel", tags=None, duration_hours=1.0,
            entry_date=_SENTINEL, entry_time=_DEFAULT_TIME, category='review', project_id=5,
        )

        entry = fake_uow.store['time_entries'][result.entry_id]
        assert (entry['category'], entry['project_id']) == ('review', 5)
        assert fake_uow.store['notes'][result.note_id]['project_id'] is None

    def test_a_failed_entry_rolls_back_the_note(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store, datetime(2099, 1, 1, 9, 0))
        _seed_active_client(fake_uow.store, 2)
        fake_uow.store['projects'] = {5: {'id': 5, 'client_id': 1}}

        with pytest.raises(ValueError, match="mismatched project"):
            time_entry_service.log_meeting_time(
                fake_uow, meeting_id, content="Sentinel", tags=None, duration_hours=1.0,
                entry_date=_SENTINEL, entry_time=_DEFAULT_TIME, project_id=5,
            )

        assert fake_uow.rolled_back is True
        assert fake_uow.store.get('notes', {}) == {}


class TestLogTaskTime:
    """log_task_time writes a task's note and entry in one unit of work."""

    def test_writes_the_task_and_returns_its_values(self, fake_uow: FakeUnitOfWork) -> None:
        result = time_entry_service.log_task_time(
            fake_uow, description="Sentinel task", duration_hours=1.25,
            entry_time=time(14, 30), entry_date=_SENTINEL, category='development',
        )

        assert fake_uow.committed is True
        assert result == time_entry_service.CreatedEntry(
            entry_id=result.entry_id, note_id=result.note_id, content="Sentinel task",
            duration_hours=Decimal('1.25'), display_time="14:30",
        )
        note = fake_uow.store['notes'][result.note_id]
        assert (note['source'], note['meeting_id']) == ('task', None)
        assert fake_uow.store['time_entries'][result.entry_id]['category'] == 'development'

    def test_a_missing_start_time_raises_and_rolls_back(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(MissingStartTimeError):
            time_entry_service.log_task_time(
                fake_uow, description="No time", duration_hours=1.0,
            )

        assert fake_uow.rolled_back is True
        assert fake_uow.store.get('notes', {}) == {}

    def test_a_failed_entry_rolls_back_the_note_and_its_task(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        _seed_active_client(fake_uow.store, 2)
        fake_uow.store['projects'] = {5: {'id': 5, 'client_id': 1}}

        with pytest.raises(ValueError, match="mismatched project"):
            time_entry_service.log_task_time(
                fake_uow, description="Sentinel", duration_hours=1.0,
                entry_time=_DEFAULT_TIME, tags=["carry-forward"], project_id=5,
            )

        assert fake_uow.store.get('notes', {}) == {}
        assert fake_uow.store.get('task_status', {}) == {}

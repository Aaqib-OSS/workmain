"""
Tests for workmain/services/notes_service.py.

create_note, apply_cf_hook_on_create and add_note are tested on fake_uow.
update_note still takes a session, so its tests seed and run on db_session.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from tests.mocks.fake_unit_of_work import FakeUnitOfWork
from workmain.database.models import Note
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services import clients_service, notes_service
from workmain.services.exceptions import InvalidTagsError


def _note_row(uow: FakeUnitOfWork, note_id: int) -> dict:
    return uow.store['notes'][note_id]


class TestCreateNote:
    """create_note writes one note on an entered unit of work."""

    def test_writes_the_note_with_its_tags(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            note = notes_service.create_note(
                fake_uow, content="Service layer test note", tags=["internal-only"],
            )
        row = _note_row(fake_uow, note.id)
        assert (row['content'], row['tags']) == ("Service layer test note", ["internal-only"])

    @pytest.mark.parametrize('tags', [None, []])
    def test_no_tags_default_to_internal_only(
        self, fake_uow: FakeUnitOfWork, tags: list | None
    ) -> None:
        with fake_uow:
            note = notes_service.create_note(fake_uow, content="No tags", tags=tags)
        assert _note_row(fake_uow, note.id)['tags'] == ["internal-only"]

    def test_valid_full_name_tags_are_kept(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            note = notes_service.create_note(
                fake_uow, content="CF note", tags=["carry-forward", "internal-only"],
            )
        assert _note_row(fake_uow, note.id)['tags'] == ["carry-forward", "internal-only"]

    def test_an_invalid_tag_raises_naming_it_and_the_vocabulary(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        with fake_uow:
            with pytest.raises(InvalidTagsError) as exc_info:
                notes_service.create_note(
                    fake_uow, content="Mixed", tags=["internal-only", "made-up-tag"],
                )
        assert exc_info.value.invalid_tags == ["made-up-tag"]
        assert "internal-only" in exc_info.value.valid_tags
        assert fake_uow.store.get('notes', {}) == {}

    def test_the_active_client_is_stamped(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            7: {
                'id': 7, 'name': 'Sentinel Client', 'is_active': True,
                'created_at': datetime(2099, 1, 1, 9, 0, tzinfo=timezone.utc),
            },
        }
        with fake_uow:
            note = notes_service.create_note(fake_uow, content="Attributed note")
        assert _note_row(fake_uow, note.id)['client_id'] == 7

    def test_no_active_client_leaves_the_client_unset(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            note = notes_service.create_note(fake_uow, content="Internal note")
        assert _note_row(fake_uow, note.id)['client_id'] is None

    def test_after_the_active_client_is_deleted_no_client_is_stamped(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        fake_uow.store['clients'] = {
            7: {
                'id': 7, 'name': 'Sentinel Client', 'is_active': True,
                'created_at': datetime(2099, 1, 1, 9, 0, tzinfo=timezone.utc),
            },
        }
        clients_service.delete_client(fake_uow, 7)

        uow = FakeUnitOfWork(store=fake_uow.store)
        with uow:
            note = notes_service.create_note(uow, content="After the delete")
        assert _note_row(uow, note.id)['client_id'] is None

    def test_source_defaults_to_ad_hoc(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            note = notes_service.create_note(fake_uow, content="Ad-hoc note")
        assert _note_row(fake_uow, note.id)['source'] == "ad-hoc"

    def test_source_meeting_and_project_are_written_as_given(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        fake_uow.store['meetings'] = {4: {'id': 4, 'title': 'Sentinel', 'client_id': None}}
        with fake_uow:
            note = notes_service.create_note(
                fake_uow, content="Task note", source="task", meeting_id=4, project_id=None,
            )
        row = _note_row(fake_uow, note.id)
        assert (row['source'], row['meeting_id'], row['project_id']) == ("task", 4, None)

    def test_created_at_backdates_the_note(self, fake_uow: FakeUnitOfWork) -> None:
        backdated = datetime(2026, 7, 1, 9, 0)
        with fake_uow:
            note = notes_service.create_note(
                fake_uow, content="Sentinel backdated note 2099", created_at=backdated,
            )
        assert _note_row(fake_uow, note.id)['created_at'] == backdated


class TestApplyCfHookOnCreate:
    """The carry-forward hook makes a note a task when, and only when, it is tagged carry-forward."""

    def test_a_carry_forward_note_gets_an_active_task(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            note = notes_service.create_note(
                fake_uow, content="Sentinel CF hook note 2099", tags=["carry-forward"],
            )
        tasks = list(fake_uow.store['task_status'].values())
        assert [(t['note_id'], t['status']) for t in tasks] == [(note.id, 'active')]

    def test_a_note_without_carry_forward_gets_no_task(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            notes_service.create_note(
                fake_uow, content="Sentinel non-CF note 2099", tags=["internal-only"],
            )
        assert fake_uow.store.get('task_status', {}) == {}

    def test_the_hook_alone_on_a_carry_forward_note(self, fake_uow: FakeUnitOfWork) -> None:
        with fake_uow:
            note = fake_uow.notes.create(content="Sentinel", tags=["carry-forward"])
            notes_service.apply_cf_hook_on_create(fake_uow, note)
        assert [t['note_id'] for t in fake_uow.store['task_status'].values()] == [note.id]


class TestAddNote:
    """add_note enters its unit of work, writes one note, and returns plain values."""

    def test_writes_the_note_and_returns_its_values(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['meetings'] = {4: {'id': 4, 'title': 'Sentinel', 'client_id': None}}

        result = notes_service.add_note(
            fake_uow, content="Sentinel add", tags=["internal-only"], source="meeting",
            meeting_id=4,
        )

        assert fake_uow.committed is True
        assert result == notes_service.CreatedNote(
            id=result.id, content="Sentinel add", display_tags="[internal-only]",
        )
        row = _note_row(fake_uow, result.id)
        assert (row['content'], row['source'], row['meeting_id']) == ("Sentinel add", "meeting", 4)

    def test_a_carry_forward_note_commits_with_its_task(self, fake_uow: FakeUnitOfWork) -> None:
        result = notes_service.add_note(fake_uow, content="Sentinel CF", tags=["carry-forward"])

        assert [t['note_id'] for t in fake_uow.store['task_status'].values()] == [result.id]

    def test_an_invalid_tag_writes_nothing_and_rolls_back(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        with pytest.raises(InvalidTagsError):
            notes_service.add_note(fake_uow, content="Bad", tags=["bogus"])

        assert fake_uow.rolled_back is True
        assert fake_uow.store.get('notes', {}) == {}


def _seed_note(db_session: Session, content: str, tags: list[str]) -> Note:
    note = NotesRepository(db_session).create(content=content, tags=tags)
    if 'carry-forward' in tags:
        TaskStatusRepository(db_session).ensure_active(note.id)
    return note


class TestUpdateNote:
    """update_note makes one repository call and applies the CF-transition hook only when tags change."""

    def test_update_note_transitions_cf_add(self, db_session: Session) -> None:
        note = _seed_note(db_session, "Sentinel CF-add note 2099", ["internal-only"])
        notes_service.update_note(
            db_session,
            note.id,
            tags=["internal-only", "carry-forward"],
        )
        ts = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts is not None
        assert ts.status == "active"

    def test_update_note_transitions_cf_remove(self, db_session: Session) -> None:
        note = _seed_note(db_session, "Sentinel CF-remove note 2099", ["carry-forward"])
        notes_service.update_note(
            db_session,
            note.id,
            tags=["internal-only"],
        )
        ts = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts is not None
        assert ts.status == "dismissed"

    def test_update_note_no_transition_when_cf_unchanged(self, db_session: Session) -> None:
        note = _seed_note(db_session, "Sentinel CF-unchanged note 2099", ["carry-forward"])
        ts_before = TaskStatusRepository(db_session).get_by_note_id(note.id)
        updated_at_before = ts_before.updated_at

        notes_service.update_note(
            db_session,
            note.id,
            tags=["carry-forward"],
        )

        ts_after = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts_after.status == "active"
        assert ts_after.updated_at == updated_at_before

    def test_update_note_content_only_does_not_touch_tags_or_hook(
        self, db_session: Session
    ) -> None:
        note = _seed_note(db_session, "Sentinel content-only note 2099", ["internal-only"])
        updated = notes_service.update_note(
            db_session,
            note.id,
            content="Sentinel content-only note 2099 (edited)",
            tags=None,
        )
        assert updated.content == "Sentinel content-only note 2099 (edited)"
        assert updated.tags == ["internal-only"]
        ts = TaskStatusRepository(db_session).get_by_note_id(note.id)
        assert ts is None

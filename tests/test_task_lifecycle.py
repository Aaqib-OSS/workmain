"""
Tests for the task_status repository, eager creation hooks and the tasks group.

Covers TaskStatusRepository's create_active, ensure_active, set_completed,
set_dismissed, set_dismissed_by_tag_removal, get_by_note_id, get_filtered and
count_filtered, including that get_filtered loads each row's note with it,
and the tasks group's help, removed names and root wiring. Each tasks
command's paths are tested end to end in tests/test_tasks_commands.py.

Uses db_session fixture from conftest.py for full transaction isolation.
Tests use fixed dates in 2099 (2099-xx-xx).
"""

from datetime import date, datetime
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner
from sqlalchemy import event
from sqlalchemy.orm import Session

from workmain.cli.commands.tasks import task_list, tasks
from workmain.cli.interface import cli
from workmain.cli.output import Renderer
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services import tasks_service
from workmain.services.results import Page

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_cf_note(db_session, content: str = "Sentinel CF task 2099",
                  created_at: datetime = None):
    repo = NotesRepository(db_session)
    return repo.create(
        content=content,
        tags=['carry-forward'],
        source='task',
        created_at=created_at or datetime(2099, 1, 1, 9, 0),
    )


def _make_note(db_session, content: str, tags=None, created_at: datetime = None):
    repo = NotesRepository(db_session)
    return repo.create(
        content=content,
        tags=tags or ['internal-only'],
        source='task',
        created_at=created_at or datetime(2099, 1, 1, 9, 0),
    )


# ---------------------------------------------------------------------------
# Repository — create_active
# ---------------------------------------------------------------------------

class TestCreateActive:
    """create_active() basic behaviour."""

    def test_creates_record_with_active_status(self, db_session):
        """create_active() returns a TaskStatus with status='active'."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        ts = repo.create_active(note.id)
        assert ts.id is not None
        assert ts.note_id == note.id
        assert ts.status == 'active'
        assert ts.completed_at is None

    def test_raises_on_duplicate(self, db_session):
        """create_active() raises ValueError if record already exists for note."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        with pytest.raises(ValueError, match="already exists"):
            repo.create_active(note.id)


# ---------------------------------------------------------------------------
# Repository — ensure_active
# ---------------------------------------------------------------------------

class TestEnsureActive:
    """ensure_active() idempotent creation and re-activation."""

    def test_creates_if_none_exists(self, db_session):
        """ensure_active() creates an active record when none exists."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        ts = repo.ensure_active(note.id)
        assert ts.status == 'active'
        assert ts.note_id == note.id

    def test_reactivates_completed_record(self, db_session):
        """ensure_active() re-opens a completed task_status record."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        repo.set_completed(note.id)
        ts = repo.ensure_active(note.id)
        assert ts.status == 'active'
        assert ts.completed_at is None

    def test_reactivates_dismissed_record(self, db_session):
        """ensure_active() re-opens a dismissed task_status record."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        repo.set_dismissed(note.id)
        ts = repo.ensure_active(note.id)
        assert ts.status == 'active'

    def test_returns_unchanged_active_record(self, db_session):
        """ensure_active() returns the same record when already active."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        ts1 = repo.ensure_active(note.id)
        ts2 = repo.ensure_active(note.id)
        assert ts1.id == ts2.id
        assert ts2.status == 'active'


# ---------------------------------------------------------------------------
# Repository — set_completed / set_dismissed
# ---------------------------------------------------------------------------

class TestStatusTransitions:
    """set_completed() and set_dismissed() transition tests."""

    def test_set_completed_sets_status_and_timestamp(self, db_session):
        """set_completed() sets status='completed' and populates completed_at."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        ts = repo.set_completed(note.id)
        assert ts.status == 'completed'
        assert ts.completed_at is not None

    def test_set_completed_raises_if_no_record(self, db_session):
        """set_completed() raises ValueError when no task_status record exists."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        with pytest.raises(ValueError):
            repo.set_completed(note.id)

    def test_set_dismissed_sets_status_and_timestamp(self, db_session):
        """set_dismissed() sets status='dismissed' and populates completed_at."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        ts = repo.set_dismissed(note.id)
        assert ts.status == 'dismissed'
        assert ts.completed_at is not None

    def test_set_dismissed_by_tag_removal_dismisses_existing(self, db_session):
        """set_dismissed_by_tag_removal() dismisses an existing active record."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        ts = repo.set_dismissed_by_tag_removal(note.id)
        assert ts is not None
        assert ts.status == 'dismissed'

    def test_set_dismissed_by_tag_removal_returns_none_when_no_record(self, db_session):
        """set_dismissed_by_tag_removal() returns None silently when no record exists."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        result = repo.set_dismissed_by_tag_removal(note.id)
        assert result is None


# ---------------------------------------------------------------------------
# Repository — get_by_note_id / get_filtered
# ---------------------------------------------------------------------------

class TestQueries:
    """Query methods on TaskStatusRepository."""

    def test_get_by_note_id_returns_record(self, db_session):
        """get_by_note_id() returns the correct task_status record."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note.id)
        ts = repo.get_by_note_id(note.id)
        assert ts is not None
        assert ts.note_id == note.id

    def test_get_by_note_id_returns_none_when_missing(self, db_session):
        """get_by_note_id() returns None when no record exists."""
        note = _make_cf_note(db_session)
        repo = TaskStatusRepository(db_session)
        assert repo.get_by_note_id(note.id) is None

    def test_get_filtered_active_only(self, db_session):
        """get_filtered(status='active') returns only active records."""
        note_a = _make_cf_note(db_session, "Sentinel active 2099-A")
        note_b = _make_cf_note(db_session, "Sentinel completed 2099-B",
                               created_at=datetime(2099, 1, 2, 9, 0))
        repo = TaskStatusRepository(db_session)
        repo.create_active(note_a.id)
        repo.create_active(note_b.id)
        repo.set_completed(note_b.id)

        results = repo.get_filtered(status='active')
        ids = [ts.note_id for ts in results]
        assert note_a.id in ids
        assert note_b.id not in ids

    def test_get_filtered_all_statuses(self, db_session):
        """get_filtered(status='all') returns records of every status."""
        note_a = _make_cf_note(db_session, "Sentinel all-A 2099",
                               created_at=datetime(2099, 2, 1, 9, 0))
        note_b = _make_cf_note(db_session, "Sentinel all-B 2099",
                               created_at=datetime(2099, 2, 2, 9, 0))
        repo = TaskStatusRepository(db_session)
        repo.create_active(note_a.id)
        repo.create_active(note_b.id)
        repo.set_dismissed(note_b.id)

        results = repo.get_filtered(status='all')
        ids = [ts.note_id for ts in results]
        assert note_a.id in ids
        assert note_b.id in ids

    def test_get_filtered_search(self, db_session):
        """get_filtered(search=...) matches note content."""
        note_match = _make_cf_note(db_session, "Sentinel xyzzy_unique_token task 2099",
                                   created_at=datetime(2099, 3, 1, 9, 0))
        note_other = _make_cf_note(db_session, "Sentinel other content 2099",
                                   created_at=datetime(2099, 3, 2, 9, 0))
        repo = TaskStatusRepository(db_session)
        repo.create_active(note_match.id)
        repo.create_active(note_other.id)

        results = repo.get_filtered(status='active', search='xyzzy_unique_token')
        ids = [ts.note_id for ts in results]
        assert note_match.id in ids
        assert note_other.id not in ids

    def test_get_filtered_date_filter(self, db_session):
        """get_filtered(date_filter=...) matches by note created_at date."""
        target = datetime(2099, 4, 1, 10, 0)
        other = datetime(2099, 4, 2, 10, 0)
        note_on = _make_cf_note(db_session, "Sentinel date-on 2099",
                                created_at=target)
        note_off = _make_cf_note(db_session, "Sentinel date-off 2099",
                                 created_at=other)
        repo = TaskStatusRepository(db_session)
        repo.create_active(note_on.id)
        repo.create_active(note_off.id)

        results = repo.get_filtered(status='active', date_filter=date(2099, 4, 1))
        ids = [ts.note_id for ts in results]
        assert note_on.id in ids
        assert note_off.id not in ids

    def test_get_filtered_limit(self, db_session):
        """get_filtered(limit=N) caps results at N."""
        repo = TaskStatusRepository(db_session)
        for i in range(5):
            n = _make_cf_note(db_session, f"Sentinel limit test 2099-{i}",
                              created_at=datetime(2099, 5, i + 1, 9, 0))
            repo.create_active(n.id)

        results = repo.get_filtered(status='active', limit=2)
        assert len(results) <= 2

    def test_get_filtered_statement_count_does_not_grow_with_rows(
        self, db_session: Session
    ) -> None:
        """get_filtered() loads each row's note with it: no query per row."""
        def count(day: int, n: int) -> int:
            repo = TaskStatusRepository(db_session)
            for i in range(n):
                note = _make_cf_note(db_session, f"Sentinel load {day}-{i} 2099",
                                     created_at=datetime(2099, 6, day, 9, i))
                repo.create_active(note.id)
            db_session.flush()
            db_session.expunge_all()
            seen = []
            conn = db_session.connection()

            def listener(*args: object) -> None:
                seen.append(1)

            event.listen(conn, "before_cursor_execute", listener)
            try:
                rows = TaskStatusRepository(db_session).get_filtered(
                    status='active', date_filter=date(2099, 6, day), limit=0,
                )
                for ts in rows:
                    (ts.note.id, ts.note.content, ts.note.tags, ts.note.created_date)
            finally:
                event.remove(conn, "before_cursor_execute", listener)
            assert len(rows) == n
            return len(seen)

        assert count(7, 1) == count(8, 5)


class TestTasksGroup:
    def test_list_help_and_status_option(self):
        result = CliRunner(mix_stderr=False).invoke(tasks, ["list", "--help"])
        assert result.exit_code == 0
        assert any("--status" in p.opts for p in task_list.params)

    def test_carryover_no_longer_resolves(self):
        result = CliRunner(mix_stderr=False).invoke(tasks, ["carryover"])
        assert result.exit_code != 0
        assert "no such command" in result.stderr.lower()

    def test_root_group_puts_a_renderer_on_the_context(self):
        seen = []

        def record(self, view, page):
            seen.append(click.get_current_context().find_root().obj)

        with patch.object(
            tasks_service, "list_tasks", autospec=True, return_value=Page((), 0)
        ), patch.object(Renderer, "collection", autospec=True, side_effect=record):
            result = CliRunner(mix_stderr=False).invoke(cli, ["tasks", "list"])
        assert result.exit_code == 0
        assert isinstance(seen[0], Renderer)

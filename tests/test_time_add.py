"""
CLI-level coverage for 'workmain time add'.

Each test runs the command through CliRunner against the test's database and
asserts the exit code and the rows the path writes or leaves alone. Nothing
is patched between the command and the use cases it reaches
(time_entry_service.log_meeting_time and log_task_time,
notes_service.add_note); UnitOfWork refuses to enter inside an open
session_scope(), so a passing test also shows each use case ran with the
command's scope closed.
"""

from datetime import date, datetime
from unittest.mock import patch

import click
from click.testing import CliRunner
from sqlalchemy.orm import Session

from workmain.cli.commands.time import time
from workmain.database.models import Client, Meeting, Note, TimeEntry
from workmain.services import clockify_service
from workmain.services.exceptions import IntegrationError
from workmain.services.results import Page

_SENTINEL_PRIMARY_CONTENT = "Sentinel time add primary content 2099-07-28"
_SENTINEL_EXTRA_CONTENT = "Sentinel extra note content 2099"
_SENTINEL_CLIENT_ID_CONTENT = "Sentinel time add client-id content 2099-07-28"
_SENTINEL_TASK_CONTENT = "Sentinel time add task content 2099-07-28"


def _seed_meeting(session: Session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=datetime(2099, 6, 1, 9, 0),
        end_time=datetime(2099, 6, 1, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


def _one_note(session: Session, content: str) -> Note:
    return session.query(Note).filter(Note.content == content).one()


class TestTimeAdd:
    """time add writes the meeting path, the task path and the extra note through their use cases."""

    def test_the_meeting_path_and_its_extra_note_are_backdated_meeting_notes(
        self, db_session: Session
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Time Add Meeting 2099")

        result = CliRunner().invoke(
            time,
            ["add", _SENTINEL_PRIMARY_CONTENT, "1h", "-T", "14:30", "-d", "2099-06-01",
             "-m", str(meeting.id), "-C", "meeting"],
            # y: add additional notes; the note's content; n: skip Clockify sync
            input="y\n" + _SENTINEL_EXTRA_CONTENT + "\nn\n",
        )

        assert result.exit_code == 0, result.output
        primary = _one_note(db_session, _SENTINEL_PRIMARY_CONTENT)
        extra = _one_note(db_session, _SENTINEL_EXTRA_CONTENT)
        for note in (primary, extra):
            assert (note.source, note.meeting_id, note.created_date) == (
                "meeting", meeting.id, date(2099, 6, 1),
            )
        entry = db_session.query(TimeEntry).filter(TimeEntry.note_id == primary.id).one()
        assert (entry.meeting_id, entry.entry_date, entry.display_time, entry.category) == (
            meeting.id, date(2099, 6, 1), "14:30", "meeting",
        )
        assert db_session.query(TimeEntry).filter(TimeEntry.note_id == extra.id).count() == 0

    def test_the_meeting_path_stamps_the_active_client_on_note_and_entry(
        self, db_session: Session
    ) -> None:
        client = Client(name="Sentinel Time Add ClientID Client 2099", is_active=True)
        db_session.add(client)
        db_session.flush()
        meeting = _seed_meeting(db_session, "Sentinel Time Add ClientID Meeting 2099")

        result = CliRunner().invoke(
            time,
            ["add", _SENTINEL_CLIENT_ID_CONTENT, "1h", "-T", "14:30", "-d", "2099-06-01",
             "-m", str(meeting.id)],
            # n: skip additional notes; n: skip Clockify sync
            input="n\nn\n",
        )

        assert result.exit_code == 0, result.output
        note = _one_note(db_session, _SENTINEL_CLIENT_ID_CONTENT)
        entry = db_session.query(TimeEntry).filter(TimeEntry.note_id == note.id).one()
        assert (note.client_id, entry.client_id) == (client.id, client.id)

    def test_the_task_path_writes_a_task_note_with_its_tags_and_entry(
        self, db_session: Session
    ) -> None:
        result = CliRunner().invoke(
            time,
            ["add", _SENTINEL_TASK_CONTENT, "1.5h", "-T", "0915", "-d", "2099-06-02",
             "-t", "cf", "-C", "development"],
            # n: skip Clockify sync
            input="n\n",
        )

        assert result.exit_code == 0, result.output
        note = _one_note(db_session, _SENTINEL_TASK_CONTENT)
        assert (note.source, note.meeting_id, note.tags, note.created_date) == (
            "task", None, ["carry-forward"], date(2099, 6, 2),
        )
        entry = db_session.query(TimeEntry).filter(TimeEntry.note_id == note.id).one()
        assert (entry.entry_date, entry.display_time, float(entry.duration_hours)) == (
            date(2099, 6, 2), "09:15", 1.5,
        )
        assert entry.category == "development"
        assert note.task_status is not None and note.task_status.status == "active"


def _notes_with(session, content):
    return session.query(Note).filter(Note.content == content).all()


class TestTimeAddUnitOfWork:
    """time add commits its writes before each wait, and a command stopped
    between two writes leaves neither (#96)."""

    def test_t7_time_add_persists_a_note_and_a_time_entry(self, db_session):
        content = "Sentinel time add persists 2099-96"

        result = CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"], input="n\n")

        assert result.exit_code == 0, result.output
        notes = _notes_with(db_session, content)
        assert len(notes) == 1
        entries = db_session.query(TimeEntry).filter(TimeEntry.note_id == notes[0].id).all()
        assert len(entries) == 1

    def test_t2_interrupt_between_the_note_and_the_entry_leaves_neither(self, db_session):
        from workmain.database.repositories.time_entries_repo import (
            TimeEntriesRepository,
        )
        content = "Sentinel time add interrupted 2099-96"

        with patch.object(TimeEntriesRepository, "create", side_effect=KeyboardInterrupt):
            CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"])

        assert _notes_with(db_session, content) == []

    def test_t14_meeting_entry_persists_when_the_extra_notes_prompt_is_cancelled(
        self, db_session
    ):
        meeting = _seed_meeting(db_session, "Sentinel Time Add Abort Meeting 2099-96")
        content = "Sentinel time add meeting abort 2099-96"

        with patch('click.confirm', side_effect=click.Abort()):
            CliRunner().invoke(
                time,
                ["add", content, "1h", "-T", "0900", "-d", "2099-06-01", "-m", str(meeting.id)],
            )

        notes = _notes_with(db_session, content)
        assert len(notes) == 1
        assert db_session.query(TimeEntry).filter(TimeEntry.note_id == notes[0].id).count() == 1

    def test_t1_time_add_pushes_the_new_entry_when_asked(self, db_session):
        content = "Sentinel time add pushes 2099-96"
        pushed = clockify_service.PushedEntry(1, "clockify-id", content)
        result_ = clockify_service.PushResult(
            (), clockify_service.PushTotals(1, 1, 0, 0), Page((pushed,), 1), Page((), 0), (), None,
        )

        with patch.object(clockify_service, "push", autospec=True, return_value=result_) as push:
            result = CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"], input="y\n")

        assert result.exit_code == 0, result.output
        note = _notes_with(db_session, content)[0]
        entry = db_session.query(TimeEntry).filter(TimeEntry.note_id == note.id).one()
        plan = push.call_args.args[0]
        assert [item.entry_id for item in plan.rows] == [entry.id]
        assert "✓ Synced to Clockify" in result.output

    def test_t2_time_add_reports_a_failed_push_and_still_exits_zero(self, db_session):
        content = "Sentinel time add push fails 2099-96"
        failed = clockify_service.FailedEntry(1, content, "boom")
        result_ = clockify_service.PushResult(
            (), clockify_service.PushTotals(1, 0, 1, 0), Page((), 0), Page((failed,), 1), (),
            IntegrationError("1 of 1 entries were not pushed to Clockify"),
        )

        with patch.object(clockify_service, "push", autospec=True, return_value=result_):
            result = CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"], input="y\n")

        assert result.exit_code == 0, result.output
        assert "✗ Sync failed" in result.output
        assert "  Error: boom" in result.output

    def test_t15_entry_persists_when_the_clockify_sync_prompt_is_cancelled(self, db_session):
        content = "Sentinel time add sync abort 2099-96"

        with patch('click.confirm', side_effect=click.Abort()):
            CliRunner().invoke(time, ["add", content, "1h", "-T", "0900"])

        notes = _notes_with(db_session, content)
        assert len(notes) == 1
        assert db_session.query(TimeEntry).filter(TimeEntry.note_id == notes[0].id).count() == 1

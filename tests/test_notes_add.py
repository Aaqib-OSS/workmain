"""
CLI-level coverage for 'workmain notes add'.

Each test runs the command through CliRunner against the test's database,
with nothing patched between the command and the use cases it reaches
(notes_service.add_note, time_entry_service.log_meeting_time), and asserts
the exit code and the rows the path writes. UnitOfWork refuses to enter
inside an open session_scope(), so a passing test also shows each use case
ran with the command's scope closed.
"""

from datetime import datetime
from unittest.mock import patch

import click
from click.testing import CliRunner
from sqlalchemy.orm import Session

from workmain.cli.commands.notes import notes
from workmain.database.models import Meeting, Note, TimeEntry

_SENTINEL_PRIMARY_CONTENT = "Sentinel notes add primary content 2099-07-28"
_SENTINEL_TIME_ENTRY_CONTENT = "Sentinel notes add time entry content 2099-07-28"


def _seed_meeting(session: Session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=datetime(2099, 6, 2, 9, 0),
        end_time=datetime(2099, 6, 2, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


class TestNotesAdd:
    """notes add writes its note, and on a meeting the follow-on time entry, through its use cases."""

    def test_a_note_without_a_meeting_is_written_alone(self, db_session: Session) -> None:
        result = CliRunner().invoke(notes, ["add", _SENTINEL_PRIMARY_CONTENT, "-t", "cf"])

        assert result.exit_code == 0, result.output
        note = db_session.query(Note).filter(Note.content == _SENTINEL_PRIMARY_CONTENT).one()
        assert (note.tags, note.source, note.meeting_id) == (["carry-forward"], "ad-hoc", None)
        assert db_session.query(TimeEntry).filter(TimeEntry.note_id == note.id).count() == 0

    def test_a_meeting_note_and_its_follow_on_entry_with_the_prompted_tag(
        self, db_session: Session
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Notes Add Meeting 2099")

        result = CliRunner().invoke(
            notes,
            ["add", _SENTINEL_PRIMARY_CONTENT, "-m", str(meeting.id)],
            # y: create time entry; description; #cr tag entered at the prompt
            input=f"y\n{_SENTINEL_TIME_ENTRY_CONTENT}\n#cr\n",
        )

        assert result.exit_code == 0, result.output
        primary = db_session.query(Note).filter(Note.content == _SENTINEL_PRIMARY_CONTENT).one()
        assert (primary.meeting_id, primary.tags) == (meeting.id, ["internal-only"])
        te_note = db_session.query(Note).filter(
            Note.content == _SENTINEL_TIME_ENTRY_CONTENT
        ).one()
        assert (te_note.tags, te_note.source, te_note.meeting_id) == (
            ["client-report"], "meeting", meeting.id,
        )
        entry = db_session.query(TimeEntry).filter(TimeEntry.note_id == te_note.id).one()
        assert (entry.meeting_id, entry.category, float(entry.duration_hours)) == (
            meeting.id, "meeting", 0.5,
        )

    def test_declining_the_time_entry_writes_only_the_note(self, db_session: Session) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Notes Add Decline Meeting 2099")

        result = CliRunner().invoke(
            notes, ["add", _SENTINEL_PRIMARY_CONTENT, "-m", str(meeting.id)], input="n\n",
        )

        assert result.exit_code == 0, result.output
        note = db_session.query(Note).filter(Note.content == _SENTINEL_PRIMARY_CONTENT).one()
        assert db_session.query(TimeEntry).filter(TimeEntry.meeting_id == meeting.id).count() == 0
        assert note.meeting_id == meeting.id


def test_t12_note_persists_when_the_time_entry_prompt_is_cancelled(db_session: Session) -> None:
    """The note is committed before "Create time entry for this meeting?", so
    cancelling that prompt keeps it (#96)."""
    meeting = _seed_meeting(db_session, "Sentinel Notes Add Abort Meeting 2099-96")
    content = "Sentinel notes add abort 2099-96"

    with patch('click.confirm', side_effect=click.Abort()):
        CliRunner().invoke(notes, ["add", content, "-m", str(meeting.id)])

    assert db_session.query(Note).filter(Note.content == content).count() == 1

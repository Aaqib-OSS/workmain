"""
CLI-level coverage for 'workmain meetings track'.

Each test runs the command through CliRunner against the test's database,
with nothing patched between the command and
time_entry_service.log_meeting_time, and asserts the exit code and the rows
the path writes. UnitOfWork refuses to enter inside an open session_scope(),
so a passing test also shows the use case ran with the command's scope
closed.
"""

from datetime import datetime

from click.testing import CliRunner
from sqlalchemy.orm import Session

from workmain.cli.commands.meetings import meetings
from workmain.database.models import Client, Meeting, Note, TimeEntry
from workmain.database.repositories.system_state_repository import SystemStateRepository

_SENTINEL_DESCRIPTION = "Sentinel meetings track description 2099-07-28"


def _seed_meeting(session: Session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=datetime(2099, 6, 3, 9, 0),
        end_time=datetime(2099, 6, 3, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


class TestMeetingsTrack:
    """meetings track writes the meeting's note and entry with the prompted tag and the active client."""

    def test_the_note_and_entry_carry_the_tag_and_the_active_client(
        self, db_session: Session
    ) -> None:
        client = Client(name="Sentinel Meetings Track Client 2099", is_active=True)
        db_session.add(client)
        db_session.flush()
        SystemStateRepository(db_session).set_int("active_client_id", client.id)
        meeting = _seed_meeting(db_session, "Sentinel Meetings Track Meeting 2099")

        result = CliRunner().invoke(
            meetings,
            ["track", str(meeting.id)],
            # description; #cr tag entered at the prompt
            input=f"{_SENTINEL_DESCRIPTION}\n#cr\n",
        )

        assert result.exit_code == 0, result.output
        note = db_session.query(Note).filter(Note.content == _SENTINEL_DESCRIPTION).one()
        assert (note.tags, note.source, note.meeting_id, note.client_id) == (
            ["client-report"], "meeting", meeting.id, client.id,
        )
        entry = db_session.query(TimeEntry).filter(TimeEntry.note_id == note.id).one()
        assert (entry.client_id, entry.meeting_id, entry.category) == (
            client.id, meeting.id, "meeting",
        )
        assert (entry.entry_date, float(entry.duration_hours)) == (
            meeting.start_time.date(), 0.5,
        )

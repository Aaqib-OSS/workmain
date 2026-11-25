"""
CLI-level coverage for 'workmain notes log'.

Each test runs the command through CliRunner against the test's database and
asserts the exit code and the rows the path writes or leaves alone. Nothing
is patched between the command and the use cases it reaches
(notes_service.add_note, meetings_service.record_condensation); UnitOfWork
refuses to enter inside an open session_scope(), so a passing test also
shows each use case ran with the command's scope closed. The condenser's
provider reply comes from tests/mocks/stub_providers.py, through
provider_manager._provider_manager_instance.
"""

from contextlib import AbstractContextManager
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner
from sqlalchemy import text
from sqlalchemy.orm import Session

from tests.mocks.stub_providers import complete, stubbed_manager
from workmain.ai import provider_manager as pm_module
from workmain.ai.base_provider import ProviderType
from workmain.cli.commands.notes import notes
from workmain.database.models import AiCost, Client, Meeting, Note, Project, TimeEntry
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

_SENTINEL_CONDENSED_SUMMARY = "Sentinel notes log condensed summary 2099-07-28"
_MEETING_START = datetime(2099, 6, 1, 9, 0)


def _seed_meeting(session: Session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=_MEETING_START,
        end_time=datetime(2099, 6, 1, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


def _seed_meeting_note(session: Session, meeting: Meeting, content: str, tags: list[str]) -> Note:
    """A note on the meeting's date, which the condenser selects."""
    return NotesRepository(session).create(
        content=content, tags=tags, meeting_id=meeting.id, source="meeting",
        created_at=meeting.start_time,
    )


def _condense_with(tmp_path: Path, summary: str) -> AbstractContextManager[object]:
    """Answer note_condensation with summary from a stubbed provider."""
    manager = stubbed_manager(
        tmp_path, {"gemini": complete(ProviderType.GEMINI, content=summary)},
        {"note_condensation": ("gemini", None)},
    )
    return patch.object(pm_module, "_provider_manager_instance", manager)


def _contents(session: Session, meeting_id: int) -> list[str]:
    rows = session.query(Note).filter(Note.meeting_id == meeting_id).all()
    return sorted(n.content for n in rows)


def _condensed(session: Session, meeting_id: int) -> list[Note]:
    return session.query(Note).filter(
        Note.meeting_id == meeting_id, Note.source == "condensed"
    ).all()


class TestNotesLog:
    """notes log writes each line through add_note, and the condensation through record_condensation."""

    @pytest.fixture(autouse=True)
    def _no_editor(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('EDITOR', raising=False)

    def test_each_line_is_written_as_a_meeting_note_with_its_tags(
        self, db_session: Session
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Log Lines Meeting 2099")

        # Two lines, a blank line ends bulk entry, 'n' skips condensation
        result = CliRunner().invoke(
            notes, ["log", "--meeting", str(meeting.id)],
            input="First sentinel line #cf\nSecond sentinel line\n\nn\n",
        )

        assert result.exit_code == 0, result.output
        rows = db_session.query(Note).filter(Note.meeting_id == meeting.id).order_by(Note.id).all()
        assert [(n.content, n.tags, n.source) for n in rows] == [
            ("First sentinel line", ["carry-forward"], "meeting"),
            ("Second sentinel line", ["internal-only"], "meeting"),
        ]
        assert _condensed(db_session, meeting.id) == []

    def test_condense_writes_the_summary_note_and_entry_with_the_computed_tags(
        self, db_session: Session, tmp_path: Path
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Log Condense Mixed 2099")
        # Mixed-audience source notes collapse to ['internal-only'] (Ray, 20260728)
        _seed_meeting_note(db_session, meeting, "Internal detail", ["internal-only"])
        _seed_meeting_note(db_session, meeting, "Client-visible detail", ["client-report"])
        db_session.commit()

        # A blank line ends bulk entry (no new notes); 'y' condenses the seeded ones
        with _condense_with(tmp_path, _SENTINEL_CONDENSED_SUMMARY):
            result = CliRunner().invoke(
                notes, ["log", "--meeting", str(meeting.id)], input="\ny\n",
            )

        assert result.exit_code == 0, result.output
        db_session.expire_all()
        assert db_session.get(Meeting, meeting.id).condensed_summary == _SENTINEL_CONDENSED_SUMMARY
        (condensed,) = _condensed(db_session, meeting.id)
        assert (condensed.content, condensed.tags) == (
            _SENTINEL_CONDENSED_SUMMARY, ["internal-only"],
        )
        entry = db_session.query(TimeEntry).filter(TimeEntry.meeting_id == meeting.id).one()
        assert (entry.note_id, entry.entry_date) == (condensed.id, date(2099, 6, 1))

    def test_t13_logged_notes_persist_when_the_condense_prompt_is_cancelled(
        self, db_session: Session
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Log Abort Meeting 2099-96")

        with patch('click.confirm', side_effect=click.Abort()):
            CliRunner().invoke(
                notes, ["log", "--meeting", str(meeting.id)],
                input="Sentinel log abort one\nSentinel log abort two\n\n",
            )

        assert _contents(db_session, meeting.id) == [
            "Sentinel log abort one", "Sentinel log abort two",
        ]

    def test_t16_a_failed_line_rolls_back_only_that_line(self, db_session: Session) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Log Line Failure 2099-96")
        real_create = NotesRepository.create
        calls = []

        def create(self, *args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                self.session.execute(text("SELECT 1/0"))
            return real_create(self, *args, **kwargs)

        with patch.object(NotesRepository, "create", create):
            result = CliRunner().invoke(
                notes, ["log", "--meeting", str(meeting.id)],
                input="Sentinel line one\nSentinel line two\nSentinel line three\n\nn\n",
            )

        assert result.exit_code == 0, result.output
        assert "✗ Error:" not in result.output
        assert _contents(db_session, meeting.id) == [
            "Sentinel line one", "Sentinel line three",
        ]

    def test_t17_a_failed_link_writes_no_summary_and_keeps_the_cost_and_the_notes(
        self, db_session: Session, tmp_path: Path
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Log Condense Failure 2099-96")
        _seed_meeting_note(db_session, meeting, "Sentinel condense source", ["internal-only"])
        # The meeting's entry on its date carries another client's project, so
        # repointing it at the condensed note fails in the repository.
        owner = Client(name="Sentinel Log Project Owner 2099-96")
        other = Client(name="Sentinel Log Entry Client 2099-96")
        db_session.add_all([owner, other])
        db_session.flush()
        project = Project(name="Sentinel Log Project 2099-96", client_id=owner.id)
        db_session.add(project)
        db_session.flush()
        detail = _seed_meeting_note(db_session, meeting, "Sentinel entry detail", ["internal-only"])
        entry = TimeEntriesRepository(db_session).create(
            note_id=detail.id, duration_hours=0.5, entry_date=meeting.start_time.date(),
            entry_time=meeting.start_time.time(), meeting_id=meeting.id, client_id=other.id,
        )
        entry.project_id = project.id
        db_session.commit()

        with _condense_with(tmp_path, _SENTINEL_CONDENSED_SUMMARY):
            result = CliRunner().invoke(
                notes, ["log", "--meeting", str(meeting.id)],
                input="Sentinel condense failure note\n\ny\n",
            )

        assert result.exit_code == 0, result.output
        db_session.expire_all()
        assert db_session.get(Meeting, meeting.id).condensed_summary is None
        assert _condensed(db_session, meeting.id) == []
        assert db_session.get(TimeEntry, entry.id).note_id == detail.id
        assert db_session.query(AiCost).filter(
            AiCost.meeting_id == meeting.id, AiCost.interaction_type == "note_condensation",
        ).count() == 1
        assert "Sentinel condense failure note" in _contents(db_session, meeting.id)

    def test_t18_condense_repoints_the_existing_entry(
        self, db_session: Session, tmp_path: Path
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Log Repoint 2099-96")
        existing_note = _seed_meeting_note(
            db_session, meeting, "Sentinel repoint seeded detail", ["internal-only"],
        )
        existing = TimeEntriesRepository(db_session).create(
            note_id=existing_note.id, duration_hours=0.5,
            entry_date=meeting.start_time.date(), entry_time=meeting.start_time.time(),
            category='meeting', meeting_id=meeting.id,
        )
        db_session.commit()
        entry_id = existing.id

        with _condense_with(tmp_path, _SENTINEL_CONDENSED_SUMMARY):
            result = CliRunner().invoke(
                notes, ["log", "--meeting", str(meeting.id)],
                input="Sentinel repoint note\n\ny\n",
            )

        assert result.exit_code == 0, result.output
        db_session.expire_all()
        entries = db_session.query(TimeEntry).filter(TimeEntry.meeting_id == meeting.id).all()
        assert [e.id for e in entries] == [entry_id]
        (condensed,) = _condensed(db_session, meeting.id)
        assert entries[0].note_id == condensed.id

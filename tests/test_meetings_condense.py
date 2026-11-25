"""
CLI-level coverage for 'workmain meetings condense'.

Each test runs the command through CliRunner against the test's database and
asserts the exit code, the rows the path writes or leaves alone, and on a
refusal the Error line on stderr. Nothing is patched between the command and
meetings_service.record_condensation; UnitOfWork refuses to enter inside an
open session_scope(), so a passing test also shows the use case ran with the
command's scope closed. The provider's reply comes from
tests/mocks/stub_providers.py, through
provider_manager._provider_manager_instance.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner, Result
from sqlalchemy.orm import Session

from tests.mocks.stub_providers import StubProvider, complete, cut_off, stubbed_manager
from workmain.ai import provider_manager as pm_module
from workmain.ai.base_provider import ProviderType
from workmain.cli.commands.meetings import meetings
from workmain.database.models import AiCost, Client, Meeting, Note, Project, TimeEntry
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

_MEETING_DATE = datetime(2099, 6, 4, 9, 0)
_SENTINEL_SUMMARY_V1 = "Sentinel condensed summary 2099-07-28 v1"
_SENTINEL_SUMMARY_V2 = "Sentinel condensed summary 2099-07-28 v2"


def _seed_meeting(session: Session, title: str) -> Meeting:
    m = Meeting(
        title=title,
        start_time=_MEETING_DATE,
        end_time=datetime(2099, 6, 4, 9, 30),
        is_recurring=False,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


def _seed_note(session: Session, meeting: Meeting, content: str, tags: list[str]) -> Note:
    return NotesRepository(session).create(
        content=content, tags=tags, meeting_id=meeting.id, source="meeting",
        created_at=_MEETING_DATE,
    )


def _condense(tmp_path: Path, meeting_id: int, stubs: dict[str, StubProvider]) -> Result:
    manager = stubbed_manager(tmp_path, stubs, {"note_condensation": ("gemini", "claude")})
    with patch.object(pm_module, "_provider_manager_instance", manager):
        return CliRunner(mix_stderr=False).invoke(meetings, ["condense", str(meeting_id)])


def _answer(summary: str) -> dict[str, StubProvider]:
    return {"gemini": complete(ProviderType.GEMINI, content=summary)}


def _condensed(session: Session, meeting_id: int) -> list[Note]:
    return session.query(Note).filter(
        Note.meeting_id == meeting_id, Note.source == "condensed"
    ).order_by(Note.id).all()


def _entries(session: Session, meeting_id: int) -> list[TimeEntry]:
    return session.query(TimeEntry).filter(TimeEntry.meeting_id == meeting_id).all()


class TestMeetingsCondense:
    """meetings condense records the summary, its note and its entry through record_condensation."""

    def test_condense_writes_the_summary_note_and_entry_with_the_computed_tags(
        self, db_session: Session, tmp_path: Path
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Meetings Condense Mixed 2099")
        # Mixed-audience source notes collapse to ['internal-only'] (Ray, 20260728)
        _seed_note(db_session, meeting, "Internal detail", ["internal-only"])
        _seed_note(db_session, meeting, "Client-visible detail", ["client-report"])
        db_session.commit()

        result = _condense(tmp_path, meeting.id, _answer(_SENTINEL_SUMMARY_V1))

        assert result.exit_code == 0, result.output
        db_session.expire_all()
        assert db_session.get(Meeting, meeting.id).condensed_summary == _SENTINEL_SUMMARY_V1
        (condensed,) = _condensed(db_session, meeting.id)
        assert (condensed.content, condensed.tags) == (_SENTINEL_SUMMARY_V1, ["internal-only"])
        (entry,) = _entries(db_session, meeting.id)
        assert (entry.note_id, entry.entry_date, entry.category) == (
            condensed.id, _MEETING_DATE.date(), "meeting",
        )

    def test_a_second_condense_repoints_the_entry_rather_than_adding_one(
        self, db_session: Session, tmp_path: Path
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Meetings Condense Relink 2099")
        _seed_note(db_session, meeting, "Both-tagged detail", ["both"])
        db_session.commit()

        (tmp_path / "v1").mkdir()
        (tmp_path / "v2").mkdir()

        first = _condense(tmp_path / "v1", meeting.id, _answer(_SENTINEL_SUMMARY_V1))
        assert first.exit_code == 0, first.output
        db_session.expire_all()
        (first_entry,) = _entries(db_session, meeting.id)

        second = _condense(tmp_path / "v2", meeting.id, _answer(_SENTINEL_SUMMARY_V2))

        assert second.exit_code == 0, second.output
        db_session.expire_all()
        (entry,) = _entries(db_session, meeting.id)
        latest = _condensed(db_session, meeting.id)[-1]
        assert (entry.id, entry.note_id, latest.content) == (
            first_entry.id, latest.id, _SENTINEL_SUMMARY_V2,
        )

    def test_a_failed_link_writes_no_summary_and_keeps_the_cost_row(
        self, db_session: Session, tmp_path: Path
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Meetings Condense Link Failure 2099")
        _seed_note(db_session, meeting, "Sentinel condense source", ["internal-only"])
        # The meeting's entry on its date carries another client's project, so
        # repointing it at the condensed note fails in the repository.
        owner = Client(name="Sentinel Condense Project Owner 2099")
        other = Client(name="Sentinel Condense Entry Client 2099")
        db_session.add_all([owner, other])
        db_session.flush()
        project = Project(name="Sentinel Condense Project 2099", client_id=owner.id)
        db_session.add(project)
        db_session.flush()
        detail = _seed_note(db_session, meeting, "Sentinel entry detail", ["internal-only"])
        entry = TimeEntriesRepository(db_session).create(
            note_id=detail.id, duration_hours=0.5, entry_date=_MEETING_DATE.date(),
            entry_time=_MEETING_DATE.time(), meeting_id=meeting.id, client_id=other.id,
        )
        entry.project_id = project.id
        db_session.commit()

        result = _condense(tmp_path, meeting.id, _answer(_SENTINEL_SUMMARY_V1))

        assert result.exit_code == 1, result.output
        db_session.expire_all()
        assert db_session.get(Meeting, meeting.id).condensed_summary is None
        assert _condensed(db_session, meeting.id) == []
        assert db_session.get(TimeEntry, entry.id).note_id == detail.id
        assert db_session.query(AiCost).filter(
            AiCost.meeting_id == meeting.id, AiCost.interaction_type == "note_condensation",
        ).count() == 1

    def test_a_refused_condensation_exits_3_with_its_cause_and_writes_nothing(
        self, db_session: Session, tmp_path: Path
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Meetings Condense Refusal 2099")
        _seed_note(db_session, meeting, "Discussed refusal", ["client-report"])
        db_session.commit()

        result = _condense(tmp_path, meeting.id, {
            "gemini": cut_off(ProviderType.GEMINI),
            "claude": cut_off(ProviderType.CLAUDE),
        })

        assert result.exit_code == 3, result.output
        assert "note_condensation" in result.stderr
        assert "4000" in result.stderr
        assert len(result.stderr.strip().splitlines()) == 1
        db_session.expire_all()
        assert db_session.get(Meeting, meeting.id).condensed_summary is None
        assert _condensed(db_session, meeting.id) == []

    def test_a_fallback_reply_is_recorded_as_the_summary(
        self, db_session: Session, tmp_path: Path
    ) -> None:
        meeting = _seed_meeting(db_session, "Sentinel Meetings Condense Fallback 2099")
        _seed_note(db_session, meeting, "Discussed fallback", ["client-report"])
        db_session.commit()

        result = _condense(tmp_path, meeting.id, {
            "gemini": cut_off(ProviderType.GEMINI),
            "claude": complete(ProviderType.CLAUDE, content="Recovered summary"),
        })

        assert result.exit_code == 0, result.output
        db_session.expire_all()
        assert db_session.get(Meeting, meeting.id).condensed_summary == "Recovered summary"
        assert [n.content for n in _condensed(db_session, meeting.id)] == ["Recovered summary"]

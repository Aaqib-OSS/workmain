"""
Command coverage for workmain/cli/commands/clockify.py (Issue #202).

Each test runs a command through CliRunner with a mock renderer, and asserts
the service's arguments, the view and result the renderer received, and the
exit code. TestClockifyCommands patches the service functions a command
reaches. TestPullReachesApplyPullWithNoScopeOpen runs the pull paths end to
end, with only ClockifyClient replaced. No test calls Clockify.
"""

from contextlib import ExitStack
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from sqlalchemy.orm import Session

from workmain.cli.commands.clockify import (
    CONFLICT,
    PULL,
    PUSH,
    REPORT_SAVED,
    STATUS,
    clockify,
    clockify_report,
    clockify_sync,
)
from workmain.cli.output import Renderer, WorkmAInGroup
from workmain.database.connection import scope_open
from workmain.database.models import Note, TimeEntry
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.integrations.clockify.client import ClockifyClient
from workmain.services import clockify_service
from workmain.services.exceptions import (
    ClockifyNotConfiguredError,
    IntegrationError,
    ServiceValidationError,
)
from workmain.services.results import Page
from workmain.services.unit_of_work import UnitOfWork

D = date(2099, 1, 5)


def _run(args, patched=(), input=None):
    """Invoke `clockify <args>` with the named service functions patched.

    Returns the result, the renderer and the patched functions by name.
    """
    renderer = Mock(spec=Renderer)
    with ExitStack() as stack:
        mocks = {
            name: stack.enter_context(patch.object(clockify_service, name, autospec=True))
            for name in patched
        }
        result = CliRunner(mix_stderr=False).invoke(
            clockify, args, obj=renderer, input=input
        )
    return result, renderer, mocks


def _ok_result():
    return Mock(error=None)


def _entry(description="Remote work"):
    return SimpleNamespace(clockify_id="remote-id", description=description)


class _RecordUnitOfWork:
    """Equal to any UnitOfWork built with record=True, the pull's import record."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UnitOfWork) and other._record is True


RECORD_UOW = _RecordUnitOfWork()


def _item(kind, entry=None):
    pair = Page((SimpleNamespace(source="WorkmAIn"),), 1) if kind == "conflict" else Page((), 0)
    return SimpleNamespace(kind=kind, entry=entry or _entry(), pair=pair, local_id=7)


class TestClockifyCommands:

    def test_c1_status(self):
        result, renderer, m = _run(["status"], ["get_status"])

        assert result.exit_code == 0, result.stderr
        m["get_status"].assert_called_once()
        session, now = m["get_status"].call_args.args
        assert isinstance(session, Session) and isinstance(now, datetime)
        renderer.record.assert_called_once_with(STATUS, m["get_status"].return_value)

    def test_c2_status_integration_error(self):
        renderer = Mock(spec=Renderer)
        with patch.object(
            clockify_service, "get_status", autospec=True, side_effect=IntegrationError("x")
        ):
            result = CliRunner(mix_stderr=False).invoke(clockify, ["status"], obj=renderer)

        assert result.exit_code == 3
        assert "Error: x" in result.stderr
        renderer.record.assert_not_called()

    def test_c3_report_save(self):
        result, renderer, m = _run(
            ["report", "save", "weekly", "-b", "2099-01-05", "-e", "2099-01-09"], ["save_report"]
        )

        assert result.exit_code == 0, result.stderr
        args = m["save_report"].call_args.args
        assert args[:3] == ("weekly", date(2099, 1, 5), date(2099, 1, 9))
        assert isinstance(args[3], date)
        renderer.record.assert_called_once_with(REPORT_SAVED, m["save_report"].return_value)

    def test_c4_report_save_without_an_api_key(self):
        renderer = Mock(spec=Renderer)
        with patch.object(
            clockify_service, "save_report", autospec=True,
            side_effect=ClockifyNotConfiguredError("k"),
        ):
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["report", "save"], obj=renderer
            )

        assert result.exit_code == 1
        assert "Error: k" in result.stderr

    @pytest.mark.parametrize("args,on_date,include_synced", [
        ([], None, False),
        (["-d", "2099-01-05"], D, False),
        (["--all"], None, True),
        (["-d", "2099-01-05", "--all"], D, True),
    ])
    def test_c5_sync_push(self, args, on_date, include_synced):
        renderer = Mock(spec=Renderer)
        with patch.object(clockify_service, "plan_push", autospec=True) as plan_push, \
             patch.object(clockify_service, "push", autospec=True,
                          return_value=_ok_result()) as push:
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["sync", "push", *args], obj=renderer
            )

        assert result.exit_code == 0, result.stderr
        plan_push.assert_called_once()
        assert isinstance(plan_push.call_args.args[0], Session)
        assert plan_push.call_args.kwargs == {
            "on_date": on_date, "include_synced": include_synced,
        }
        push.assert_called_once_with(plan_push.return_value)
        renderer.report.assert_called_once_with(PUSH, push.return_value, quiet=False)

    def test_c6_sync_push_quiet(self):
        renderer = Mock(spec=Renderer)
        with patch.object(clockify_service, "plan_push", autospec=True), \
             patch.object(clockify_service, "push", autospec=True,
                          return_value=_ok_result()) as push:
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["sync", "push", "-q"], obj=renderer
            )

        assert result.exit_code == 0
        renderer.report.assert_called_once_with(PUSH, push.return_value, quiet=True)

    def test_c7_sync_push_renders_then_raises_the_result_error(self):
        renderer = Mock(spec=Renderer)
        failed = Mock(error=IntegrationError("1 of 2 entries were not pushed to Clockify"))
        with patch.object(clockify_service, "plan_push", autospec=True), \
             patch.object(clockify_service, "push", autospec=True, return_value=failed):
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["sync", "push"], obj=renderer
            )

        renderer.report.assert_called_once_with(PUSH, failed, quiet=False)
        assert result.exit_code == 3
        assert "Error: 1 of 2 entries were not pushed to Clockify" in result.stderr

    def test_c8_sync_pull_quiet_asks_nothing(self):
        renderer = Mock(spec=Renderer)
        entries = (_entry("one"), _entry("two"))
        items = [_item("new", e) for e in entries]
        with patch.object(clockify_service, "fetch_pull", autospec=True,
                          return_value=entries) as fetch_pull, \
             patch.object(clockify_service, "classify", autospec=True,
                          side_effect=items) as classify, \
             patch.object(clockify_service, "apply_pull", autospec=True) as apply_pull, \
             patch.object(clockify_service, "pull_result", autospec=True,
                          return_value=_ok_result()) as pull_result, \
             patch("workmain.cli.commands.clockify.click.prompt") as prompt:
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["sync", "pull", "-q", "-b", "2099-01-05"], obj=renderer
            )

        assert result.exit_code == 0, result.stderr
        fetch_pull.assert_called_once_with(D, None)
        assert classify.call_count == 2
        assert [c.args[0] for c in apply_pull.call_args_list] == [RECORD_UOW, RECORD_UOW]
        assert [c.args[2] for c in apply_pull.call_args_list] == [None, None]
        prompt.assert_not_called()
        renderer.report.assert_called_once_with(PULL, pull_result.return_value, quiet=True)

    def _pull_one(self, item, input):
        renderer = Mock(spec=Renderer)
        with patch.object(clockify_service, "fetch_pull", autospec=True,
                          return_value=(item.entry,)), \
             patch.object(clockify_service, "classify", autospec=True, return_value=item), \
             patch.object(clockify_service, "apply_pull", autospec=True) as apply_pull, \
             patch.object(clockify_service, "pull_result", autospec=True,
                          return_value=_ok_result()):
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["sync", "pull"], obj=renderer, input=input
            )
        return result, renderer, apply_pull

    def test_c9_a_conflict_shows_the_pair_and_links(self):
        item = _item("conflict")

        result, renderer, apply_pull = self._pull_one(item, "1\n")

        assert result.exit_code == 0, result.stderr
        renderer.collection.assert_called_once_with(CONFLICT, item.pair)
        apply_pull.assert_called_once_with(
            RECORD_UOW, item, clockify_service.PullAnswer("link", None),
        )

    def test_c10_a_new_entry_asks_for_tags(self):
        item = _item("new")

        result, renderer, apply_pull = self._pull_one(item, "#cf\n")

        assert result.exit_code == 0, result.stderr
        apply_pull.assert_called_once_with(
            RECORD_UOW, item, clockify_service.PullAnswer("import", "#cf"),
        )

    def test_c11_a_bad_conflict_answer_is_asked_again(self):
        item = _item("conflict")

        result, renderer, apply_pull = self._pull_one(item, "4\n2\n\n")

        assert result.exit_code == 0, result.stderr
        apply_pull.assert_called_once_with(
            RECORD_UOW, item, clockify_service.PullAnswer("import", ""),
        )

    def test_c12_sync_both(self):
        renderer = Mock(spec=Renderer)
        with patch.object(clockify_service, "plan_push", autospec=True) as plan_push, \
             patch.object(clockify_service, "push", autospec=True,
                          return_value=_ok_result()) as push, \
             patch.object(clockify_service, "fetch_pull", autospec=True,
                          return_value=()) as fetch_pull, \
             patch.object(clockify_service, "pull_result", autospec=True,
                          return_value=_ok_result()) as pull_result:
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["sync", "both", "-d", "2099-01-05"], obj=renderer
            )

        assert result.exit_code == 0, result.stderr
        assert plan_push.call_args.kwargs == {"on_date": D}
        fetch_pull.assert_called_once_with(D, D)
        assert renderer.report.call_args_list == [
            ((PUSH, push.return_value), {}),
            ((PULL, pull_result.return_value), {}),
        ]

    def test_c13_sync_both_raises_the_push_error_after_both_reports(self):
        renderer = Mock(spec=Renderer)
        failed_push = Mock(error=ServiceValidationError("1 of 2 entries were not pushed"))
        with patch.object(clockify_service, "plan_push", autospec=True), \
             patch.object(clockify_service, "push", autospec=True, return_value=failed_push), \
             patch.object(clockify_service, "fetch_pull", autospec=True, return_value=()), \
             patch.object(clockify_service, "pull_result", autospec=True,
                          return_value=_ok_result()):
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["sync", "both"], obj=renderer
            )

        assert renderer.report.call_count == 2
        assert result.exit_code == 1
        assert "Error: 1 of 2 entries were not pushed" in result.stderr

    @pytest.mark.parametrize("group", [clockify, clockify_report, clockify_sync])
    def test_c14_every_group_is_a_wiring_group(self, group):
        assert isinstance(group, WorkmAInGroup)

    def test_c15_a_bad_date_is_a_usage_error(self):
        result, renderer, m = _run(["sync", "push", "-d", "2026-13-01"], ["plan_push", "push"])

        assert result.exit_code == 2
        assert "Error:" in result.stderr
        m["plan_push"].assert_not_called()

    def test_c16_pull_classifies_each_entry_after_the_last_is_applied(self):
        renderer = Mock(spec=Renderer)
        entries = (_entry("one"), _entry("two"))
        parent = Mock()
        with patch.object(clockify_service, "fetch_pull", autospec=True,
                          return_value=entries), \
             patch.object(clockify_service, "classify", autospec=True,
                          side_effect=[_item("new", e) for e in entries]) as classify, \
             patch.object(clockify_service, "apply_pull", autospec=True) as apply_pull, \
             patch.object(clockify_service, "pull_result", autospec=True,
                          return_value=_ok_result()):
            parent.attach_mock(classify, "classify")
            parent.attach_mock(apply_pull, "apply_pull")
            result = CliRunner(mix_stderr=False).invoke(
                clockify, ["sync", "pull", "-q"], obj=renderer
            )

        assert result.exit_code == 0, result.stderr
        assert [c[0] for c in parent.mock_calls] == [
            "classify", "apply_pull", "classify", "apply_pull",
        ]
        first, second = (c.args[0] for c in classify.call_args_list)
        assert first is not second
        first_uow, second_uow = (c.args[0] for c in apply_pull.call_args_list)
        assert first_uow is not second_uow


def _raw(clockify_id: str, description: str, start: datetime, hours: float) -> dict:
    """A Clockify API time entry starting at a local time."""
    begin = start.astimezone()
    end = begin + timedelta(hours=hours)
    return {
        "id": clockify_id,
        "description": description,
        "timeInterval": {"start": begin.isoformat(), "end": end.isoformat()},
    }


class TestPullReachesApplyPullWithNoScopeOpen:
    """
    Each pull path reaches apply_pull with no session_scope() open, and imports through it.

    ClockifyClient is the one replacement: building it returns one
    Mock(spec=ClockifyClient), so fetch_pull, classify, push and apply_pull
    run unpatched. apply_pull is wrapped to record scope_open() on entry,
    since a UnitOfWork(record=True) is not refused inside an open scope.
    """

    @staticmethod
    def _run(args: list, client: Mock, input: str | None = None) -> tuple:
        renderer = Mock(spec=Renderer)
        scope_open_on_entry = []
        real_apply_pull = clockify_service.apply_pull

        def recording_apply_pull(
            uow: UnitOfWork,
            item: clockify_service.PullItem,
            answer: clockify_service.PullAnswer | None,
        ) -> clockify_service.PullOutcome:
            scope_open_on_entry.append(scope_open())
            return real_apply_pull(uow, item, answer)

        with patch.object(clockify_service, "ClockifyClient", return_value=client), \
             patch.object(clockify_service, "apply_pull", recording_apply_pull):
            result = CliRunner(mix_stderr=False).invoke(
                clockify, args, obj=renderer, input=input
            )
        return result, renderer, scope_open_on_entry

    @staticmethod
    def _imported(db_session: Session, clockify_id: str) -> TimeEntry:
        return db_session.query(TimeEntry).filter(TimeEntry.clockify_id == clockify_id).one()

    def test_sync_pull_imports_a_new_entry_with_no_scope_open(
        self, db_session: Session
    ) -> None:
        client = Mock(spec=ClockifyClient)
        client.get_time_entries.return_value = [
            _raw("zqv-pull-1", "Sentinel pulled work", datetime(2099, 1, 5, 6, 17), 1.5),
        ]

        result, renderer, scope_open_on_entry = self._run(
            ["sync", "pull", "-q", "-b", "2099-01-05"], client,
        )

        assert result.exit_code == 0, result.stderr
        assert scope_open_on_entry == [False]
        client.get_time_entries.assert_called_once_with(D, D)
        entry = self._imported(db_session, "zqv-pull-1")
        note = db_session.get(Note, entry.note_id)
        assert (note.content, note.source, note.tags) == (
            "Sentinel pulled work", "clockify", ["internal-only"],
        )
        (view, pulled), kwargs = renderer.report.call_args
        assert (view, kwargs) == (PULL, {"quiet": True})
        assert (pulled.totals.imported, pulled.imported.rows[0].entry_id) == (1, entry.id)

    def test_sync_both_pushes_then_imports_with_no_scope_open(
        self, db_session: Session
    ) -> None:
        local_note = NotesRepository(db_session).create(
            content="Sentinel local work", tags=["internal-only"],
        )
        local = TimeEntriesRepository(db_session).create(
            note_id=local_note.id, duration_hours=1.0, entry_date=D, entry_time=time(5, 3),
        )
        local_id = local.id
        db_session.commit()
        client = Mock(spec=ClockifyClient)
        client.create_time_entry.return_value = {"id": "zqv-pushed-1"}
        client.get_time_entries.return_value = [
            _raw("zqv-pull-2", "Sentinel remote work", datetime(2099, 1, 5, 6, 41), 0.5),
        ]

        result, renderer, scope_open_on_entry = self._run(
            ["sync", "both", "-d", "2099-01-05"], client, input="#cf\n",
        )

        assert result.exit_code == 0, result.stderr
        assert scope_open_on_entry == [False]
        client.create_time_entry.assert_called_once()
        db_session.expire_all()
        assert db_session.get(TimeEntry, local_id).clockify_id == "zqv-pushed-1"
        entry = self._imported(db_session, "zqv-pull-2")
        assert db_session.get(Note, entry.note_id).tags == ["carry-forward"]
        (push_view, pushed), _ = renderer.report.call_args_list[0]
        (pull_view, pulled), _ = renderer.report.call_args_list[1]
        assert (push_view, pushed.totals.successful) == (PUSH, 1)
        assert (pull_view, pulled.totals.imported) == (PULL, 1)


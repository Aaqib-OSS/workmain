"""Tests for automation/issue_validator.py, named for the AC they cover (§6, AC4.1)."""

import html
import importlib.util
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

_spec = importlib.util.spec_from_file_location(
    "issue_validator", ROOT / "automation" / "issue_validator.py"
)
issue_validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(issue_validator)

SCHEMA = issue_validator.load_schema(ROOT / ".github" / "ISSUE_TEMPLATE" / "issue.schema.json")
LABEL_PAIR = issue_validator.parse_label_pair(ROOT / issue_validator.STANDARDS_RELATIVE_PATH)
LIVE_LABELS = {"cli", "defect", "gap", "tests", "documentation"}
LIVE_MILESTONES = {"Phase 14 — Setup Wizard & Configuration"}


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


def fake_issue_state(open_numbers=(), closed_numbers=()):
    open_set = set(open_numbers)
    closed_set = set(closed_numbers)

    def get_issue_state(number):
        if number in closed_set:
            return "CLOSED"
        if number in open_set:
            return "OPEN"
        return None

    return get_issue_state


def render_as_written(text: str) -> str:
    """A renderer that displays every line as written, so a test not about display is unaffected by it."""
    items = "".join(f"<li>{html.escape(line.removeprefix('  - ').replace('`', ''))}</li>\n" for line in text.splitlines())
    return f"<ul>\n{items}</ul>"


RENDERED = json.loads((FIXTURES / "check_display_rendered.json").read_text())


def render_recorded(text: str) -> str:
    """GitHub's HTML for each input in check_display_rendered.json, recorded from `gh api -X POST /markdown`."""
    return RENDERED[text]


def run_validate(
    data: dict,
    label_pair: list = LABEL_PAIR,
    live_labels: set = LIVE_LABELS,
    live_milestones: set = LIVE_MILESTONES,
    get_issue_state: Callable[[int], str | None] | None = None,
    render: Callable[[str], str] = render_as_written,
) -> tuple[list[str], dict]:
    if get_issue_state is None:
        get_issue_state = fake_issue_state(open_numbers=(100, 101, 102))
    return issue_validator.validate_issue(data, SCHEMA, label_pair, live_labels, live_milestones, get_issue_state, render)


class TestAC1:
    def test_ac1_4_shapes_satisfying_the_label_pair_rule_validate(self):
        for name in (
            "shape_scheduled_standalone.json",
            "shape_scheduled_child.json",
            "shape_scheduled_with_pair_standalone.json",
            "shape_scheduled_with_pair_child.json",
            "shape_unscheduled_standalone.json",
            "shape_unscheduled_child.json",
        ):
            errors, _ = run_validate(fixture(name))
            assert errors == [], f"{name} unexpectedly failed: {errors}"

    def test_ac1_4_shapes_violating_the_label_pair_rule_fail(self):
        for name in (
            "shape_invalid_unscheduled_no_pair_standalone.json",
            "shape_invalid_unscheduled_no_pair_child.json",
        ):
            errors, _ = run_validate(fixture(name))
            assert errors, f"{name} unexpectedly passed"


class TestAC2:
    def test_ac2_1_missing_required_key_names_it(self):
        errors, _ = run_validate(fixture("ac2_1_missing_milestone.json"))
        assert any("milestone" in e for e in errors)

    def test_ac2_2_unknown_key_names_it(self):
        errors, _ = run_validate(fixture("ac2_2_unknown_key.json"))
        assert any("mileston" in e for e in errors)

    def test_ac2_3_the_two_label_pair_failures_are_distinguishable(self):
        errors_a, _ = run_validate(fixture("shape_invalid_unscheduled_no_pair_standalone.json"))
        errors_b, _ = run_validate(fixture("shape_invalid_unscheduled_both_pair_labels.json"))
        assert "unscheduled issue carries none of defect/gap" in errors_a
        assert any(e.startswith("issue carries more than one of") for e in errors_b)
        assert errors_a != errors_b

    def test_ac2_5_nonexistent_label_milestone_and_parent_each_fail(self):
        errors, _ = run_validate(fixture("ac2_5_bad_label.json"))
        assert any("not-a-real-label" in e for e in errors)

        errors, _ = run_validate(fixture("ac2_5_bad_milestone.json"))
        assert any("Not A Real Milestone" in e for e in errors)

        errors, _ = run_validate(fixture("ac2_5_bad_parent.json"), get_issue_state=fake_issue_state())
        assert any("999999" in e and "does not exist" in e for e in errors)

    def test_ac2_6a_label_pair_names_are_not_hardcoded(self):
        source = (ROOT / "automation" / "issue_validator.py").read_text()
        import re

        assert re.findall(r"['\"](defect|gap)['\"]", source) == []

    def test_ac2_6b_the_label_pair_is_parsed_from_the_standards_file(self):
        tokens = issue_validator.parse_label_pair(FIXTURES / "standards_alpha_beta.md")
        assert tokens == ["alpha", "beta"]
        assert "defect" not in tokens

    def test_the_live_standards_file_yields_exactly_the_label_pair(self):
        """A reflow of §1.3 that breaks this parse breaks every issue creation."""
        tokens = issue_validator.parse_label_pair(ROOT / issue_validator.STANDARDS_RELATIVE_PATH)
        assert tokens == ["defect", "gap"]

    def test_ac2_7_validation_is_total(self):
        errors, _ = run_validate(fixture("ac2_7_three_errors.json"))
        assert any("unknown key: extra_bogus_key" in e for e in errors)
        assert any("not-a-real-label" in e for e in errors)
        assert any("carries none of" in e for e in errors)
        assert len(errors) >= 3

    def test_ac2_8_missing_label_pair_line_aborts_before_other_checks(self):
        with pytest.raises(issue_validator.ValidationAbort) as excinfo:
            issue_validator.parse_label_pair(FIXTURES / "standards_missing_label_pair.md")
        message = str(excinfo.value)
        assert "standards_missing_label_pair.md" in message
        assert "label pair" in message

    def test_ac2_9_closed_parent_is_reported_as_closed_not_missing(self):
        data = fixture("shape_scheduled_child.json")
        errors = issue_validator.validate_live_state(
            data, LIVE_LABELS, LIVE_MILESTONES, fake_issue_state(closed_numbers=(100,))
        )
        assert any("closed" in e for e in errors)
        assert not any("does not exist" in e for e in errors)

    def test_ac2_9_nonexistent_parent_is_reported_as_missing_not_closed(self):
        data = fixture("shape_scheduled_child.json")
        errors = issue_validator.validate_live_state(
            data, LIVE_LABELS, LIVE_MILESTONES, fake_issue_state()
        )
        assert any("does not exist" in e for e in errors)
        assert not any("closed" in e for e in errors)


class TestLabelPairCases:
    """§1.3's one rule, case by case (#105). Each asserts the message, not merely that errors exist."""

    def test_label_pair_unscheduled_with_neither_label_fails_naming_what_is_missing(self):
        errors, _ = run_validate(fixture("shape_invalid_unscheduled_no_pair_standalone.json"))
        assert "unscheduled issue carries none of defect/gap" in errors

    def test_label_pair_unscheduled_with_both_labels_fails_naming_both(self):
        errors, _ = run_validate(fixture("shape_invalid_unscheduled_both_pair_labels.json"))
        offending = [e for e in errors if "more than one" in e]
        assert len(offending) == 1
        assert "defect" in offending[0] and "gap" in offending[0]

    def test_label_pair_unscheduled_with_exactly_one_label_validates_and_reaches_the_label_flags(self, tmp_path):
        data = fixture("shape_unscheduled_standalone.json")
        errors, normalized = run_validate(data)
        assert errors == []

        cmd = issue_validator.build_command(normalized, tmp_path / "body.md")
        label_values = [cmd[i + 1] for i, part in enumerate(cmd) if part == "--label"]
        assert "defect" in label_values

    def test_label_pair_a_milestone_carrying_a_pair_label_validates(self):
        """Scheduling work pulled in from the unscheduled pool does not strip its label."""
        for name in (
            "shape_scheduled_with_pair_standalone.json",
            "shape_scheduled_with_pair_child.json",
        ):
            errors, _ = run_validate(fixture(name))
            assert errors == [], f"{name} unexpectedly failed: {errors}"

    def test_label_pair_a_milestone_carrying_both_labels_still_fails(self):
        """At-most-one is not gated on the milestone: one kept label is a record, two is incoherent."""
        errors, _ = run_validate(fixture("shape_invalid_scheduled_both_pair_labels.json"))
        offending = [e for e in errors if "more than one" in e]
        assert len(offending) == 1
        assert "defect" in offending[0] and "gap" in offending[0]


class TestSingleLine:
    """Every string-typed value is a single line; `context` is the sole exception (#88)."""

    def test_single_line_newline_in_an_ac_is_refused_naming_the_index(self):
        errors, _ = run_validate(fixture("single_line_newline_in_ac.json"))
        assert "key 'acs[1].criterion' must be a single line" in errors

    def test_single_line_newline_in_the_title_is_refused(self):
        errors, _ = run_validate(fixture("single_line_newline_in_title.json"))
        assert "key 'title' must be a single line" in errors

    def test_single_line_refusal_participates_in_total_reporting(self):
        """DR5 — the newline does not stop the run before other errors are collected."""
        data = fixture("single_line_newline_in_ac.json")
        data["labels"] = ["not-a-real-label", "defect"]
        data["extra_bogus_key"] = True

        errors, _ = run_validate(data)
        assert "key 'acs[1].criterion' must be a single line" in errors
        assert any("not-a-real-label" in e for e in errors)
        assert any("unknown key: extra_bogus_key" in e for e in errors)

    def test_single_line_the_valid_fixtures_are_unaffected(self):
        open_all = fake_issue_state(open_numbers=(100, 101, 102, 201, 202))
        for name in ("valid_minimal.json", "valid_full.json"):
            errors, _ = run_validate(fixture(name), get_issue_state=open_all)
            assert errors == [], f"{name} unexpectedly failed: {errors}"

    def test_single_line_a_multi_line_context_is_still_accepted(self):
        """`context` is the issue body's prose and is deliberately exempt."""
        data = fixture("valid_minimal.json")
        data["context"] = "First paragraph.\n\nSecond paragraph."
        errors, _ = run_validate(data)
        assert errors == []

    def test_single_line_render_body_is_not_repaired(self):
        """DR6 — the fix is refusal at validation, not repair at render."""
        acs = [
            {"criterion": "one", "check": "first"},
            {"criterion": "two\nsplit", "check": "second"},
        ]
        rendered = issue_validator.render_body("Context line.", acs)
        assert len([line for line in rendered.splitlines() if line.startswith("- ")]) == 2
        assert "\nsplit" in rendered


class TestStructuredCriteria:
    """A criterion and its check are separate fields, and a criterion that is only a command is refused (#120)."""

    def test_structured_skeleton_carries_the_criterion_and_check_fields(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "automation" / "issue_validator.py"), "--new"],
            capture_output=True,
            text=True,
            check=True,
        )
        skeleton_acs = json.loads(result.stdout)["acs"]
        assert len(skeleton_acs) == 1
        assert sorted(skeleton_acs[0]) == sorted(SCHEMA["acs"]["items"]["keys"])

    def test_structured_criterion_that_is_only_code_is_refused(self):
        errors, _ = run_validate(fixture("criterion_only_code.json"))
        assert errors == ["acs[0].criterion is only code — it names no property of the delivered system"]

    def test_structured_one_string_criterion_is_refused(self):
        errors, _ = run_validate(fixture("criterion_legacy_string.json"))
        assert errors == ["key 'acs[0]' must be of type object"]

    def test_structured_criterion_without_a_check_is_refused(self):
        data = fixture("valid_minimal.json")
        del data["acs"][0]["check"]
        errors, _ = run_validate(data)
        assert errors == ["missing required key: acs[0].check"]

    def test_structured_unknown_key_in_a_criterion_is_named(self):
        data = fixture("valid_minimal.json")
        data["acs"][0]["id"] = "AC1"
        errors, _ = run_validate(data)
        assert errors == ["unknown key: acs[0].id"]

    def test_structured_refusal_stops_the_create_path_before_gh_runs(self, tmp_path, monkeypatch):
        issue_file = tmp_path / "issue.json"
        issue_file.write_text(json.dumps(fixture("criterion_only_code.json")))

        monkeypatch.setattr(issue_validator, "gh_live_labels", lambda: LIVE_LABELS)
        monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
        monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
        monkeypatch.setattr(issue_validator, "gh_render_markdown", render_as_written)
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **k: pytest.fail("gh issue create must not run for a refused issue"),
        )

        assert issue_validator.main([str(issue_file), "--create"]) == 1

    def test_structured_render_keeps_criterion_and_check_distinct(self):
        acs = [{"criterion": "no module carries a header", "check": "`grep -rn x workmain/` returns zero hits"}]
        rendered = issue_validator.render_body("Context line.", acs)
        assert rendered == (
            "Context line.\n"
            "\n"
            "**ACs**\n"
            "\n"
            "- no module carries a header\n"
            "  - Checked by: `grep -rn x workmain/` returns zero hits\n"
        )


ALTERING_FORMS = [
    pytest.param(
        'grep -nE "config\\.get\\(" workmain/ai/providers/ returning zero hits',
        '`grep -nE "config\\.get\\(" workmain/ai/providers/` returning zero hits',
        id="backslash-before-punctuation",
    ),
    pytest.param(
        "python3 automation/session_param_check.py <service module> printing nothing",
        "`python3 automation/session_param_check.py <service module>` printing nothing",
        id="placeholder",
    ),
    pytest.param(
        "grep -rn __repr__ workmain/ returning zero hits",
        "`grep -rn __repr__ workmain/` returning zero hits",
        id="double-underscore-name",
    ),
]


def with_check(check: str) -> dict:
    data = fixture("valid_minimal.json")
    data["acs"][0]["check"] = check
    return data


class TestCheckDisplay:
    """A check displays on GitHub as written, judged by GitHub's renderer."""

    @pytest.mark.parametrize("unquoted, quoted", ALTERING_FORMS)
    def test_check_display_a_form_that_alters_display_is_refused(self, unquoted: str, quoted: str) -> None:
        errors, _ = run_validate(with_check(unquoted), render=render_recorded)
        assert len(errors) == 1
        assert errors[0].startswith("acs[0].check displays on GitHub as ")

    @pytest.mark.parametrize("unquoted, quoted", ALTERING_FORMS)
    def test_check_display_the_same_check_in_backticks_is_accepted(self, unquoted: str, quoted: str) -> None:
        errors, _ = run_validate(with_check(quoted), render=render_recorded)
        assert errors == []

    def test_check_display_prose_that_displays_as_written_is_accepted(self) -> None:
        check = "a stated reading by Ray of docs/standards/1-workflow.md §1.2 for whether a check displays as written"
        errors, _ = run_validate(with_check(check), render=render_recorded)
        assert errors == []

    def test_check_display_renders_every_check_in_one_call_as_the_lines_render_body_writes(self) -> None:
        seen = []

        def spy(text: str) -> str:
            seen.append(text)
            return render_as_written(text)

        data = with_check("`pytest automation/` reporting 0 failed")
        data["acs"].append({"criterion": "a second property", "check": "`git status` showing a clean tree"})
        run_validate(data, render=spy)
        body_lines = issue_validator.render_body(data["context"], data["acs"]).splitlines()
        assert len(seen) == 1
        assert seen[0].splitlines() == [line for line in body_lines if line.startswith("  - Checked by: ")]

    def test_check_display_names_the_index_of_the_check_that_displays_differently(self) -> None:
        data = with_check("`pytest automation/` reporting 0 failed")
        data["acs"].append({"criterion": "a second property", "check": ALTERING_FORMS[1].values[0]})
        errors, _ = run_validate(data, render=render_recorded)
        assert len(errors) == 1
        assert errors[0].startswith("acs[1].check displays on GitHub as ")

    def test_check_display_refusal_stops_the_create_path_before_gh_issue_create_runs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        issue_file = tmp_path / "issue.json"
        issue_file.write_text(json.dumps(with_check(ALTERING_FORMS[1].values[0])))

        monkeypatch.setattr(issue_validator, "gh_live_labels", lambda: LIVE_LABELS)
        monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
        monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
        monkeypatch.setattr(issue_validator, "gh_render_markdown", render_recorded)
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **k: pytest.fail("gh issue create must not run for a refused issue"),
        )

        assert issue_validator.main([str(issue_file), "--create"]) == 1

    def test_check_display_gh_render_markdown_sends_the_text_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls = []

        def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="<p>x</p>", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        assert issue_validator.gh_render_markdown("a `b` <c>") == "<p>x</p>"
        assert calls == [["gh", "api", "-X", "POST", "/markdown", "-f", "mode=gfm", "-f", "text=a `b` <c>"]]


class TestAC3:
    def test_ac3_1_default_run_creates_nothing(self, tmp_path, monkeypatch, capsys):
        issue_file = tmp_path / "issue.json"
        issue_file.write_text(json.dumps(fixture("valid_minimal.json")))

        monkeypatch.setattr(issue_validator, "gh_live_labels", lambda: LIVE_LABELS)
        monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
        monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
        monkeypatch.setattr(issue_validator, "gh_render_markdown", render_as_written)
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **k: pytest.fail("gh issue create must not run without --create"),
        )

        exit_code = issue_validator.main([str(issue_file)])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "gh issue create" in captured.out

    def test_ac3_2_printed_command_carries_every_populated_field(self, tmp_path):
        body_file = tmp_path / "body.md"
        cmd = issue_validator.build_command(fixture("valid_full.json"), body_file)
        assert "--title" in cmd
        assert "--body-file" in cmd
        assert "--parent" in cmd and "100" in cmd
        assert cmd.count("--label") == 3
        blocked_by_index = cmd.index("--blocked-by")
        assert cmd[blocked_by_index + 1] == "201,202"
        assert cmd.count("--blocked-by") == 1
        assert "--milestone" not in cmd  # valid_full.json's milestone is null

    def test_ac3_3_project_flag_always_present(self, tmp_path):
        body_file = tmp_path / "body.md"
        cmd = issue_validator.build_command(fixture("valid_minimal.json"), body_file)
        assert "--project" in cmd
        assert "WorkmAIn Queue" in cmd

    def test_ac3_4_the_type_flag_is_never_passed(self):
        source = (ROOT / "automation" / "issue_validator.py").read_text()
        assert source.count("--type") == 0

    def test_ac3_5_empty_blocked_by_and_blocking_omit_the_flag(self, tmp_path):
        body_file = tmp_path / "body.md"
        cmd = issue_validator.build_command(fixture("valid_minimal.json"), body_file)
        assert "--blocked-by" not in cmd
        assert "--blocking" not in cmd


class TestSchema:
    def test_new_skeleton_matches_schema_keys(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "automation" / "issue_validator.py"), "--new"],
            capture_output=True,
            text=True,
            check=True,
        )
        skeleton_keys = sorted(json.loads(result.stdout))
        assert skeleton_keys == sorted(SCHEMA)

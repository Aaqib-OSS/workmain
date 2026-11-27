# A check that displays as written — Spec

**Status:** Draft

**Author:** Spanner

**Date:** 20261127

**Read at:** 02a2bee5693be9f015bf0947a48aa9783c14b5c0

**Branch:** `chore/issue-284-check-command-backticks` (base: `main`, `docs/standards/2-git.md` §2.1)

**Target release:** none — a `chore/*` merge leaves the version unchanged (`docs/standards/2-git.md` §2.2)

**Originating item:** Issue #284

**Design study:** `../design/DESIGN_CHECK_COMMAND_BACKTICKS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261127 | Ray | Design study Q1: how the validator judges display | Accepted — GitHub's renderer judges it, through `gh api -X POST /markdown` (Option A). DR1 |
| 20261127 | Ray | Design study Q2: whether "a check's command is written in backticks" is a written rule | Accepted — no rule is written: backticks around a command are standard Markdown practice. The validator judges display only. DR3. AC2 is restated in §5 to drop its reading of §1.2 for how to write a check |
| 20261127 | Ray | Design study Q3: which checks the sweep covers | Accepted — every check that displays altered, and every command outside backticks in a check. Each change is checked against the body before it. Step 3, DR4, AC4.2 |
| 20261127 | Ray | Design study Q4: parked #295 | Accepted — it stays parked. Its checks are swept like any other |
| 20261127 | Ray | Design study Q5: where the sweep's backup is kept | Accepted — no durable backup. GitHub's edit history keeps every earlier body, and the copy step 3 compares against is temporary, in the session scratchpad |
| 20261127 | Spanner | `docs/standards/3-code.md` §3.8: the text of rendered HTML is read with the standard library's `html.parser.HTMLParser` | Accepted — no mechanism is written by hand |

---

## 1. Scope

**In scope:**

- `automation/issue_validator.py`: a rule that refuses a check GitHub would display differently from its source, and the renderer it calls.
- `automation/issue_validator_test.py`, and a new fixture, `automation/fixtures/check_display_rendered.json`.
- `docs/standards/1-workflow.md` §1.2: the criterion-form sentence, whose `<property>` GitHub drops.
- `docs/dev/specs/_TEMPLATE_SPEC.md` §5: the rows AC1.1 and AC1.3, whose placeholders GitHub drops.
- The bodies of open GitHub issues: the checks only, and backticks only.

**Out of scope:**

- **Whether text is a command.** No validator rule judges it, and no standard states it (design study Q2).
- **Every other part of an issue body**, including its context and its criteria. Only checks are swept.
- **Closed issues**, and artifacts in `docs/archive/`.
- **Other placeholders in the templates**, outside `docs/dev/specs/_TEMPLATE_SPEC.md` §5: the header fields and §6 of that file, and `docs/dev/design/_TEMPLATE_DESIGN.md` and `docs/dev/results/_TEMPLATE_RESULTS.md`. Issue #284 names only §1.2 and the template §5. Reported as an existing defect.
- **`automation/fixtures/*.json` checks.** Tests not about display use `render_as_written`, so these fixtures are judged by no renderer.
- **#295's own finding.** It stays parked (Q4).

## 2. Verified current state

Direct path: each step quotes the text it replaces (`docs/standards/1-workflow.md` §1.2). Two facts the steps rely on are stated here, because no single step's quote shows them.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `validate_issue` gains a parameter, `render`, so every caller is listed. `git grep -n "validate_issue(" -- . ':!docs/archive'` returns two call sites, each confirmed a call of `issue_validator.validate_issue`. `git grep -n -E "getattr.*validate_issue\|validate_issue[^(_]"` returns none. | `automation/issue_validator.py` `main`; `automation/issue_validator_test.py` `run_validate` |
| Two tests run `main`, which will now call `gh_render_markdown`. Each patches the other `gh_*` functions, and each is updated in step 1 to patch this one too. | `automation/issue_validator_test.py` `TestStructuredCriteria.test_structured_refusal_stops_the_create_path_before_gh_runs`, `TestAC3.test_ac3_1_default_run_creates_nothing` |

## 3. Design rules

- **DR1 —** GitHub's renderer judges display. The validator holds no model of GitHub-flavoured Markdown. It compares the text GitHub displays with the check's source with backticks removed, whitespace collapsed on both sides.
- **DR2 —** A check is rendered as the line `render_body` writes for it. Both build that line from `CHECK_LABEL`, so the line judged is the line the issue carries.
- **DR3 —** Nothing in this work judges whether text is a command: not the validator, not a standard. The sweep's reading of which text is a command is done once, by the rule in step 3, and recorded for Ray.
- **DR4 —** The sweep changes nothing in a body but backticks. A body is written only after its new text passes both checks in step 3 (the AC4.1 compare and the AC3.1 render), and only if the live body still equals the snapshot.
- **DR5 —** No test reaches the network. Display tests use GitHub's HTML recorded in `automation/fixtures/check_display_rendered.json`. Every other test uses `render_as_written`, which displays every line as written.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The validator refuses a check that GitHub would display differently from its source | `automation/issue_validator.py`, `automation/issue_validator_test.py`, `automation/fixtures/check_display_rendered.json` |
| 2 | §1.2 and the template §5 display as written | `docs/standards/1-workflow.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 3 | Every open issue's checks display as written, with every command in backticks | open issue bodies on GitHub; `docs/dev/results/CHECK_COMMAND_BACKTICKS_RESULTS.md` (created) |
| 4 | The results artifact records every criterion | `docs/dev/results/CHECK_COMMAND_BACKTICKS_RESULTS.md` |

### Step 1 — the validator judges display

Owner: `automation/issue_validator.py` owns the rules on an issue file the schema cannot express (its module docstring). `docs/ARCHITECTURE.md` names no owner for `automation/`, which is non-application tooling (`docs/standards/7-file-placement.md` §7).

The contract:

- `validate_check_display(data: dict, render: Callable[[str], str]) -> list[str]` is new, and public.
- `gh_render_markdown(text: str) -> str` is new, and public.
- `CHECK_LABEL` is a new module constant, and `render_body` builds its check line from it.
- `validate_issue` gains `render: Callable[[str], str]` as its last parameter, runs `validate_check_display` after `validate_criterion_rule`, and is annotated in full.
- `main` passes `gh_render_markdown`.

`_TextCollector` and `_displayed_text` are private.

The exact edit to `automation/issue_validator.py`:

```diff
diff --git a/automation/issue_validator.py b/automation/issue_validator.py
index 7dbdabf..3443dc5 100644
--- a/automation/issue_validator.py
+++ b/automation/issue_validator.py
@@ -1,11 +1,13 @@
 """
-Validate a WorkmAIn issue JSON file against the schema and against live
-GitHub state, then create the issue through `gh issue create`.
+Validates a WorkmAIn issue file, then creates the issue through `gh issue create`.
+
+The file is checked against the schema and against live GitHub state.
 
 The schema (`.github/ISSUE_TEMPLATE/issue.schema.json`) declares the key set
 and each key's type and required-ness. This script owns the rules the schema
 file cannot express: the §1.3 label-pair rule, the §1.2 rule that a criterion
-is not only a command, and existence checks against live GitHub state (labels,
-milestones, referenced issues).
+is not only a command, that each check displays on GitHub as written, and
+existence checks against live GitHub state (labels, milestones, referenced
+issues).
 
 Why this exists: GitHub carries no type-vs-area marking on a label
@@ -22,4 +24,6 @@ import subprocess
 import sys
 import tempfile
+from collections.abc import Callable
+from html.parser import HTMLParser
 from pathlib import Path
 
@@ -29,4 +33,5 @@ STANDARDS_RELATIVE_PATH = Path("docs/standards/1-workflow.md")
 LABEL_PAIR_PHRASE = "label pair"
 PROJECT_NAME = "WorkmAIn Queue"
+CHECK_LABEL = "Checked by:"
 
 
@@ -228,4 +233,60 @@ def validate_criterion_rule(data: dict) -> list:
 
 
+class _TextCollector(HTMLParser):
+    """Collects the text of an HTML fragment, with its entities decoded."""
+
+    def __init__(self) -> None:
+        super().__init__()
+        self.parts: list[str] = []
+
+    def handle_data(self, data: str) -> None:
+        self.parts.append(data)
+
+
+def _displayed_text(rendered_html: str) -> str:
+    collector = _TextCollector()
+    collector.feed(rendered_html)
+    collector.close()
+    return " ".join("".join(collector.parts).split())
+
+
+def validate_check_display(data: dict, render: Callable[[str], str]) -> list[str]:
+    """
+    Refuse a check that GitHub would display differently from its source.
+
+    Each check is rendered as the line `render_body` writes for it, and the
+    text GitHub displays is compared with the check with its backticks
+    removed, whitespace collapsed on both sides. GitHub's own renderer
+    judges, so an escape, a `<placeholder>` or an emphasis marker the body
+    would lose is refused, and prose that displays as written is accepted.
+    Shape errors are the schema's to report; an entry without a non-empty
+    string check is skipped here.
+
+    Args:
+        data: The issue data, after schema normalization.
+        render: Takes one Markdown line and returns the HTML GitHub renders
+            for it. `gh_render_markdown` in production.
+
+    Returns:
+        One error per check that displays differently, naming its index and
+        what GitHub displays.
+    """
+    errors = []
+    for i, ac in enumerate(data.get("acs") or []):
+        if not isinstance(ac, dict):
+            continue
+        check = ac.get("check")
+        if not isinstance(check, str) or not check.strip():
+            continue
+        written = " ".join(check.replace("`", "").split())
+        displayed = _displayed_text(render(f"  - {CHECK_LABEL} {check.strip()}"))
+        displayed = displayed.removeprefix(CHECK_LABEL).strip()
+        if displayed != written:
+            errors.append(
+                f"acs[{i}].check displays on GitHub as {displayed!r}, not as written — put its command in backticks"
+            )
+    return errors
+
+
 def _check_open_issue(field: str, number: int, get_issue_state) -> list:
     state = get_issue_state(number)
@@ -264,5 +325,5 @@ def render_body(context: str, acs: list) -> str:
     for ac in acs:
         lines.append(f"- {ac['criterion'].strip()}")
-        lines.append(f"  - Checked by: {ac['check'].strip()}")
+        lines.append(f"  - {CHECK_LABEL} {ac['check'].strip()}")
     return "\n".join(lines) + "\n"
 
@@ -304,4 +365,26 @@ def gh_issue_state(number: int):
 
 
+def gh_render_markdown(text: str) -> str:
+    """
+    Render Markdown through GitHub's API, as GitHub displays an issue body.
+
+    Args:
+        text: The Markdown to render.
+
+    Returns:
+        The HTML GitHub returns for it.
+
+    Raises:
+        subprocess.CalledProcessError: `gh api` failed.
+    """
+    result = subprocess.run(
+        ["gh", "api", "-X", "POST", "/markdown", "-f", "mode=gfm", "-f", f"text={text}"],
+        capture_output=True,
+        text=True,
+        check=True,
+    )
+    return result.stdout
+
+
 def gh_live_labels() -> set:
     result = subprocess.run(
@@ -324,9 +407,32 @@ def gh_live_milestones() -> set:
 
 
-def validate_issue(data: dict, schema: dict, label_pair: list, live_labels: set, live_milestones: set, get_issue_state):
-    """Run every check and return (errors, normalized_data). Total reporting — DR4."""
+def validate_issue(
+    data: dict,
+    schema: dict,
+    label_pair: list,
+    live_labels: set,
+    live_milestones: set,
+    get_issue_state: Callable[[int], str | None],
+    render: Callable[[str], str],
+) -> tuple[list[str], dict]:
+    """
+    Run every check on an issue's data, and report every error found.
+
+    Args:
+        data: The issue data as read from its file.
+        schema: The key specs `load_schema` returns.
+        label_pair: The §1.3 label pair `parse_label_pair` returns.
+        live_labels: The labels that exist on GitHub.
+        live_milestones: The milestones that exist on GitHub.
+        get_issue_state: Takes an issue number and returns its state, or None if it does not exist.
+        render: Takes one Markdown line and returns the HTML GitHub renders for it.
+
+    Returns:
+        Every error found, and the data normalized by the schema.
+    """
     errors, normalized = validate_schema(data, schema)
     errors += validate_label_pair_rule(normalized, label_pair)
     errors += validate_criterion_rule(normalized)
+    errors += validate_check_display(normalized, render)
     errors += validate_live_state(normalized, live_labels, live_milestones, get_issue_state)
     return errors, normalized
@@ -373,5 +479,5 @@ def main(argv=None) -> int:
 
     errors, normalized = validate_issue(
-        data, schema, label_pair, live_labels, live_milestones, gh_issue_state
+        data, schema, label_pair, live_labels, live_milestones, gh_issue_state, gh_render_markdown
     )
 
```

The exact edit to `automation/issue_validator_test.py`. `run_validate` takes `render`, defaulting to `render_as_written`, so every existing test runs as before (DR5). The two tests that run `main` patch `gh_render_markdown`. `TestCheckDisplay` is new.

```diff
diff --git a/automation/issue_validator_test.py b/automation/issue_validator_test.py
index 8eab037..2aa8244 100644
--- a/automation/issue_validator_test.py
+++ b/automation/issue_validator_test.py
@@ -1,8 +1,10 @@
 """Tests for automation/issue_validator.py, named for the AC they cover (§6, AC4.1)."""
 
+import html
 import importlib.util
 import json
 import subprocess
 import sys
+from collections.abc import Callable
 from pathlib import Path
 
@@ -42,8 +44,28 @@ def fake_issue_state(open_numbers=(), closed_numbers=()):
 
 
-def run_validate(data, label_pair=LABEL_PAIR, live_labels=LIVE_LABELS, live_milestones=LIVE_MILESTONES, get_issue_state=None):
+def render_as_written(text: str) -> str:
+    """A renderer that displays every line as written, so a test not about display is unaffected by it."""
+    return f"<ul>\n<li>{html.escape(text.removeprefix('  - ').replace('`', ''))}</li>\n</ul>"
+
+
+RENDERED = json.loads((FIXTURES / "check_display_rendered.json").read_text())
+
+
+def render_recorded(text: str) -> str:
+    """GitHub's HTML for each line in check_display_rendered.json, recorded from `gh api -X POST /markdown`."""
+    return RENDERED[text.removeprefix("  ")]
+
+
+def run_validate(
+    data: dict,
+    label_pair: list = LABEL_PAIR,
+    live_labels: set = LIVE_LABELS,
+    live_milestones: set = LIVE_MILESTONES,
+    get_issue_state: Callable[[int], str | None] | None = None,
+    render: Callable[[str], str] = render_as_written,
+) -> tuple[list[str], dict]:
     if get_issue_state is None:
         get_issue_state = fake_issue_state(open_numbers=(100, 101, 102))
-    return issue_validator.validate_issue(data, SCHEMA, label_pair, live_labels, live_milestones, get_issue_state)
+    return issue_validator.validate_issue(data, SCHEMA, label_pair, live_labels, live_milestones, get_issue_state, render)
 
 
@@ -269,4 +291,5 @@ class TestStructuredCriteria:
         monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
         monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
+        monkeypatch.setattr(issue_validator, "gh_render_markdown", render_as_written)
         monkeypatch.setattr(
             subprocess,
@@ -290,4 +313,89 @@ class TestStructuredCriteria:
 
 
+ALTERING_FORMS = [
+    pytest.param(
+        'grep -nE "config\\.get\\(" workmain/ai/providers/ returning zero hits',
+        '`grep -nE "config\\.get\\(" workmain/ai/providers/` returning zero hits',
+        id="backslash-before-punctuation",
+    ),
+    pytest.param(
+        "python3 automation/session_param_check.py <service module> printing nothing",
+        "`python3 automation/session_param_check.py <service module>` printing nothing",
+        id="placeholder",
+    ),
+    pytest.param(
+        "grep -rn __repr__ workmain/ returning zero hits",
+        "`grep -rn __repr__ workmain/` returning zero hits",
+        id="double-underscore-name",
+    ),
+]
+
+
+def with_check(check: str) -> dict:
+    data = fixture("valid_minimal.json")
+    data["acs"][0]["check"] = check
+    return data
+
+
+class TestCheckDisplay:
+    """A check displays on GitHub as written, judged by GitHub's renderer."""
+
+    @pytest.mark.parametrize("unquoted, quoted", ALTERING_FORMS)
+    def test_check_display_a_form_that_alters_display_is_refused(self, unquoted: str, quoted: str) -> None:
+        errors, _ = run_validate(with_check(unquoted), render=render_recorded)
+        assert len(errors) == 1
+        assert errors[0].startswith("acs[0].check displays on GitHub as ")
+
+    @pytest.mark.parametrize("unquoted, quoted", ALTERING_FORMS)
+    def test_check_display_the_same_check_in_backticks_is_accepted(self, unquoted: str, quoted: str) -> None:
+        errors, _ = run_validate(with_check(quoted), render=render_recorded)
+        assert errors == []
+
+    def test_check_display_prose_that_displays_as_written_is_accepted(self) -> None:
+        check = "a stated reading by Ray of docs/standards/1-workflow.md §1.2 for whether a check displays as written"
+        errors, _ = run_validate(with_check(check), render=render_recorded)
+        assert errors == []
+
+    def test_check_display_renders_the_line_render_body_writes(self) -> None:
+        seen = []
+
+        def spy(text: str) -> str:
+            seen.append(text)
+            return render_as_written(text)
+
+        data = with_check("`pytest automation/` reporting 0 failed")
+        run_validate(data, render=spy)
+        rendered_body = issue_validator.render_body(data["context"], data["acs"])
+        assert seen == ["  - Checked by: `pytest automation/` reporting 0 failed"]
+        assert seen[0] in rendered_body.splitlines()
+
+    def test_check_display_refusal_stops_the_create_path_before_gh_issue_create_runs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
+        issue_file = tmp_path / "issue.json"
+        issue_file.write_text(json.dumps(with_check(ALTERING_FORMS[1].values[0])))
+
+        monkeypatch.setattr(issue_validator, "gh_live_labels", lambda: LIVE_LABELS)
+        monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
+        monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
+        monkeypatch.setattr(issue_validator, "gh_render_markdown", render_recorded)
+        monkeypatch.setattr(
+            subprocess,
+            "run",
+            lambda *a, **k: pytest.fail("gh issue create must not run for a refused issue"),
+        )
+
+        assert issue_validator.main([str(issue_file), "--create"]) == 1
+
+    def test_check_display_gh_render_markdown_sends_the_text_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
+        calls = []
+
+        def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
+            calls.append(cmd)
+            return subprocess.CompletedProcess(cmd, 0, stdout="<p>x</p>", stderr="")
+
+        monkeypatch.setattr(subprocess, "run", fake_run)
+        assert issue_validator.gh_render_markdown("a `b` <c>") == "<p>x</p>"
+        assert calls == [["gh", "api", "-X", "POST", "/markdown", "-f", "mode=gfm", "-f", "text=a `b` <c>"]]
+
+
 class TestAC3:
     def test_ac3_1_default_run_creates_nothing(self, tmp_path, monkeypatch, capsys):
@@ -298,4 +406,5 @@ class TestAC3:
         monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
         monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
+        monkeypatch.setattr(issue_validator, "gh_render_markdown", render_as_written)
         monkeypatch.setattr(
             subprocess,
```

`automation/fixtures/check_display_rendered.json` is new. Each value is GitHub's response to `gh api -X POST /markdown -f mode=gfm -f text=<key>`, recorded 20261127:

```json
{
  "- Checked by: grep -nE \"config\\.get\\(\" workmain/ai/providers/ returning zero hits": "<ul>\n<li>Checked by: grep -nE \"config.get(\" workmain/ai/providers/ returning zero hits</li>\n</ul>",
  "- Checked by: `grep -nE \"config\\.get\\(\" workmain/ai/providers/` returning zero hits": "<ul>\n<li>Checked by: <code class=\"notranslate\">grep -nE \"config\\.get\\(\" workmain/ai/providers/</code> returning zero hits</li>\n</ul>",
  "- Checked by: python3 automation/session_param_check.py <service module> printing nothing": "<ul>\n<li>Checked by: python3 automation/session_param_check.py  printing nothing</li>\n</ul>",
  "- Checked by: `python3 automation/session_param_check.py <service module>` printing nothing": "<ul>\n<li>Checked by: <code class=\"notranslate\">python3 automation/session_param_check.py &lt;service module&gt;</code> printing nothing</li>\n</ul>",
  "- Checked by: grep -rn __repr__ workmain/ returning zero hits": "<ul>\n<li>Checked by: grep -rn <strong>repr</strong> workmain/ returning zero hits</li>\n</ul>",
  "- Checked by: `grep -rn __repr__ workmain/` returning zero hits": "<ul>\n<li>Checked by: <code class=\"notranslate\">grep -rn __repr__ workmain/</code> returning zero hits</li>\n</ul>",
  "- Checked by: a stated reading by Ray of docs/standards/1-workflow.md §1.2 for whether a check displays as written": "<ul>\n<li>Checked by: a stated reading by Ray of docs/standards/1-workflow.md §1.2 for whether a check displays as written</li>\n</ul>"
}
```

The suite after the step: `pytest automation/` 152 passed, 0 failed, 0 skipped (§6).

### Step 2 — §1.2 and the template §5 display as written

In `docs/standards/1-workflow.md` §1.2, the bullet "A criterion names a property of the delivered system":

- Replace: ``Write it as "*<property>*, checked by `<command>`".``
- With: ``Write it as "`<property>`, checked by `<command>`".``

In `docs/dev/specs/_TEMPLATE_SPEC.md` §5, replace these two rows:

```text
| AC1.1 | <property of the delivered system> | `pytest tests/test_x.py` passes, with a test showing <behaviour> |
| AC1.3 | <property of a document> | Ray reads <section> for <what> |
```

With:

```text
| AC1.1 | `<property of the delivered system>` | `pytest tests/test_x.py` passes, with a test showing `<behaviour>` |
| AC1.3 | `<property of a document>` | Ray reads `<section>` for `<what>` |
```

No rule changes, so the §1.5 search for other statements of a changed rule does not apply.

### Step 3 — the sweep

The sweep's scripts live in the session scratchpad, and nothing it runs is committed. It is run from the repository root.

1. **Snapshot.** `gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --json number,title,body` is written to the scratchpad. Its number of entries must equal `gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --json number --jq length`, and no body may be empty. Otherwise the sweep stops.
2. **Measure the set.** Every check in every body is read, in both forms: the `Checked by:` child bullet, and the inline "— checked by …" / "check is …" inside a criterion bullet. A check is in the set when either holds:
   - its text, rendered through `gh_render_markdown`, differs from its source with backticks removed (the AC3.1 compare)
   - it holds a command outside backticks, by the reading rule below
3. **Edit.** For each issue in the set, its new body is written to a scratchpad file. In each check in the set, backticks are added and nothing else changes. The reading rule:
   - A command runs from its first word to its last argument, and is wrapped in one span. The phrase stating the result, such as "returning no hits", "printing nothing" or "passing", stays outside it.
   - A check that holds more than one command gets one span for each.
   - Other text in a check that displays altered gets a span of its own, around that token alone. #295's `providers.<name>.<key>` is the known case.
   - A tool's name used as a noun in prose ("a grep of both repositories") stays as it is. A runnable command line, such as "pytest passes" written alone, is wrapped.
4. **Check before writing.** For every edited body, before the first write, both must hold:
   - with every backtick removed, it equals its snapshot body with every backtick removed (AC4.1)
   - every check in it renders as its source with backticks removed (AC3.1)

   Any failure stops the sweep before its first write.
5. **Write.** For each edited issue: the live body is read and compared with the snapshot. If it changed, that issue is measured and edited again from the live body. Then `gh issue edit <N> --body-file <file>` is run, with its stderr read in the same command, and the body is read back and compared with the file. A trailing newline added by `--jq` output is ignored.
6. **Record.** `docs/dev/results/CHECK_COMMAND_BACKTICKS_RESULTS.md` is created from its template, with a table of edited issues: issue, each check as it was and as it now is, and the result of the AC4.1 compare. It is the step's commit.

### Step 4 — the results artifact

The results artifact records every criterion in §5 against the delivered branch and the live issues. It records the AC3.1 render compare over every open issue at that time, and Ray's AC4.2 reading as `Not met`, `Awaiting Ray` (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None. `docs/standards/1-workflow.md` §1.4 lists none of the actions this spec takes. Step 3 edits issue bodies, which is outward-facing, so Ray's approval of this spec is his approval of step 3 as written, and DR4 holds each write to it.

## 5. Acceptance criteria

The issue body needs two edits at close-out (`docs/standards/1-workflow.md` §1.2):

- **AC2:** drop its first check, the reading of §1.2 for how to write a check (design study Q2).
- **AC4:** add the criterion of AC4.2 (Q3).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | An issue whose check would display on GitHub differently from its source is refused before `gh issue create` runs, for each form found altering display, and the same check with its command in backticks is accepted | `pytest automation/issue_validator_test.py` passes, including `TestCheckDisplay`'s refused and accepted cases for `backslash-before-punctuation`, `placeholder` and `double-underscore-name`, and `test_check_display_refusal_stops_the_create_path_before_gh_issue_create_runs` |
| AC1.2 | Through its only entry path, `python3 automation/issue_validator.py <file>`, with GitHub's live renderer, the validator refuses a check that displays altered and accepts it in backticks | `python3 automation/issue_validator.py` run on a copy of `automation/fixtures/valid_minimal.json` whose check is `git -C <live tree> rev-parse HEAD equals git rev-parse dev` exits 1 and prints an `acs[0].check displays on GitHub as` line. The same file with `` `git -C <live tree> rev-parse HEAD` `` prints no such line. Recorded in the results artifact |
| AC2.1 | `docs/standards/1-workflow.md` §1.2 and `docs/dev/specs/_TEMPLATE_SPEC.md` §5 display on GitHub as written. Restated from issue AC2 (design study Q2) | Each section rendered through `gh api -X POST /markdown -f mode=gfm` and compared line by line, and cell by cell, with its source with backticks removed, showing no difference. Recorded in the results artifact |
| AC3.1 | Every check in every open issue displays on GitHub as its source states, in both forms | Every open issue's body rendered through `gh api -X POST /markdown -f mode=gfm` and compared check by check with its source with backticks removed, showing no difference. Recorded in the results artifact |
| AC4.1 | The sweep changed nothing in any issue body but backticks | For each edited issue, its snapshot body and its body after, each with every backtick removed, compared showing no difference. Recorded in the results artifact's table of edited issues |
| AC4.2 | Every command in an open issue's check is in backticks. Added from design study Q3 | A stated reading by Ray of the results artifact's table of edited issues, for whether each command, and only the command, is in backticks |
| AC5.1 | The automation suite passes | `pytest automation/` reporting 152 passed, 0 failed, 0 skipped |

## 6. Test plan

Counts are in the form `docs/standards/6-testing.md` §6 states.

- **Baseline before this work**, at the **Read at:** commit:
  - bare `pytest`: 1862 passed, 0 failed, 0 skipped, with 1 xfailed and 3 xpassed
  - `pytest automation/`: 142 passed, 0 failed, 0 skipped
- **Expected after:**
  - bare `pytest`: unchanged, since no file under `tests/` or `workmain/` changes
  - `pytest automation/`: 152 passed, 0 failed, 0 skipped
- **Test files:** `automation/issue_validator_test.py` `TestCheckDisplay` adds 10 tests: 3 refused and 3 accepted parametrized cases, and 4 single tests. They cover prose accepted, the line `render_body` writes, the create path stopping, and the argv `gh_render_markdown` sends. `render_as_written` keeps every existing test independent of display (DR5).

## 7. Risks and rollback

- **GitHub changes its renderer.** The recorded fixture then no longer matches live rendering. The tests still pass on the recording, and the live validator follows GitHub, which is DR1's point. AC1.2 is the live check at delivery.
- **The validator makes one API call per check.** A run against an issue with five criteria makes five calls, well inside GitHub's authenticated rate limit. Without the network the validator already fails at `gh_live_labels`, so no new failure mode is added.
- **A sweep edit is wrong.** DR4's checks run before any write. A wrong edit that passes them adds backticks in the wrong place, which AC4.2's reading catches. Any body is restored from GitHub's edit history, or from the snapshot while the session lasts, with `gh issue edit <N> --body-file`.
- **Rollback:** steps 1, 2 and 4 are each a commit, reverted with `git revert`. Step 3's issue edits are reverted body by body, as above.

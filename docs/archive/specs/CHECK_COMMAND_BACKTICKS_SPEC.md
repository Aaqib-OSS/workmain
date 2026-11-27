# A check that displays as written — Spec

**Status:** Shipped

**Author:** Spanner

**Date:** 20261127

**Read at:** 24dedd4a5dfe539f8066d5ba5da6f14a69d69ddc

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
| 20261127 | Ray | Fix every placeholder outside backticks in the three `docs/dev/` templates, not only the template §5 rows issue #284 names | Accepted — step 2 and AC2.1 cover all three templates. AC2 is restated in §5 to name them |
| 20261127 | Spanner | `docs/standards/3-code.md` §3.8: the text of rendered HTML is read with the standard library's `html.parser.HTMLParser` | Accepted — no mechanism is written by hand |
| 20261127 | Caliper | 1, Spec defect, blocking: DR4 and step 3.5 contradict each other. DR4 writes a body "only if the live body still equals the snapshot". Step 3.5 says that when the live body has changed, the issue "is measured and edited again from the live body", and then written. That re-edited body never goes through step 3.4's checks, which run "before the first write". It also fails AC4.1 by construction, because AC4.1 compares the body after against the *snapshot* body. The implementer has to choose between skipping and reporting the issue, or re-running 3.4 and comparing AC4.1 against the live body read just before the write. | Accepted — each issue's before-body is now the live body read just before its write. Step 3.5's checks run against it for every write, re-run when the body differs from the snapshot, and AC4.1 compares against it. DR4, steps 3.5 and 3.6, AC4.1 |
| 20261127 | Caliper | 2, Spec defect, blocking: the implementer can't identify the set of checks that step 3.2 and AC3.1 cover without guessing. In today's 135 open bodies, the markers "— checked by" and "check is" match 49 lines. These include context paragraphs that are not criteria (#284, #277, #240, #194). The spec says "inside a criterion bullet" but never says how to recognise a criterion bullet: 12 bodies have no AC section and 44 have checkbox criteria. It also doesn't say where an inline check ends. #176's "checked by a bare `pytest` reporting 0 failed and by Ray running…" holds two checks. Whether the sweep keeps to §1's "Only checks are swept" depends on this rule. The spec also doesn't carry the design study's measured population (F3: 273 + 42 checks), so a check list the implementer extracts can't be compared with it. AC3.1 renders the whole body and compares "check by check", but nothing says how rendered HTML is matched to a check. | Accepted — step 3.2 states the extraction rule: criteria sections, both forms, where an inline check starts and ends, and that a bullet with two markers is one check. It carries the population the rule finds at the **Read at:** commit: 273 checks in 58 issues, 83 in 20. AC3.1 runs `validate_check_display` over each issue's checks, so its matching is the shipped rule's: one list item per check, in order |
| 20261127 | Caliper | 1 (§1.2: a check can produce the answer the criterion states), Spec defect, blocking: AC1.2's check can't show "accepts it in backticks". It uses a copy of `automation/fixtures/valid_minimal.json`, whose label `cli` doesn't exist on GitHub. I applied step 1 at `24dedd4` and ran both files live without `--create`. Both exited 1 and printed `label does not exist: cli`. The refused file also printed the `acs[0].check displays on GitHub as` line. "Prints no such line" holds; "accepts" can't. | Accepted — AC1.2's copy sets `labels` to `["gap", "process"]`, which exist. Run live on the revised step 1, the refused file exits 1 with the display error, and the backticked file exits 0 and prints its `gh issue create` command |
| 20261127 | Caliper | 2, Spec defect, non-blocking: §1's count "Ten such lines lose a placeholder… Five keep" doesn't match the render. I rendered the 15 lines step 2 lists through `gh api -X POST /markdown -f mode=gfm`, alone and in their whole files. 9 lose a placeholder: the spec template's Decision Log `<why>` row, AC1.1, AC1.3, Baseline and Expected; the design template's Read at and Option XX; and the results template's AC1.2 and Test suite. 6 keep theirs: the three `# <Title>` headings, which render as `&lt;Title&gt;`, plus the spec template's Read at, Recommendation and Superseded by. Step 2 lists every line, so the build isn't affected. | Accepted — §1 reads 9 and 6. Recommendation and Superseded by are in the design template, not the spec template |
| 20261127 | Caliper | 4 (§1.2: a contract change enumerates its call sites), Spec defect, non-blocking: §2 row 1's searches don't give the stated results. `git grep -n "validate_issue("` also returns the `def` line. At `HEAD` it returns the spec's own diff lines too. The getattr search has no pathspec, so it returns hits in `docs/archive/` and the design study, not "none". It returns none with `-- '*.py'`. The conclusion holds: the only callers are `main` and `run_validate`. | Accepted — both searches take `-- '*.py'`, and the row states what each returns |
| 20261127 | Caliper | Pass at 24dedd4, full: 18 items checked, 3 blocking, 2 non-blocking. | n/a |
| 20261127 | Caliper | 2, Spec defect, non-blocking: when an issue's checks render as a different number of list items, `validate_check_display` returns one issue-level error (`acs: N checks display on GitHub as M list items`) that names no check. Step 3.3 puts a check in the set when the validator "reports it", so that error puts no check in the set, and step 3.6.1 doesn't say what happens next. None of the 78 open issues produces it today (run live at `d6ad044`). In step 3.5 it is an error, so it stops the sweep. Suggested fix: state that a count error stops the sweep at that issue. | Accepted — step 3.3 states that the count error stops the sweep at that issue, which is reported to Ray |
| 20261127 | Caliper | 2, Spec defect, non-blocking: step 3.7 spaces renders "at least one second apart" for step 3 only. Step 4's AC3.1 run makes the same 78 `gh_render_markdown` calls and nothing spaces them. Step 3.7's "resumes there once the limit has cleared" also covers only a rate-limit error. Any other `gh` error has no resume rule. | Accepted — step 3.7 covers step 4's AC3.1 run, and step 4 cites it. After any error other than a rate limit, the run resumes only on Ray's word |
| 20261127 | Caliper | Pass at d6ad044, changes since 24dedd4: 20 items checked, 0 blocking, 2 non-blocking. | n/a |
| 20261127 | Spanner | Finding 2's measurement showed that one render call per check trips GitHub's secondary rate limit at sweep scale: 356 checks, refused with HTTP 403 partway through. | Accepted — `validate_check_display` renders all of an issue's checks in one call, one list item per check, so the sweep makes one call per issue: 78 calls, run one at a time, with no limit reached. DR2, step 1 |
| 20261127 | Spanner | Step 2 stopped before any write: its §1.2 replacement drops the italics around `<property>`, so the line changes by more than the backticks the step's opening sentence allows | Ray, 20261127: apply the replacement as quoted. The backticks do the work the italics did, setting the placeholder apart from prose, so the line keeps its meaning |
| 20261127 | Caliper (post-implementation) | No findings. | n/a |

---

## 1. Scope

**In scope:**

- `automation/issue_validator.py`: a rule that refuses a check GitHub would display differently from its source, and the renderer it calls.
- `automation/issue_validator_test.py`, and a new fixture, `automation/fixtures/check_display_rendered.json`.
- `docs/standards/1-workflow.md` §1.2: the criterion-form sentence, whose `<property>` GitHub drops.
- Every placeholder written outside backticks in `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/design/_TEMPLATE_DESIGN.md` and `docs/dev/results/_TEMPLATE_RESULTS.md`. Nine such lines lose a placeholder on GitHub. Six keep theirs only because of their wording: `<commit SHA §2 was verified at>` survives, while `<commit SHA the read was taken at>` is dropped.
- The bodies of open GitHub issues: the checks only, and backticks only.

**Out of scope:**

- **Whether text is a command.** No validator rule judges it, and no standard states it (design study Q2).
- **Every other part of an issue body**, including its context and its criteria. Only checks are swept.
- **Closed issues**, and artifacts in `docs/archive/`.
- **The design template's `Promoted to:` line.** Its placeholder wraps code spans in angle brackets: ``<`../specs/<file>_SPEC.md`, …, or issue #N>``. GitHub escapes the brackets and displays the line as written, and a code span cannot hold it without nesting.
- **Placeholders already in backticks**, such as `config/providers/_template/models/README.md`'s `models/<model>/`, and every placeholder inside a fenced block.
- **`automation/fixtures/*.json` checks.** Tests not about display use `render_as_written`, so these fixtures are judged by no renderer.
- **#295's own finding.** It stays parked (Q4).

## 2. Verified current state

Direct path: each step quotes the text it replaces (`docs/standards/1-workflow.md` §1.2). Two facts the steps rely on are stated here, because no single step's quote shows them.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `validate_issue` gains a parameter, `render`, so every caller is listed. `git grep -n "validate_issue(" -- '*.py'` returns its `def` and two call sites, each confirmed a call of `issue_validator.validate_issue`. `git grep -n -E "getattr.*validate_issue\|validate_issue[^(_]" -- '*.py'` returns nothing, so no reference by name exists. | `automation/issue_validator.py` `main`; `automation/issue_validator_test.py` `run_validate` |
| Two tests run `main`, which will now call `gh_render_markdown`. Each patches the other `gh_*` functions, and each is updated in step 1 to patch this one too. | `automation/issue_validator_test.py` `TestStructuredCriteria.test_structured_refusal_stops_the_create_path_before_gh_runs`, `TestAC3.test_ac3_1_default_run_creates_nothing` |

## 3. Design rules

- **DR1 —** GitHub's renderer judges display. The validator holds no model of GitHub-flavoured Markdown. It compares the text GitHub displays with the check's source with backticks removed, whitespace collapsed on both sides.
- **DR2 —** An issue's checks are rendered together, in one call, as the lines `render_body` writes for them, and each list item GitHub returns is matched to its check by position. Both build that line from `CHECK_LABEL`, so the line judged is the line the issue carries. A check whose text changes the number of list items is refused.
- **DR3 —** Nothing in this work judges whether text is a command: not the validator, not a standard. The sweep's reading of which text is a command is done once, by the rule in step 3, and recorded for Ray.
- **DR4 —** The sweep changes nothing in a body but backticks. An issue's before-body is its live body, read just before its write. A body is written only after its new text passes both of step 3.5's checks against that before-body: the AC4.1 compare and the AC3.1 render.
- **DR5 —** No test reaches the network. Display tests use GitHub's HTML recorded in `automation/fixtures/check_display_rendered.json`. Every other test uses `render_as_written`, which displays every line as written.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The validator refuses a check that GitHub would display differently from its source | `automation/issue_validator.py`, `automation/issue_validator_test.py`, `automation/fixtures/check_display_rendered.json` |
| 2 | §1.2 and the three `docs/dev/` templates display as written | `docs/standards/1-workflow.md`, `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/design/_TEMPLATE_DESIGN.md`, `docs/dev/results/_TEMPLATE_RESULTS.md` |
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

`validate_check_display` makes one `render` call per issue, holding every check (DR2). `_ListItemCollector` and `_displayed_items` are private.

The exact edit to `automation/issue_validator.py`:

```diff
diff --git a/automation/issue_validator.py b/automation/issue_validator.py
index 7dbdabf..b160d1c 100644
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
 
 
@@ -228,4 +233,78 @@ def validate_criterion_rule(data: dict) -> list:
 
 
+class _ListItemCollector(HTMLParser):
+    """Collects the text of each list item in an HTML fragment, in order, with its entities decoded."""
+
+    def __init__(self) -> None:
+        super().__init__()
+        self.items: list[list[str]] = []
+        self._open = False
+
+    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
+        if tag == "li":
+            self.items.append([])
+            self._open = True
+
+    def handle_endtag(self, tag: str) -> None:
+        if tag == "li":
+            self._open = False
+
+    def handle_data(self, data: str) -> None:
+        if self._open:
+            self.items[-1].append(data)
+
+
+def _displayed_items(rendered_html: str) -> list[str]:
+    collector = _ListItemCollector()
+    collector.feed(rendered_html)
+    collector.close()
+    return [" ".join("".join(parts).split()) for parts in collector.items]
+
+
+def validate_check_display(data: dict, render: Callable[[str], str]) -> list[str]:
+    """
+    Refuse a check that GitHub would display differently from its source.
+
+    The checks are rendered together, in one call, as the lines
+    `render_body` writes for them, and each list item GitHub displays is
+    compared with its check with the backticks removed, whitespace
+    collapsed on both sides. GitHub's own renderer judges, so an escape, a
+    `<placeholder>` or an emphasis marker the body would lose is refused,
+    and prose that displays as written is accepted. Shape errors are the
+    schema's to report; an entry without a non-empty, single-line string
+    check is skipped here.
+
+    Args:
+        data: The issue data, after schema normalization.
+        render: Takes Markdown and returns the HTML GitHub renders for it.
+            `gh_render_markdown` in production.
+
+    Returns:
+        One error per check that displays differently, naming its index and
+        what GitHub displays.
+    """
+    checks = []
+    for i, ac in enumerate(data.get("acs") or []):
+        if not isinstance(ac, dict):
+            continue
+        check = ac.get("check")
+        if isinstance(check, str) and check.strip() and not _has_line_break(check):
+            checks.append((i, check.strip()))
+    if not checks:
+        return []
+
+    displayed_items = _displayed_items(render("\n".join(f"  - {CHECK_LABEL} {check}" for _, check in checks)))
+    if len(displayed_items) != len(checks):
+        return [f"acs: {len(checks)} checks display on GitHub as {len(displayed_items)} list items"]
+
+    errors = []
+    for (i, check), displayed in zip(checks, displayed_items):
+        written = " ".join(check.replace("`", "").split())
+        shown = displayed.removeprefix(CHECK_LABEL).strip()
+        if shown != written:
+            errors.append(f"acs[{i}].check displays on GitHub as {shown!r}, not as written — put its command in backticks")
+    return errors
+
+
 def _check_open_issue(field: str, number: int, get_issue_state) -> list:
     state = get_issue_state(number)
@@ -264,5 +343,5 @@ def render_body(context: str, acs: list) -> str:
     for ac in acs:
         lines.append(f"- {ac['criterion'].strip()}")
-        lines.append(f"  - Checked by: {ac['check'].strip()}")
+        lines.append(f"  - {CHECK_LABEL} {ac['check'].strip()}")
     return "\n".join(lines) + "\n"
 
@@ -304,4 +383,26 @@ def gh_issue_state(number: int):
 
 
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
@@ -324,9 +425,32 @@ def gh_live_milestones() -> set:
 
 
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
+        render: Takes Markdown and returns the HTML GitHub renders for it.
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
@@ -373,5 +497,5 @@ def main(argv=None) -> int:
 
     errors, normalized = validate_issue(
-        data, schema, label_pair, live_labels, live_milestones, gh_issue_state
+        data, schema, label_pair, live_labels, live_milestones, gh_issue_state, gh_render_markdown
     )
 
```

The exact edit to `automation/issue_validator_test.py`. `run_validate` takes `render`, defaulting to `render_as_written`, so every existing test runs as before (DR5). The two tests that run `main` patch `gh_render_markdown`. `TestCheckDisplay` is new.

```diff
diff --git a/automation/issue_validator_test.py b/automation/issue_validator_test.py
index 8eab037..c77ac61 100644
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
 
@@ -42,8 +44,29 @@ def fake_issue_state(open_numbers=(), closed_numbers=()):
 
 
-def run_validate(data, label_pair=LABEL_PAIR, live_labels=LIVE_LABELS, live_milestones=LIVE_MILESTONES, get_issue_state=None):
+def render_as_written(text: str) -> str:
+    """A renderer that displays every line as written, so a test not about display is unaffected by it."""
+    items = "".join(f"<li>{html.escape(line.removeprefix('  - ').replace('`', ''))}</li>\n" for line in text.splitlines())
+    return f"<ul>\n{items}</ul>"
+
+
+RENDERED = json.loads((FIXTURES / "check_display_rendered.json").read_text())
+
+
+def render_recorded(text: str) -> str:
+    """GitHub's HTML for each input in check_display_rendered.json, recorded from `gh api -X POST /markdown`."""
+    return RENDERED[text]
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
 
 
@@ -269,4 +292,5 @@ class TestStructuredCriteria:
         monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
         monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
+        monkeypatch.setattr(issue_validator, "gh_render_markdown", render_as_written)
         monkeypatch.setattr(
             subprocess,
@@ -290,4 +314,97 @@ class TestStructuredCriteria:
 
 
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
+    def test_check_display_renders_every_check_in_one_call_as_the_lines_render_body_writes(self) -> None:
+        seen = []
+
+        def spy(text: str) -> str:
+            seen.append(text)
+            return render_as_written(text)
+
+        data = with_check("`pytest automation/` reporting 0 failed")
+        data["acs"].append({"criterion": "a second property", "check": "`git status` showing a clean tree"})
+        run_validate(data, render=spy)
+        body_lines = issue_validator.render_body(data["context"], data["acs"]).splitlines()
+        assert len(seen) == 1
+        assert seen[0].splitlines() == [line for line in body_lines if line.startswith("  - Checked by: ")]
+
+    def test_check_display_names_the_index_of_the_check_that_displays_differently(self) -> None:
+        data = with_check("`pytest automation/` reporting 0 failed")
+        data["acs"].append({"criterion": "a second property", "check": ALTERING_FORMS[1].values[0]})
+        errors, _ = run_validate(data, render=render_recorded)
+        assert len(errors) == 1
+        assert errors[0].startswith("acs[1].check displays on GitHub as ")
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
@@ -298,4 +415,5 @@ class TestAC3:
         monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
         monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
+        monkeypatch.setattr(issue_validator, "gh_render_markdown", render_as_written)
         monkeypatch.setattr(
             subprocess,
```

`automation/fixtures/check_display_rendered.json` is new. Each value is GitHub's response to `gh api -X POST /markdown -f mode=gfm -f text=<key>`, recorded 20261127:

```json
{
  "  - Checked by: grep -nE \"config\\.get\\(\" workmain/ai/providers/ returning zero hits": "<ul>\n<li>Checked by: grep -nE \"config.get(\" workmain/ai/providers/ returning zero hits</li>\n</ul>",
  "  - Checked by: `grep -nE \"config\\.get\\(\" workmain/ai/providers/` returning zero hits": "<ul>\n<li>Checked by: <code class=\"notranslate\">grep -nE \"config\\.get\\(\" workmain/ai/providers/</code> returning zero hits</li>\n</ul>",
  "  - Checked by: python3 automation/session_param_check.py <service module> printing nothing": "<ul>\n<li>Checked by: python3 automation/session_param_check.py  printing nothing</li>\n</ul>",
  "  - Checked by: `python3 automation/session_param_check.py <service module>` printing nothing": "<ul>\n<li>Checked by: <code class=\"notranslate\">python3 automation/session_param_check.py &lt;service module&gt;</code> printing nothing</li>\n</ul>",
  "  - Checked by: grep -rn __repr__ workmain/ returning zero hits": "<ul>\n<li>Checked by: grep -rn <strong>repr</strong> workmain/ returning zero hits</li>\n</ul>",
  "  - Checked by: `grep -rn __repr__ workmain/` returning zero hits": "<ul>\n<li>Checked by: <code class=\"notranslate\">grep -rn __repr__ workmain/</code> returning zero hits</li>\n</ul>",
  "  - Checked by: a stated reading by Ray of docs/standards/1-workflow.md §1.2 for whether a check displays as written": "<ul>\n<li>Checked by: a stated reading by Ray of docs/standards/1-workflow.md §1.2 for whether a check displays as written</li>\n</ul>",
  "  - Checked by: `pytest automation/` reporting 0 failed\n  - Checked by: python3 automation/session_param_check.py <service module> printing nothing": "<ul>\n<li>Checked by: <code class=\"notranslate\">pytest automation/</code> reporting 0 failed</li>\n<li>Checked by: python3 automation/session_param_check.py  printing nothing</li>\n</ul>"
}
```

The suite after the step: `pytest automation/` 153 passed, 0 failed, 0 skipped (§6).

### Step 2 — §1.2 and the templates display as written

Each placeholder is wrapped in backticks, and nothing else on its line changes.

In `docs/standards/1-workflow.md` §1.2, the bullet "A criterion names a property of the delivered system":

- Replace: ``Write it as "*<property>*, checked by `<command>`".``
- With: ``Write it as "`<property>`, checked by `<command>`".``

In `docs/dev/specs/_TEMPLATE_SPEC.md`, replace these lines:

```text
# <Title> — Spec
**Read at:** <commit SHA §2 was verified at>
| YYYYMMDD | <one of: Ray, Spanner, Caliper, Caliper (post-implementation), Anvil> | | Accepted / **Not taken** — <why> |
| AC1.1 | <property of the delivered system> | `pytest tests/test_x.py` passes, with a test showing <behaviour> |
| AC1.3 | <property of a document> | Ray reads <section> for <what> |
- **Baseline before this work:** <passed> passed, <failed> failed, <skipped> skipped, from a bare `pytest` at the **Read at:** commit.
- **Expected after:** <passed> passed, <failed> failed, <skipped> skipped.
```

With:

```text
# `<Title>` — Spec
**Read at:** `<commit SHA §2 was verified at>`
| YYYYMMDD | `<one of: Ray, Spanner, Caliper, Caliper (post-implementation), Anvil>` | | Accepted / **Not taken** — `<why>` |
| AC1.1 | `<property of the delivered system>` | `pytest tests/test_x.py` passes, with a test showing `<behaviour>` |
| AC1.3 | `<property of a document>` | Ray reads `<section>` for `<what>` |
- **Baseline before this work:** `<passed>` passed, `<failed>` failed, `<skipped>` skipped, from a bare `pytest` at the **Read at:** commit.
- **Expected after:** `<passed>` passed, `<failed>` failed, `<skipped>` skipped.
```

In `docs/dev/design/_TEMPLATE_DESIGN.md`, replace these lines:

```text
# <Title> — Design Study | Recon
**Read at:** <commit SHA the read was taken at>
### Option XX — <name>
**Recommendation:** <which, and why>, argued from the governing rules above.
- Superseded by: <filename, if applicable>
```

With:

```text
# `<Title>` — Design Study | Recon
**Read at:** `<commit SHA the read was taken at>`
### Option XX — `<name>`
**Recommendation:** `<which, and why>`, argued from the governing rules above.
- Superseded by: `<filename, if applicable>`
```

In `docs/dev/results/_TEMPLATE_RESULTS.md`, replace these lines:

```text
# <Title> — Implementation Results
| AC1.2 | **Not met** | `Awaiting Ray`: <what he reads or runs> |
- **Test suite:** <passed> passed, <failed> failed, <skipped> skipped (baseline: the spec's §6 baseline).
```

With:

```text
# `<Title>` — Implementation Results
| AC1.2 | **Not met** | `Awaiting Ray`: `<what he reads or runs>` |
- **Test suite:** `<passed>` passed, `<failed>` failed, `<skipped>` skipped (baseline: the spec's §6 baseline).
```

No rule changes, so the §1.5 search for other statements of a changed rule does not apply.

### Step 3 — the sweep

The sweep's scripts live in the session scratchpad, and nothing it runs is committed. It is run from the repository root.

1. **Snapshot.** `gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --json number,title,body` is written to the scratchpad. Its number of entries must equal `gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --json number --jq length`, and no body may be empty. Otherwise the sweep stops.
2. **Find the checks.** A check is found only inside a criteria section of a body:
   - **A criteria section** starts at a line whose text, after any heading marker (`#` to `######`), is `**ACs**` or `Acceptance criteria`, in any case. It ends at the next heading line (`#` to `######` followed by a space), a line that is bold text alone (`**…**`), a `---` line, or the end of the body.
   - **The `Checked by:` form:** a line in the section matching `^\s+- Checked by:\s`. The check is the rest of the line.
   - **The inline form:** a bullet in the section, meaning a line starting `-`, `*`, or a number and `.`, then a space, optionally followed by a checkbox (`[ ]`, `[x]` or `[X]`) and a space, together with its indented continuation lines, joined with single spaces. The check runs from just after the first marker in the bullet to the bullet's end. A marker is `checked by` or `check is`, followed by a space, and preceded by either a comma and a space, or a space, an em dash (`—`) and a space. A second marker after the first stays inside that check, so #176's "checked by a bare `pytest` … and by Ray running …" is one check. A bullet with no marker holds no check.
   - **Population at the **Read at:** commit's date:** 273 checks in 58 issues in the `Checked by:` form, and 83 checks in 20 issues in the inline form. 41 of them, in 21 issues, display altered: #158, #159, #169, #205, #207–#216, #219, #230, #255, #256, #295, #298 and #299. The sweep finds them again from its own snapshot, and the results artifact records any difference from these counts.
3. **Measure the set.** A check is in the set when either holds:
   - `validate_check_display`, given the issue's checks as `acs` entries and `gh_render_markdown`, reports it (the AC3.1 compare). An inline check is judged as the line the validator builds, not inside its bullet. Measured on the population above, that judges exactly the 41 checks a render of each whole body finds.
   - it holds a command outside backticks, by the reading rule in 3.4

   An issue for which `validate_check_display` returns its count error (`acs: N checks display on GitHub as M list items`) names no check, so the sweep stops at that issue and reports it to Ray. None of the open issues returns it at the **Read at:** commit.
4. **Edit.** For each issue in the set, its new body is written to a scratchpad file. In each check in the set, backticks are added and nothing else changes. The reading rule:
   - A command runs from its first word to its last argument, and is wrapped in one span. The phrase stating the result, such as "returning no hits", "printing nothing" or "passing", stays outside it.
   - A check that holds more than one command gets one span for each.
   - Other text in a check that displays altered gets a span of its own, around that token alone. #295's `providers.<name>.<key>` is the known case.
   - A tool's name used as a noun in prose ("a grep of both repositories") stays as it is. A runnable command line, such as "pytest passes" written alone, is wrapped.
5. **Check, before any write.** Both checks hold for an edited body against its before-body (DR4):
   - with every backtick removed, the edited body equals the before-body with every backtick removed (AC4.1)
   - `validate_check_display` reports no error for the edited body's checks (AC3.1)

   Every edited body is first checked against its snapshot body. Any failure stops the sweep before its first write.
6. **Write.** For each edited issue, in turn:
   1. Its live body is read. If it differs from the snapshot, that live body becomes the issue's before-body. The issue is found, measured and edited again from it by 3.2 to 3.4, and checked again by 3.5. A failure stops the sweep at that issue.
   2. `gh issue edit <N> --body-file <file>` is run, with its stderr read in the same command.
   3. The body is read back and compared with the file. A trailing newline added by `--jq` output is ignored.
7. **Calls to GitHub.** This holds for every `gh` call in step 3 and in step 4's AC3.1 run. Every render and every edit is made one at a time, at least one second apart, so GitHub's secondary rate limit is not reached. Any `gh` error stops the run at the issue it was on. After a rate-limit error, the run resumes at that issue once the limit has cleared. After any other error, the error is reported to Ray, and the run resumes at that issue only when he says so.
8. **Record.** `docs/dev/results/CHECK_COMMAND_BACKTICKS_RESULTS.md` is created from its template. Its table of edited issues gives each issue, each check as it was and as it now is, whether its before-body was the snapshot or a re-read, and the result of the AC4.1 compare. The file is the step's commit.

### Step 4 — the results artifact

The results artifact records every criterion in §5 against the delivered branch and the live issues. It records the AC3.1 render compare over every open issue at that time, made as step 3.7 states, and Ray's AC4.2 reading as `Not met`, `Awaiting Ray` (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None. `docs/standards/1-workflow.md` §1.4 lists none of the actions this spec takes. Step 3 edits issue bodies, which is outward-facing, so Ray's approval of this spec is his approval of step 3 as written, and DR4 holds each write to it.

## 5. Acceptance criteria

The issue body needs two edits at close-out (`docs/standards/1-workflow.md` §1.2):

- **AC2:** drop its first check, the reading of §1.2 for how to write a check (design study Q2). Name the three `docs/dev/` templates in place of `docs/dev/specs/_TEMPLATE_SPEC.md` §5 (Ray, 20261127).
- **AC4:** add the criterion of AC4.2 (Q3).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | An issue whose check would display on GitHub differently from its source is refused before `gh issue create` runs, for each form found altering display, and the same check with its command in backticks is accepted | `pytest automation/issue_validator_test.py` passes, including `TestCheckDisplay`'s refused and accepted cases for `backslash-before-punctuation`, `placeholder` and `double-underscore-name`, and `test_check_display_refusal_stops_the_create_path_before_gh_issue_create_runs` |
| AC1.2 | Through its only entry path, `python3 automation/issue_validator.py <file>`, with GitHub's live renderer, the validator refuses a check that displays altered and accepts it in backticks | `python3 automation/issue_validator.py`, without `--create`, run on a copy of `automation/fixtures/valid_minimal.json` with `labels` set to `["gap", "process"]` and its check set to `git -C <live tree> rev-parse HEAD equals git rev-parse dev`, exits 1 and prints an `acs[0].check displays on GitHub as` line. The same file with its check set to `` `git -C <live tree> rev-parse HEAD` equals `git rev-parse dev` `` exits 0 and prints its `gh issue create` command. Recorded in the results artifact |
| AC2.1 | `docs/standards/1-workflow.md` §1.2 and the three `docs/dev/` templates display every placeholder on GitHub as written. Restated from issue AC2 (design study Q2; Ray, 20261127) | Each line step 2 changes, rendered through `gh api -X POST /markdown -f mode=gfm`, displays every placeholder it holds. A search of `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/design/_TEMPLATE_DESIGN.md` and `docs/dev/results/_TEMPLATE_RESULTS.md` for a `<…>` placeholder outside a code span or a fenced block finds only the design template's `Promoted to:` line (§1). Both recorded in the results artifact |
| AC3.1 | Every check in every open issue displays on GitHub as its source states, in both forms | For every open issue, the checks step 3.2's rule finds, passed to `validate_check_display` with `gh_render_markdown`, one call per issue, report no error. Recorded in the results artifact with the number of checks found in each form |
| AC4.1 | The sweep changed nothing in any issue body but backticks | For each edited issue, its before-body (DR4) and its body after, each with every backtick removed, compared showing no difference. Recorded in the results artifact's table of edited issues |
| AC4.2 | Every command in an open issue's check is in backticks. Added from design study Q3 | A stated reading by Ray of the results artifact's table of edited issues, for whether each command, and only the command, is in backticks |
| AC5.1 | The automation suite passes | `pytest automation/` reporting 153 passed, 0 failed, 0 skipped |

## 6. Test plan

Counts are in the form `docs/standards/6-testing.md` §6 states.

- **Baseline before this work**, at the **Read at:** commit:
  - bare `pytest`: 1862 passed, 0 failed, 0 skipped, with 1 xfailed and 3 xpassed
  - `pytest automation/`: 142 passed, 0 failed, 0 skipped
- **Expected after:**
  - bare `pytest`: unchanged, since no file under `tests/` or `workmain/` changes
  - `pytest automation/`: 153 passed, 0 failed, 0 skipped
- **Test files:** `automation/issue_validator_test.py` `TestCheckDisplay` adds 11 tests: 3 refused and 3 accepted parametrized cases, and 5 single tests. They cover prose accepted, every check rendered in one call as the lines `render_body` writes, the index of the one check that displays differently, the create path stopping, and the argv `gh_render_markdown` sends. `render_as_written` keeps every existing test independent of display (DR5).

## 7. Risks and rollback

- **GitHub changes its renderer.** The recorded fixture then no longer matches live rendering. The tests still pass on the recording, and the live validator follows GitHub, which is DR1's point. AC1.2 is the live check at delivery.
- **GitHub's rate limits.** The validator makes one render call per issue (DR2). The sweep makes about 78, one at a time, and stops on a `gh` error rather than retrying (step 3.7). One call per check, at sweep scale, reached GitHub's secondary rate limit when measured (Decision Log). Without the network the validator already fails at `gh_live_labels`, so no new failure mode is added.
- **A sweep edit is wrong.** DR4's checks run before any write. A wrong edit that passes them adds backticks in the wrong place, which AC4.2's reading catches. Any body is restored from GitHub's edit history, or from the snapshot while the session lasts, with `gh issue edit <N> --body-file`.
- **Rollback:** steps 1, 2 and 4 are each a commit, reverted with `git revert`. Step 3's issue edits are reverted body by body, as above.

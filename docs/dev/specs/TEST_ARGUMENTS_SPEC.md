# Test Arguments — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261116
**Branch:** `hotfix/issue-286-test-arguments` (from `main`)
**Target release:** set by `/closeout`
**Originating item:** Issue #286
**Design study:** `../design/DESIGN_TEST_ARGUMENTS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261114 | Ray | Branch type: `hotfix/*`. | Adopted; header. |
| 20261114 | Ray | Design study Q1: Option A. Rule 5 names the places an argument may come from: a fixture pytest provides, a fixture in `tests/conftest.py`, or a `parametrize` mark on the test or its class. A fixture defined in a test file, and a `@patch` decorator argument, move into the test body. | Adopted; DR1, DR3, DR4, Steps 1 to 4. |
| 20261114 | Ray | Design study Q1, correction 1: `provider_manager` and `dirs` are yield fixtures that patch. The spec states how each becomes a context manager, so its patch is still undone. | Adopted; DR2, Step 3. |
| 20261114 | Ray | Design study Q1, correction 2: the three `@patch` tests in `unittest.TestCase` classes are not edited; #208 and #209 replace those tests. | Adopted; DR4, §1 Out of scope, the AC1.1 command. |
| 20261114 | Ray | Design study Q1, correction 3: rule 5 states that it governs how a test gets an argument, and the §6.2 layer rules still govern what it asserts, so `capsys` does not license reading printed text. | Withdrawn by Ray, 20261116 (row below). |
| 20261114 | Ray | Design study Q2 and Q3: fixtures a test depends on without naming them go to #287; module-level tests go to #288, with rule 5's "method of a plain class" unchanged. | Adopted; §1 Out of scope. |
| 20261116 | Ray | Design study Q1, correction 3 is withdrawn. The §6.2 Renderer rule already decides which tests read printed text, so rule 5 does not restate it. | Adopted; Step 1, DR1, AC2.1. |
| 20261116 | Ray | Rule 5's new text is the text Step 1 quotes. The standard states the rule, not a list of names or exceptions, so it drops the "such as" fixture names, the `capsys` clause and the sentence saying the rule governs how a test gets an argument, not what it asserts. Rules 1 and 6 already name their own fixtures, and the Renderer rule already decides which tests read printed text. | Adopted; Step 1. |
| 20261116 | Ray | Rule 5 does not say how a patch a test builds is undone. That is a separate concern, and the clause was never run over the suite: `tests/test_task_lifecycle.py` `_run` (`:289`), used by plain classes, starts its patches with `p.start()` and stops them in a `finally` (`:297`–`:302`), which the clause would refuse. DR2 still decides how this spec converts `provider_manager` and `dirs`. | Adopted; Step 1. Verified at `tests/test_task_lifecycle.py:289-302`. |
| 20261116 | Ray | DR1 drops its last sentence, "The rule governs how a test gets what it uses, not what it asserts." | Adopted; DR1. |
| 20261116 | Ray | AC2.1 drops its `capsys` half. It is a stated reading by Ray of `docs/standards/6-testing.md` §6.2 rule 5, for whether a test author knows from it alone what a test may take as an argument. | Adopted; AC2.1. |
| 20261116 | Spanner | The issue's first criterion cannot see a class-level `parametrize` (13 names) or one a helper returns (2), and it allows names one by one, so it cannot say "a fixture pytest provides" (design study F16). Restated in §5 as AC1.1, which classifies each argument by where it comes from, under `docs/standards/1-workflow.md` §1.2. The issue body's edit is made at close-out. | Adopted; §5. |
| 20261116 | Spanner | `docs/standards/6-testing.md` §6.2 rule 9 asks for the test that shows a defect to be run before and after the fix. This defect is a disagreement between a rule and the suite, and no pytest test shows it. The AC1.1 command shows it: 31 lines before the fix, none after. The results artifact records both runs in place of a test's runs. Adding a test that enforces rule 5 would be tooling for a rule, which is an issue of its own. | Adopted; Step 5, §6. |
| 20261116 | Spanner | The two context managers are named `_provider_manager` and `_dirs` in the spec, because the AC1.2 command checks them by name. Every other helper this spec allows is below the contract. | Adopted; DR2, Step 3. |

---

## 1. Scope

**In scope:**

- `docs/standards/6-testing.md` §6.2 rule 5: its text (Step 1).
- The six fixtures defined in test files, and every test that takes one: `ts` (`tests/test_tag_system.py`), `loader` (`tests/test_templates.py`), `_sentinel_monday` (`tests/test_time_tracking.py`), `_active_client` (`tests/test_slack_channel_config.py`), `provider_manager` (`tests/test_cost_display.py`) and `dirs` (`tests/test_email_service.py`) (Steps 2 and 3).
- The two `@patch` decorators that pass `mock_generate` to tests in the plain class `TestNotesLogUnitOfWork` (`tests/test_notes_log.py`) (Step 4).

**Out of scope:**

- `monkeypatch` (63 tests), `capsys` (16), `offline_provider_env` (8) and every `parametrize` name (87). Rule 5 as Step 1 writes it allows them, so no test changes (design study F1–F3, F6–F8).
- The three `@patch("workmain.ai.provider_manager.ProviderManager.generate")` tests in `unittest.TestCase` classes: `tests/test_meetings_condense.py::TestMeetingsCondenseUsesComputedTags::test_meetings_condense_uses_computed_tags_not_both`, `::test_condense_existing_today_relinks_not_recreates` and `tests/test_notes_log.py::TestNotesLogCondenseUsesComputedTags::test_notes_log_condense_uses_computed_tags_not_both`. #208 and #209 replace them when they convert the meetings and notes command groups (Ray, Decision Log).
- The `autouse` fixtures `_no_writes` and `_no_editor` and the seven `usefixtures` marks: #287.
- The 86 module-level tests: #288. The 60 tests in `unittest.TestCase` classes: the command-group issues under #198.
- What any test asserts. No assertion is added, removed or changed (DR5).
- Any file under `workmain/`, `config/` or `templates/`.

## 2. Verified current state

On `hotfix/issue-286-test-arguments` at `7fed5b4`, whose `tests/` is `origin/main` `54599de`'s, 20261116.

| Claim | Evidence |
| --- | --- |
| Rule 5 reads: "**A test is a method of a plain class, and it takes what it needs as arguments.** It takes `db_session` for a session (rule 1), `tmp_path` for a directory (rule 6) and `caplog` for log records; anything else it needs, it builds in its own body. pytest hands a fixture only to a test that names it as an argument, so this is the one form in which every test can reach every fixture." | `docs/standards/6-testing.md:62` |
| No other document states rule 5's list or cites rule 5. The search found only rule 5 itself and two citations of rule 9. | `grep -rnE "rule 5\|takes what it needs\|for log records\|builds in its own body\|6\.2.*rule" CLAUDE.md docs/standards .claude docs/dev/*/_TEMPLATE_*.md .github automation/*.py` |
| The fixtures pytest provides and the fixtures `tests/conftest.py` defines are listed by `pytest --fixtures -v` with their location: `_pytest/` for pytest's own (including `monkeypatch`, `capsys`, `caplog`, `tmp_path`), and `tests/conftest.py` for `_test_database`, `_isolated_database`, `db_session` and `offline_provider_env`. | `pytest --fixtures -v -p no:cacheprovider` (pytest 7.4.3) |
| Run before any change, the AC1.1 command prints 31 lines, one for each argument this spec changes and nothing else: `provider_manager` 7, `dirs` 6, `ts` 6, `loader` 4, `_active_client` 4, `_sentinel_monday` 2, `mock_generate` 2. They are in 7 files: `tests/test_cost_display.py`, `tests/test_email_service.py`, `tests/test_tag_system.py`, `tests/test_templates.py`, `tests/test_slack_channel_config.py`, `tests/test_time_tracking.py`, `tests/test_notes_log.py`. | the AC1.1 command in §5 |
| `ts` returns `TagSystem()`; `loader` returns `TemplateLoader()`; `_sentinel_monday` returns the first Monday on or after `_TEST_DATE`. None has teardown. | `tests/test_tag_system.py:14`, `tests/test_templates.py:17`, `tests/test_time_tracking.py:40` |
| `_active_client(db_session)` adds a `Client` on the test's `db_session`, commits, makes it active with `ClientRepository(db_session).set_active(client.id)` and returns it. It has no teardown. Tests read and set the returned client's `slack_channel` (`:152`, `:161`, `:238`, `:250`). | `tests/test_slack_channel_config.py:29` |
| `provider_manager` builds a `MagicMock` manager and yields it inside `with patch('workmain.utils.ai_arguments.get_provider_manager', return_value=manager):`, so the patch is undone at teardown. Its seven tests, all in `TestCostCommands`, take it only for the patch: no test body names `provider_manager`. | `tests/test_cost_display.py:167-173`; `grep -n 'provider_manager' tests/test_cost_display.py` |
| `dirs(tmp_path)` makes `tmp_path / "reports"`, and yields `(reports, drafts)` inside `with patch.object(email_service, "REPORTS_DIR", reports), patch.object(email_service, "EMAIL_DIR", drafts):`. Its six tests unpack the yielded pair from the name `dirs` (`:49`, `:71`, `:88`, `:103`, `:111`). | `tests/test_email_service.py:24-32` |
| `tests/test_notes_log.py::TestNotesLogUnitOfWork::test_t17_a_failed_condensation_keeps_the_logged_notes` and `::test_t18_condense_repoints_the_existing_entry` are decorated `@patch("workmain.ai.provider_manager.ProviderManager.generate")` and take `mock_generate` first. `TestNotesLogUnitOfWork` has no base class. | `tests/test_notes_log.py:242-243`, `:264-265` |
| None of the six fixture names is reached other than as a test argument: no `usefixtures` mark names one, and no fixture takes one. | design study census (`usefixtures` list, fixture-argument list) |
| §6.1 and §6.2 already depend on sources rule 5 does not name. §6.2's Repository fake rule requires a class-level `parametrize`. §6.1 points to `tests/test_ai_costs.py`, whose `get_db` patch is made with `monkeypatch`. Step 1's text allows both, so neither needs an edit. | design study F9, F10 |
| `ruff` checks `tests/**` for import order (I) and type hints (ANN). D101–D103 are ignored there. `automation/style_check.py` checks every line a branch changes, and a re-indented line counts as changed. | `pyproject.toml` `[tool.ruff.lint]`, per-file-ignores; `automation/style_check.py` docstring |
| Suite: `1708 passed, 0 failed, 0 skipped`. | `CHANGELOG.md` 1.58.4 |

## 3. Design rules

- **DR1 — Rule 5 names where an argument may come from, not which names.** The places are: a fixture pytest itself provides, a fixture defined in `tests/conftest.py`, and a `@pytest.mark.parametrize` mark on the test or on its class. Anything else, the test builds in its own body.
- **DR2 — A test-file fixture that patches becomes a context manager the test enters around its whole body.** It is a module-level function in the same file, decorated `@contextlib.contextmanager`, whose body is the fixture's body unchanged. The test's former body runs, unchanged except for indentation, inside one `with` statement that enters it. The patch is then active for the same span pytest's fixture gave it, and is undone when the block exits, normally or by an exception. `provider_manager` becomes `_provider_manager()`, entered as `with _provider_manager():`. `dirs` becomes `_dirs(tmp_path)`, entered as `with _dirs(tmp_path) as dirs:`, so the body's `reports, drafts = dirs` lines stay as they are. Each test then takes `tmp_path` where it took `dirs`.
- **DR3 — A test-file fixture with no teardown is built at the start of the test body,** bound to the name the argument had, so the rest of the body is unchanged. `_active_client` is built from the test's `db_session`. Whether the value is built inline or by calling a module helper is below the contract. A helper must not keep the fixture's name where the test binds a local of that name, since Python would then treat the name as an unbound local. The `@pytest.fixture` definitions are deleted.
- **DR4 — A `@patch` decorator that passes an argument to a test in a plain class becomes `with patch(<the same target and arguments>) as <the argument's name>:`** around the test's whole former body. Tests in `unittest.TestCase` classes keep their decorators.
- **DR5 — No assertion changes.** A test's assertions, `pytest.raises` blocks and the values it sets on mocks are the same before and after. Only how the test gets what it uses changes.

Anything this spec does not decide is a departure: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Every line a step changes passes `python3 automation/style_check.py`. A re-indented line counts as changed. A test signature a step changes therefore carries type hints on its arguments and `-> None`.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Rule 5 names the places an argument may come from | `docs/standards/6-testing.md` |
| 2 | The four test-file fixtures with no teardown are built in the test body | `tests/test_tag_system.py`, `tests/test_templates.py`, `tests/test_time_tracking.py`, `tests/test_slack_channel_config.py` |
| 3 | The two test-file fixtures that patch become context managers the tests enter | `tests/test_cost_display.py`, `tests/test_email_service.py` |
| 4 | The two `@patch` arguments in `TestNotesLogUnitOfWork` become `with patch(...)` | `tests/test_notes_log.py` |
| 5 | Results artifact | `docs/dev/results/TEST_ARGUMENTS_RESULTS.md` |

### Step 1 — rule 5

In `docs/standards/6-testing.md` §6.2, replace rule 5:

> 5. **A test is a method of a plain class, and it takes what it needs as arguments.** It takes `db_session` for a session (rule 1), `tmp_path` for a directory (rule 6) and `caplog` for log records; anything else it needs, it builds in its own body. pytest hands a fixture only to a test that names it as an argument, so this is the one form in which every test can reach every fixture.

with:

> 5. **A test is a method of a plain class, and it takes what it needs as arguments.** An argument is a fixture pytest provides, a fixture in `tests/conftest.py`, or a name a `parametrize` mark on the test or its class supplies; anything else, the test builds in its own body. pytest hands a fixture only to a test that names it as an argument, so this is the one form in which every test can reach every fixture.

No other line of the file changes.

### Step 2 — fixtures with no teardown

By DR3, for `ts` (`tests/test_tag_system.py`, 6 tests), `loader` (`tests/test_templates.py`, 4), `_sentinel_monday` (`tests/test_time_tracking.py`, 2) and `_active_client` (`tests/test_slack_channel_config.py`, 4). The test that takes each is the one the AC1.1 command names. Each test drops the argument and builds the value as its first statement. If the test has a docstring, the value is built after it. Each `@pytest.fixture` definition is deleted.

### Step 3 — fixtures that patch

By DR2, for `provider_manager` (`tests/test_cost_display.py`, 7 tests) and `dirs` (`tests/test_email_service.py`, 6 tests). Each fixture becomes the module-level `@contextlib.contextmanager` function DR2 names, with the same body, and its `@pytest.fixture` is removed. Each test that took the fixture runs its whole former body inside the `with` statement DR2 states. If the test has a docstring, the docstring stays first and the `with` follows it.

### Step 4 — `@patch` arguments in a plain class

By DR4, for `tests/test_notes_log.py::TestNotesLogUnitOfWork::test_t17_a_failed_condensation_keeps_the_logged_notes` and `::test_t18_condense_repoints_the_existing_entry`. Each drops `@patch("workmain.ai.provider_manager.ProviderManager.generate")` and its `mock_generate` argument. Each runs its whole former body inside `with patch("workmain.ai.provider_manager.ProviderManager.generate") as mock_generate:`.

### Step 5 — results artifact

`docs/dev/results/TEST_ARGUMENTS_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. Under "Defect shown before the fix" it records the AC1.1 command's run before Step 2 (31 lines) and after Step 4 (nothing), in place of a test's runs (Decision Log). AC2.1 is recorded `Not met`, `Awaiting Ray` (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every argument a test in `tests/` takes comes from a place rule 5 names: a fixture pytest provides, a fixture in `tests/conftest.py`, or a `parametrize` mark on the test or its class, including one a helper in the test's file returns. Tests in `unittest.TestCase` classes are left out: their `@patch` arguments are #208's and #209's (Decision Log). | The AC1.1 command below printing nothing. Before Step 2 it prints the 31 lines §2 lists, so it can return both answers. |
| AC1.2 | Each test that took a patching fixture or a `@patch` argument still has the patch in place for its whole body, and the patch is undone when the body ends (DR2, DR4) | The AC1.2 command below printing nothing. Before Step 3 it prints 17 lines: both context managers missing, and all 15 tests failing the check. |
| AC1.3 | No fixture a test could not take under rule 5 is left defined in a test file, except the two `autouse` fixtures #287 owns | `pytest --fixtures -v -p no:cacheprovider 2>/dev/null \| grep -E -- '-- tests/test_'` printing only `_no_writes` and `_no_editor` |
| AC1.4 | No test's assertions changed, and no file under `tests/` changed except the seven the steps list (DR5) | `git diff -w -U0 origin/main...HEAD -- tests/ \| grep -E '^[-+]\s*(assert\b\|with pytest\.raises\|.*\.return_value\s*=\|.*\.side_effect\s*=)'` printing nothing; `git diff --name-only origin/main...HEAD -- tests/` listing exactly `tests/test_cost_display.py`, `tests/test_email_service.py`, `tests/test_notes_log.py`, `tests/test_slack_channel_config.py`, `tests/test_tag_system.py`, `tests/test_templates.py`, `tests/test_time_tracking.py` |
| AC2.1 | A test author can tell from rule 5 alone where a test may get each kind of argument the census found | A stated reading by Ray of `docs/standards/6-testing.md` §6.2 rule 5, for whether a test author knows from it alone what a test may take as an argument |
| AC3.1 | The full suite passes, with no test lost or added | `pytest` reporting `1708 passed, 0 failed, 0 skipped` |

**AC1.1 command**, run from the repository root:

```bash
pytest --fixtures -v -p no:cacheprovider 2>/dev/null | python3 -c '
import ast, pathlib, re, sys
allowed = {m[1] for m in (re.match(r"^(\w+)(?: \[[^]]*\])? -- (\S+):\d+$", l) for l in sys.stdin) if m and ("/_pytest/" in m[2] or m[2] == "tests/conftest.py")}
def marks(decos, helpers):
    names = set()
    for d in decos:
        if not isinstance(d, ast.Call):
            continue
        f = ast.unparse(d.func)
        call = d if f.endswith("parametrize") else helpers.get(f)
        if call is None:
            continue
        a = call.args[0] if call.args else next(k.value for k in call.keywords if k.arg == "argnames")
        if isinstance(a, ast.Constant):
            names |= {s.strip() for s in a.value.split(",")}
        else:
            names |= {e.value for e in a.elts}
    return names
for p in sorted(pathlib.Path("tests").rglob("test_*.py")):
    tree = ast.parse(p.read_text())
    helpers = {n.name: r.value for n in tree.body if isinstance(n, ast.FunctionDef) for r in ast.walk(n) if isinstance(r, ast.Return) and isinstance(r.value, ast.Call) and ast.unparse(r.value.func).endswith("parametrize")}
    def walk(body, inherited, testcase):
        for n in body:
            if isinstance(n, ast.ClassDef):
                walk(n.body, inherited | marks(n.decorator_list, helpers), any(ast.unparse(b).endswith("TestCase") for b in n.bases))
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test") and not testcase:
                ok = allowed | inherited | marks(n.decorator_list, helpers) | {"self"}
                for a in n.args.posonlyargs + n.args.args + n.args.kwonlyargs:
                    if a.arg not in ok:
                        print(f"{p}:{n.lineno} {n.name} {a.arg}")
    walk(tree.body, set(), False)
'
```

It takes the fixtures pytest provides and those in `tests/conftest.py` from pytest's own listing, so it carries no list of names. It reads `parametrize` names from the test's decorators, its enclosing classes' decorators, and any module-level helper that returns a `parametrize` mark. Module-level tests are checked too. #288 moves them into classes; it does not change their arguments.

**AC1.2 command**, run from the repository root:

```bash
python3 - <<'EOF'
import ast, pathlib
CASES = {
    "tests/test_cost_display.py": ("_provider_manager", "provider_manager", ["test_service_gets_the_parsed_options_and_the_renderer_the_result", "test_no_options_means_this_month_and_every_provider", "test_all_means_no_dates", "test_start_and_end_are_passed_through", "test_month_means_its_first_and_last_day", "test_a_service_failure_is_one_error_line_on_stderr", "test_bad_values_are_usage_errors"]),
    "tests/test_email_service.py": ("_dirs", "dirs", ["test_t1_build_draft_assembles_the_draft", "test_t2_subject_follows_the_template_name", "test_t3_build_draft_without_a_report_raises", "test_t4_save_draft_writes_the_draft_file", "test_t5_save_draft_without_a_report_writes_nothing", "test_t6_save_draft_without_recipients_still_saves"]),
    "tests/test_notes_log.py": ("patch", "mock_generate", ["test_t17_a_failed_condensation_keeps_the_logged_notes", "test_t18_condense_repoints_the_existing_entry"]),
}
for path, (helper, old, names) in CASES.items():
    tree = ast.parse(pathlib.Path(path).read_text())
    if helper != "patch":
        d = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == helper), None)
        if d is None or not any(ast.unparse(x).endswith("contextmanager") for x in d.decorator_list):
            print(f"{path}: {helper} is not a module-level contextmanager function")
    tests = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    for name in names:
        n = tests.get(name)
        if n is None:
            print(f"{path}::{name} missing")
            continue
        body = n.body[1:] if isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) else n.body
        w = body[0] if len(body) == 1 and isinstance(body[0], ast.With) else None
        if w is None or ast.unparse(w.items[0].context_expr.func) != helper or any(a.arg == old for a in n.args.args) or n.decorator_list and any("patch" in ast.unparse(x) for x in n.decorator_list):
            print(f"{path}:{n.lineno} {name}: its whole body is not one with-block entering {helper}, or it still takes {old}")
EOF
```

The issue's first criterion is checked by AC1.1 to AC1.4 in place of the command the issue states (Decision Log). Its second criterion is checked by AC2.1, and its third by AC3.1.

## 6. Test plan

- **Baseline before this work:** `1708 passed, 0 failed, 0 skipped` (`CHANGELOG.md` 1.58.4).
- **Expected after:** `1708 passed, 0 failed, 0 skipped`. No test is added or removed, and none changes its node ID: every changed test keeps its name and its class.
- No test file is added. The defect is shown by the AC1.1 command's runs before Step 2 and after Step 4, recorded in the results artifact (Decision Log).

## 7. Risks and rollback

- **A patch that no longer covers the whole test.** If part of a body were left outside the `with` block, a test could reach the real `get_provider_manager`, or the real report and draft directories under `~/.workmain/`. AC1.2 checks that the whole body is inside the block, and the steps leave the body unchanged except for indentation.
- **A name the helper shadows.** By DR3, a helper that kept a fixture's name and was bound to the same local raises `UnboundLocalError`. The suite run in each step catches it.
- **Rollback:** each step is one commit and reverts on its own. Step 1 reverted alone leaves rule 5 naming only three fixtures, so the suite disagrees with it again, and AC1.1 shows that.

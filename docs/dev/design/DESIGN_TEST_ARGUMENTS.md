# Test Arguments — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261114
**Originating item:** Issue #286

---

## 1. Purpose

`docs/standards/6-testing.md` §6.2 rule 5 says what a test may take as an argument: "It takes `db_session` for a session (rule 1), `tmp_path` for a directory (rule 6) and `caplog` for log records; anything else it needs, it builds in its own body." The suite does not follow it, so the rule and the suite disagree, and a test author reading the rule cannot tell whether the suite or the rule is right. This study measures every argument the suite's tests take, sorts the arguments by where they come from, and sets out for each kind whether the rule should name it or the tests should build it in their bodies. Those decisions are Ray's, because a change to rule 5 is a change to a standard.

## 2. Scope of the read

- Every `test_*.py` and `conftest.py` under `tests/`, on `hotfix/issue-286-test-arguments` at `54599de` (`origin/main`; `git diff --stat origin/main origin/dev` is empty, so `dev` holds the same tests). `pytest --collect-only -q` collects 1708 tests.
- The census script is an AST walk. For each function or async function whose name starts with `test`, at module level or in a class at any depth, it reads every positional-only, positional and keyword-only argument. Each argument that is not `self`, `db_session`, `tmp_path` or `caplog` is sorted by source: a name the function's own `parametrize` supplies, a name its class's `parametrize` supplies, or neither. For `parametrize`, the argument names are read from a string, a tuple or list, or the `argnames=` keyword. The "neither" arguments were then traced by hand to a pytest built-in fixture, a fixture in `tests/conftest.py`, a fixture defined in the test's own file, a `mock.patch` decorator, or a helper that returns a `parametrize` mark. The script also lists fixture definitions, `autouse` fixtures, `usefixtures` marks, module-level tests and tests in classes that have base classes.
- `docs/standards/6-testing.md` §6 end to end, for every other statement that bears on rule 5. Also `docs/archive/specs/TESTCASE_CONVERSION_SPEC.md`, the spec for issue #200 that wrote rule 5, and the commit that wrote it (`5724f92`), for what the rule was written to do. The archived spec is the record of that, not the basis for a decision here (`docs/standards/1-workflow.md` §1.5).
- Not read: `automation/` tests (`*_test.py`, a separate suite under `docs/standards/6-testing.md` §6), and `scripts/baseline/` (restricted until #188 ships).

## 3. Findings

### Arguments rule 5 does not name

208 arguments in 31 files. By source:

| # | Source | Names | Tests | Files |
| --- | --- | --- | --- | --- |
| F1 | pytest built-in fixture | `monkeypatch` | 63 | 11 — `tests/test_ai_costs.py`, `tests/test_eod_workflow.py`, `tests/test_gdrive.py`, `tests/test_intent_parser.py`, `tests/test_narration.py`, `tests/test_note_condenser.py`, `tests/test_notification_engine.py`, `tests/test_orchestration.py`, `tests/test_output.py`, `tests/test_provider_foundation.py`, `tests/test_state_io.py` |
| F2 | pytest built-in fixture | `capsys` | 16 | 3 — `tests/test_ai_arguments.py` (4), `tests/test_cli_logging.py` (1), `tests/test_eod_workflow.py` (11) |
| F3 | Fixture in `tests/conftest.py` | `offline_provider_env` (`tests/conftest.py:184`: fake vendor keys in the environment, both vendor clients patched) | 8 | 2 — `tests/test_ai_foundation.py`, `tests/test_ai_providers_offline.py` |
| F4 | Fixture defined in the test's own file | `provider_manager` (`tests/test_cost_display.py:168`), `dirs` (`tests/test_email_service.py:25`), `ts` (`tests/test_tag_system.py:14`), `_active_client` (`tests/test_slack_channel_config.py:29`), `loader` (`tests/test_templates.py:17`), `_sentinel_monday` (`tests/test_time_tracking.py:40`) | 29 (7, 6, 6, 4, 4, 2) | 6 |
| F5 | `mock.patch` decorator, which passes the mock as an argument | `mock_generate`, from `@patch("workmain.ai.provider_manager.ProviderManager.generate")` | 5 | 2 — `tests/test_meetings_condense.py:93`, `:124` and `tests/test_notes_log.py:156`, all three in `unittest.TestCase` classes; `tests/test_notes_log.py:243`, `:265`, in the plain class `TestNotesLogUnitOfWork` |
| F6 | The test's own `@pytest.mark.parametrize` | many | 72 | 18 |
| F7 | A helper that returns a `parametrize` mark | `name`, from `_names()` (`tests/test_cost_display.py:163`, `return pytest.mark.parametrize('name', keys)`) | 2 | 1 — `tests/test_cost_display.py:193`, `:211` |
| F8 | The test's class's `@pytest.mark.parametrize` | `kind`, on `TestSystemStateContract` (`tests/test_fake_unit_of_work.py:181`, `['real', 'fake']`) | 13 | 1 |

F1 to F5 and F7 are the issue's 123 arguments, reproduced exactly. The issue lists `mock_generate` (F5) and `name` (F7) as fixtures the project defines; neither is a fixture. The 13 in F8 come from `tests/test_fake_unit_of_work.py`, committed at 07:53 PST on 20261114 (`2f6ac81`), after the issue was opened at 07:29 PST.

### Statements in §6 that bear on rule 5

| # | Finding | Evidence |
| --- | --- | --- |
| F9 | §6.2's own rule for a repository fake requires a class-level `parametrize`, which rule 5 does not allow: "each fake method's behaviour tests run in one class parametrized over the real repository on `db_session` and the fake." F8 is that class. | `docs/standards/6-testing.md` §6.2 § Repository fake; `tests/test_fake_unit_of_work.py:181` |
| F10 | §6.1 holds up two files as the way to do something, and both do it with a fixture rule 5 does not name. "Patch the module's `get_db` to raise, as `tests/test_ai_costs.py` does": that patch is `monkeypatch.setattr('workmain.services.ai_cost_service.get_db', _refuse)`, in a test that takes `monkeypatch` (`tests/test_ai_costs.py:576`, `:581`). `tests/test_orchestration.py`, cited for replacing `threading.Thread`, does that with `patch.object` in the body (`:1476`), which rule 5 allows. Other tests in the same file take `monkeypatch` (`:1051`, `:1065`). | `docs/standards/6-testing.md` §6.1 |
| F11 | Rule 5 was written to settle the form a test takes, not to make a list of what it takes. Issue #200's Step 7 first worded it as "What a test needs set up is a fixture it takes or code in its own body". Ray's 20261012 ruling restated it in its present form, so that it "excludes `setUp`, `setup_method` and attribute-setting autouse fixtures by its reason". The three names were the three fixtures that spec's five files used. Nothing records the list being run over the whole suite, which `docs/standards/1-workflow.md` §1.2 requires of a rule that refuses authored text. The rule's own reason is still true of any fixture: "pytest hands a fixture only to a test that names it as an argument, so this is the one form in which every test can reach every fixture." | `docs/archive/specs/TESTCASE_CONVERSION_SPEC.md` Decision Log row 20261012, Ray; `git show 5724f92` |
| F12 | Building F1 and F2 in the test body gives the same thing the fixture gives. `pytest.MonkeyPatch.context()` yields a `MonkeyPatch` and undoes it on exit, as the `monkeypatch` fixture does at teardown. `contextlib.redirect_stdout` and `redirect_stderr` replace `sys.stdout` and `sys.stderr`, as `capsys` does. Neither is a correction of what the tests do; each is the same capability in more lines. | pytest's `MonkeyPatch.context` and `capsys` (system-level capture) |

### Outside the issue's acceptance criteria

The issue's criteria are about arguments. These findings bear on rule 5 but are not arguments, so whether any of them is this issue's work is Ray's (§5).

| # | Finding | Evidence | Open issue that covers it |
| --- | --- | --- | --- |
| F13 | Two `autouse` fixtures in test files patch for every test in their class without any test naming them: `_no_writes` makes `AiCostRepository.create` and `.link_report` raise, and `_no_editor` deletes `EDITOR`. Each test needs that patch and does not build it in its body. Rule 5 does not mention them. Its reason rules out an autouse fixture that sets an attribute on `self`; neither of these sets one. `tests/conftest.py` `_isolated_database` is the autouse fixture that `docs/standards/6-testing.md` §6.1 requires, and is not one of these. | `tests/test_ai_costs.py:749` (`TestCostReads`); `tests/test_notes_log.py:198` (`TestNotesLogUnitOfWork`) | none found |
| F14 | Seven classes reach a fixture through `@pytest.mark.usefixtures` rather than an argument. Six are `usefixtures('db_session')` in `tests/test_action_executor.py`, which #200 left as they were because they "repeat an argument the tests already take". One is `usefixtures('offline_provider_env')` on `TestCompareProviders` (`tests/test_compare_providers.py:84`), and none of its tests takes that fixture. | the census's `usefixtures` list; `docs/archive/specs/TESTCASE_CONVERSION_SPEC.md` §1 Out of scope | none found |
| F15 | Rule 5's first clause, "a method of a plain class", is broken in two ways. 86 tests in 9 files are module-level functions, 66 of them in `tests/test_provider_foundation.py`. 60 tests in 11 files are methods of `unittest.TestCase` classes. | the census's module-level and base-class lists | TestCase: the command-group issues under #198. `docs/standards/6-testing.md` §6.2 says converting a group replaces every test of its commands, and the #200 spec left these files to them. Module-level: none found |
| F16 | The issue's first criterion cannot see two of the forms it judges. It reads `parametrize` only on the function and only from a string, so it reports F8's 13 class-level names and F7's 2 helper names as violations whatever rule 5 says. It also cannot express "a fixture from `tests/conftest.py`" or "a pytest built-in", because it allows names one by one. It prints 136 lines today. | the criterion's command, run 20261114 | n/a: the spec restates the criterion in its §5 and records the issue edit for close-out (`docs/standards/1-workflow.md` §1.2) |

Open issues were searched with `gh issue list --state open --search` for `TestCase`, `monkeypatch`, `capsys`, `fixture`, `parametrize`, `usefixtures`, `module-level`, `rule 5` and `6.2`, and every result was read. None names F13, F14 or the module-level part of F15.

## 4. Options

The issue puts every kind of argument to one choice: rule 5 names it, or the tests build it in their bodies. Two policies answer every kind at once. They differ only on F4 and F5.

### Option A — rule 5 names sources, and only a test-file fixture or a patch decorator moves into the body

- **Approach:** rule 5 lists where a test's arguments may come from, not which names:
  - a fixture pytest provides (F1, F2, and the `tmp_path` and `caplog` it already names)
  - a fixture in `tests/conftest.py` (F3, and `db_session`)
  - a name the `parametrize` mark on the test or on its class supplies (F6, F7, F8)

  Anything else is built in the test body. The fixtures in F4 become module helpers that each test calls in its body. The `@patch` decorators in F5 become `with patch(...) as mock_generate:` in the body. The rule keeps its reason, and §6.1 and §6.2's Repository fake rule then agree with it.
- **Pros:** The suite already does this, so the rule describes it. One place, `tests/conftest.py`, holds every fixture a test can take that pytest does not provide. The rule doesn't have to change when a new built-in or shared fixture comes into use. F9 and F10 stop contradicting rule 5. Edits are limited to 34 tests in 8 files, all mechanical.
- **Cons:** A shared fixture in `tests/conftest.py`, such as `offline_provider_env`, still sets up things a reader cannot see from the test body.

### Option B — rule 5 names any fixture

- **Approach:** as A, except that a fixture defined anywhere is allowed, and so is a `mock.patch` decorator argument. No test changes. This is essentially the wording from #200's Step 7, "a fixture it takes or code in its own body".
- **Pros:** No test edits. The rule cannot be broken by any existing test.
- **Cons:** "Anything else it needs, it builds in its own body" then rules out nothing pytest can deliver, so it says nothing. A one-file fixture and a one-file helper do the same job, with no rule for picking between them. F5's decorator passes mocks by position, in reverse order of the decorators, ahead of fixtures, so the order of a test's arguments decides what each one is.

### Option C — keep the three names and build everything else in the body

- **Approach:** the issue's "build it in the body" choice for every kind. 63 `monkeypatch` tests change to `pytest.MonkeyPatch.context()`, and 16 `capsys` tests to `redirect_stdout`/`redirect_stderr`. F3 and F4 are built inline. A parametrized name is either allowed (otherwise F9's rule and F6–F8 cannot stand) or every parametrized test is unrolled.
- **Pros:** The rule needs no change, apart from what a parametrized name is.
- **Cons:** 123 arguments in 23 files rewritten into code that does the same thing in more lines (F12). §6.1's exemplar (F10) has to change with them. It keeps a list that F11 shows was never measured against the suite, and every built-in that comes into use later goes against it.

**Recommendation: Option A.** Rule 5 is there to fix the form of a test, an argument rather than `setUp`, `setup_method` or `self` (F11). A built-in fixture, a shared fixture and a parametrized name all fit that form, and the standard already relies on two of them (F9, F10). Moving them into the body changes nothing a test does (F12), so C is churn. B is cheaper than A by 34 edits, but it leaves the second half of the rule meaning nothing, and it allows the one positional-injection form (F5) the suite barely uses. A keeps the second half meaningful, and means the lines the rule allows can be read off a file listing, not a register of names that must be kept up by hand (`docs/standards/1-workflow.md` §1.5).

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Which option does rule 5 take: A (sources: pytest built-ins, `tests/conftest.py` fixtures, the test's or its class's `parametrize`; test-file fixtures and `@patch` arguments move into the body), B (any fixture, no test edits), or C (the three names; built-ins and fixtures rebuilt in the body)? | |
| Q2 | Is the issue's work also to state rule 5's position on fixtures a test depends on without naming them: the two test-file `autouse` fixtures (F13) and the seven `usefixtures` marks (F14)? Or do they go to an issue of their own? Joining this issue means the study adds options for them before the spec. | |
| Q3 | 86 module-level tests in 9 files break rule 5's "method of a plain class" (F15), and no open issue covers them. Do they join this issue, go to an issue of their own, or does rule 5 change? The 60 TestCase tests are already covered by the command-group issues under #198 and are not proposed here. | |

## 6. Disposition

- Promoted to:
- Superseded by:

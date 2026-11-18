# Testing Standard Rules — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261117
**Spec:** `../specs/TESTING_STANDARD_RULES_SPEC.md`
**Released as:** v1.58.7 (tag v1.58.7)

---

## 1. Summary

Complete. Everything before `### 6.3 Placement` in `docs/standards/6-testing.md` is Ray's text, verbatim. The six record tests no longer fail a later scope, and each is renamed for what it checks. The fixtures' mechanics are in their docstrings, and `fake_uow` is added. The `pyproject.toml` comment that cited §6.2 is gone. The two rules that left §6 have their homes, and no live document or open issue cites a §6 rule by number. The suite is unchanged at 1707 tests, all passing.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 (`fa3ba28`) | §6's opening, §6.1 and §6.2 replaced by Ray's text | `docs/standards/6-testing.md` | +0 |
| 2 (`8924267`) | The six record tests without a later scope, renamed and annotated; `_fail_a_later_scope` deleted | `tests/test_ai_costs.py`, `tests/test_clockify_service.py`, `tests/test_gdrive.py`, `tests/test_slack.py` | +0 (6 renamed) |
| 3 (`dc51a7b`) | Docstrings of `_test_database`, `_isolated_database`, `db_session` and `tests/mocks/fake_unit_of_work.py`; the `fake_uow` fixture | `tests/conftest.py`, `tests/mocks/fake_unit_of_work.py` | +0 |
| 4 (`9653674`) | The comment above `"tests/**"` deleted | `pyproject.toml` | +0 |
| 5 (`d21e9f3`) | Defect-fix rule in `anvil.md` § Working rules; template cites it; §1.3 gains the rule on inputs an open issue leaves valid; `4-database.md` cites §6.2; #287 and #288 bodies edited | `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/standards/4-database.md`, `docs/standards/1-workflow.md`; issues #287, #288 | +0 |
| 6 | This artifact | `docs/dev/results/TESTING_STANDARD_RULES_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Ray, 20261117: §6.2 states how a test of an outside-action record is written, and that form opens no session through `get_db()`. The mechanical half is shown: no line of the six tests' bodies names `get_db` (§5 Record test bodies). |
| AC2.1 | Met | Ray, 20261117: Every `get_db()` call in `tests/` either complies with §6.1, or is in a test an open issue converts. Table in §5 `get_db()` census, which matches all 45 hits of `git grep -n 'get_db()' tests/` to a Step 6 category. |
| AC3.1 | Met | Ray, 20261117: Every statement of the old opening, §6.1 and §6.2 is accounted for: kept, moved with its new home, or deleted with its reason and table in §5 Where each old statement went. |
| AC3.2 | Met | `sed '/^### 6.3/,$d' docs/standards/6-testing.md \| wc -w` printed `660` (was 1,872). |
| AC3.3 | Met | The `tomllib` command printed `--strict-markers -rs`. `ANTHROPIC_API_KEY= GOOGLE_API_KEY= pytest tests/test_ai_providers_live.py` reported `5 skipped`, with five `SKIPPED [1] tests/test_ai_providers_live.py:<line>: <key> not set` lines (§5 AC3.3 run). |
| AC3.4 | Met | The comparison script in §5 AC3.4 printed `equal` for `_test_database` (8 lines), `_isolated_database` (18), `db_session` (10) and `fake_uow` (4), exit 0. |
| AC3.5 | Met | Ray, 20261117: No docstring Step 3 writes gives an instruction |
| AC4.1 | Met | Ray, 20261117: §6.2 states how a command branch that skips or changes a service call is tested, as a path through the command |
| AC6.1 | Met | `grep -nE '^[0-9]+\. ' docs/standards/6-testing.md` and the spec's `grep -rnE … \| grep -v …` both printed nothing. |
| AC6.2 | Met | The filter in §5 AC6.2 printed nothing, run after the Step 5 edits. |
| AC6.3 | Met | The first `grep` printed one line, `docs/standards/1-workflow.md:102`; the second printed one line, `.claude/skills/session-start/references/anvil.md:43`. |
| AC7.1 | Met | `git diff --stat origin/main...HEAD -- tests/` listed exactly `tests/conftest.py`, `tests/mocks/fake_unit_of_work.py`, `tests/test_ai_costs.py`, `tests/test_clockify_service.py`, `tests/test_gdrive.py`, `tests/test_slack.py`. |
| AC7.2 | Met | The spec's `git diff -U0 … \| grep -E …` printed nothing (exit 1). |
| AC8.1 | Met | `pytest`: `1707 passed, 0 failed, 0 skipped`. |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

None.

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 2 | New names: `test_record_reply_writes_its_row_in_a_record_scope`, `test_s17_the_link_is_written_in_a_record_scope`, `test_s26_a_link_is_written_in_a_record_scope`, `test_s28_an_import_is_written_in_a_record_scope`, `test_t18_record_is_written_in_a_record_scope`, `test_t19_record_is_written_in_a_record_scope`. Existing `s17`/`t18`-style prefixes kept. | Dropping the prefixes; naming the read through `db_session` | Each test now checks that the record is written inside `record_scope()` and can be read back; the prefixes are how the neighbouring tests are named. |
| 2 | 2 | `test_record_reply_…`'s docstring: "T8: the cost row is written in a record scope, and is read back through db_session." | Deleting the docstring | It is the only one of the six with a docstring, and the spec says to reword it. |
| 3 | 2 | `from sqlalchemy.orm import Session` placed in each file's third-party block in isort order. | — | `automation/style_check.py` runs ruff's `I` rules. |
| 4 | 2 | `import pytest` removed from `tests/test_gdrive.py`; the local import in the T8 test becomes `from workmain.database.connection import DatabaseConnection`. | Leaving them | The deletion left both unused, and Step 2 removes any import the deletion leaves unused. |
| 5 | 2 | `import json` in `tests/test_gdrive.py` left as it is. `_insert_cost`, `_make_upload` and `Client` stay. | Removing the unused `json` import | `json` was already unused on `origin/main`, so the deletion did not leave it unused, and no other line changes. The helpers and `Client` still have other uses. |
| 6 | 3 | The `TYPE_CHECKING` block goes after the third-party imports in `tests/conftest.py`, and `fake_uow` goes after `db_session`. | Putting the fixture at the end of the file | It sits next to the other database fixture. |
| 7 | 5 | `gh issue edit --body-file` was first sent each body with a trailing newline that the original lacked. The read-back showed it, and both bodies were sent again without it. The read-back now equals the edited file byte for byte. | Leaving the newline | Step 5 says nothing else in either body changes. |

## 5. Verification

- **Test suite:** 1707 passed, 0 failed, 0 skipped (baseline: 1707 passed, 0 failed, 0 skipped). The bare `pytest` run included `tests/test_ai_providers_live.py` with keys from `.env`.
- **Live verification:** none. No application code changed.
- **Daemon restart** (`docs/standards/2-git.md` §2.6): at close-out.

### Record test bodies (AC1.1)

Each test's body, from its `def` line to its last line, read with `ast`:

```text
tests/test_ai_costs.py:628-645 test_record_reply_writes_its_row_in_a_record_scope get_db lines: 0
tests/test_clockify_service.py:323-337 test_s17_the_link_is_written_in_a_record_scope get_db lines: 0
tests/test_clockify_service.py:489-499 test_s26_a_link_is_written_in_a_record_scope get_db lines: 0
tests/test_clockify_service.py:548-559 test_s28_an_import_is_written_in_a_record_scope get_db lines: 0
tests/test_gdrive.py:261-275 test_t18_record_is_written_in_a_record_scope get_db lines: 0
tests/test_slack.py:586-604 test_t19_record_is_written_in_a_record_scope get_db lines: 0
```

### `get_db()` census (AC2.1)

`git grep -n 'get_db()' tests/` at `d21e9f3`: 45 lines.

| Hit | Where | Category |
| --- | --- | --- |
| `tests/conftest.py:92` | `build_test_database` | The suite's own setup |
| `tests/conftest.py:138` | `_isolated_database` docstring | Not a call |
| `tests/conftest.py:158` | `_isolated_database` | The suite's own setup |
| `tests/conftest.py:205` | `db_session` | The suite's own setup |
| `tests/test_ai_arguments.py:268` | `TestReportTypeFiltersRows` docstring | Not a call |
| `tests/test_ai_arguments.py:276` | `TestReportTypeFiltersRows.setUp` (`unittest.TestCase`, invokes `reports`) | A test an open issue converts: #212 |
| `tests/test_ai_costs.py:657` | `def fake_get_db():` | Not a call |
| `tests/test_database_isolation.py:4` | module docstring | Not a call |
| `tests/test_database_isolation.py:47` | `TestIsolatedDatabase::test_an_application_session_sees_rows_the_test_seeded` | A test of the connection or the session machinery (`get_db()`) |
| `tests/test_database_isolation.py:59` | `TestIsolatedDatabase::test_an_application_rollback_keeps_the_rows_the_test_seeded` | A test of the connection or the session machinery (`session_scope()`) |
| `tests/test_database_isolation.py:69` | `TestIsolatedDatabase::test_closing_the_connection_during_a_test_raises` | A test of the connection or the session machinery (`DatabaseConnection.close()`) |
| `tests/test_database_isolation.py:76` | `TestRecordScope::test_record_scope_sets_the_lock_timeout` | A test of the connection or the session machinery (`record_scope()`) |
| `tests/test_database_isolation.py:100` | `TestTestDatabaseGuard::test_the_suite_is_connected_to_the_test_database` | A test of the connection or the session machinery (the connection's URL) |
| `tests/test_database_isolation.py:111` | `TestTestDatabaseBuild::test_the_build_empties_the_schema_and_upgrades_to_head` | A test of the database build |
| `tests/test_database_isolation.py:131` | `TestTestDatabaseBuild::test_a_run_builds_the_database_before_its_first_test` | A test of the database build |
| `tests/test_meetings_condense.py:72` | `TestMeetingsCondenseUsesComputedTags.setUp` (`unittest.TestCase`, invokes `meetings`) | A test an open issue converts: #208 |
| `tests/test_meetings_condense.py:187` | `TestMeetingsCondenseRefusal.setUp` (`unittest.TestCase`, invokes `meetings`) | A test an open issue converts: #208 |
| `tests/test_meetings_track.py:49` | `TestMeetingsTrackTagPromptAndClientId.setUp` (`unittest.TestCase`, invokes `meetings`) | A test an open issue converts: #208 |
| `tests/test_notes_add.py:51` | `TestNotesAddMeetingFollowOnTagPrompt.setUp` (`unittest.TestCase`, invokes `notes`) | A test an open issue converts: #209 |
| `tests/test_notes_edit.py:47` | `TestNotesEditRoutesThroughService.setUp` (`unittest.TestCase`, invokes `notes`) | A test an open issue converts: #209 |
| `tests/test_notes_log.py:56` | `TestNotesLogRoutesThroughService.setUp` (`unittest.TestCase`, invokes `notes`) | A test an open issue converts: #209 |
| `tests/test_notes_log.py:131` | `TestNotesLogCondenseUsesComputedTags.setUp` (`unittest.TestCase`, invokes `notes`) | A test an open issue converts: #209 |
| `tests/test_report_correction.py:493` | `TestReportConfirmCLI.setUp` (`unittest.TestCase`, invokes `reports`) | A test an open issue converts: #212 |
| `tests/test_report_correction.py:657` | `TestReportCorrectCLI.setUp` (`unittest.TestCase`, invokes `reports`) | A test an open issue converts: #212 |
| `tests/test_report_history.py:51` | `TestReportHistory.setUp` (`unittest.TestCase`, invokes `reports`) | A test an open issue converts: #212 |
| `tests/test_report_history.py:135` | `TestReportView.setUp` (`unittest.TestCase`, invokes `reports`) | A test an open issue converts: #212 |
| `tests/test_report_history.py:228` | `TestReportResend.setUp` (`unittest.TestCase`, invokes `reports`) | A test an open issue converts: #212 |
| `tests/test_reports_corrections.py:52` | `TestReportsCorrections.setUp` (`unittest.TestCase`, invokes `reports`) | A test an open issue converts: #212 |
| `tests/test_slack.py:415` | `TestSlackPostWeeklySharedRunner.setUp` (`unittest.TestCase`, invokes `slack`) | A test an open issue converts: #214 |
| `tests/test_time_add.py:71` | `TestTimeAddExtraNoteSourceDefault.setUp` (`unittest.TestCase`, invokes `time`) | A test an open issue converts: #216 |
| `tests/test_time_add.py:136` | `TestTimeAddMeetingPathClientId.setUp` (`unittest.TestCase`, invokes `time`) | A test an open issue converts: #216 |
| `tests/test_unit_of_work.py:5` | module docstring | Not a call |
| `tests/test_unit_of_work.py:56` | `TestScopeState::test_true_inside_session_scope` | A test of the connection or the session machinery (`session_scope()`) |
| `tests/test_unit_of_work.py:60` | `TestScopeState::test_true_inside_record_scope` | A test of the connection or the session machinery (`record_scope()`) |
| `tests/test_unit_of_work.py:65` | `TestScopeState::test_false_before_and_after` | A test of the connection or the session machinery (`session_scope()`) |
| `tests/test_unit_of_work.py:70` | `TestScopeState::test_nested_scope_restores_true` | A test of the connection or the session machinery (`session_scope()`) |
| `tests/test_unit_of_work.py:71` | `TestScopeState::test_nested_scope_restores_true` | A test of the connection or the session machinery (`session_scope()`) |
| `tests/test_unit_of_work.py:78` | `TestScopeState::test_false_after_exception` | A test of the connection or the session machinery (`session_scope()`) |
| `tests/test_unit_of_work.py:84` | `TestScopeState::test_false_after_keyboard_interrupt` | A test of the connection or the session machinery (`session_scope()`) |
| `tests/test_unit_of_work.py:90` | `TestScopeState::test_false_on_another_thread` | A test of the connection or the session machinery (`session_scope()`) |
| `tests/test_unit_of_work.py:195` | `TestReentryGuard::test_refused_by_open_scope_check_enters_after_scope_closes` | A test of the connection or the session machinery (the scope a test of `UnitOfWork`'s check opens) |
| `tests/test_unit_of_work.py:222` | `TestReentryGuard::test_refused_in_open_scope_opens_no_session` | A test of the connection or the session machinery (the scope a test of `UnitOfWork`'s check opens) |
| `tests/test_unit_of_work.py:234` | `TestOpenScopeCheck::test_inside_bare_session_scope_raises` | A test of the connection or the session machinery (the scope a test of `UnitOfWork`'s check opens) |
| `tests/test_unit_of_work.py:246` | `TestOpenScopeCheck::test_after_scope_closes_enters` | A test of the connection or the session machinery (the scope a test of `UnitOfWork`'s check opens) |
| `tests/test_unit_of_work.py:252` | `TestOpenScopeCheck::test_record_inside_open_scope_enters` | A test of the connection or the session machinery (the scope a test of `UnitOfWork`'s check opens) |

The class, function and invoked group of each hit come from an `ast` walk of the hit's file, which records the enclosing class and its bases, the enclosing function, and each `invoke(<group>` in the class.

### Where each old statement went (AC3.1)

The spec's Step 1 table, with each row checked against the delivered files.

| Old statement | Status | Home, or reason | Checked |
| --- | --- | --- | --- |
| Opening: pytest is the exclusive runner | Kept | §6 | `6-testing.md` §6, first bullet |
| Opening: the application suite is a bare `pytest`; `testpaths` resolves it; no other invocation stands in unless a spec names it and says why, including a path subset, a filter or an environment variable | Kept, shortened | §6: "Any other run offered as the suite's result names the alternative and states why." The `testpaths` mechanism and the list of alternatives are deleted; `pyproject.toml` holds the first, and "any other run" covers the second. | §6, second bullet; `pyproject.toml` `testpaths = ["tests"]` |
| Opening: non-application suites; "§7 owns test placement" | Kept, shortened | §6. The pointer to §7 is deleted: `docs/standards/README.md`'s index names §7. | §6, third bullet; `README.md` § Sections row for §7 |
| Opening: a test reports what actually happened | Kept, shortened | §6's three sub-bullets. "never reports passed without having run" is covered by "ran to its end". "only way a test is skipped" and "never reports skipped after it has run" are covered by the Skipped sub-bullet. "A skip is never added to turn a red suite green" is deleted: `-rs` reports every skip with its reason. | §6, fourth bullet and its three sub-bullets; `pyproject.toml` `addopts` |
| Opening: recorded evidence states all three counts | Kept, shortened | §6 | §6, fifth bullet |
| Opening: the command examples | Deleted | pytest's own usage; they state no rule | Absent from §6 |
| §6.1: the build from empty, the `DB_NAME` guard, `workmain_test`'s creation; "The rest of the connection comes from `.env`"; the `(§4.5)` citation | Moved, part deleted | `_test_database`'s docstring; §6.1's rule names `workmain_test`. Where the rest of the connection comes from, and the `(§4.5)` citation, are deleted. | `tests/conftest.py` `_test_database` docstring; §6.1's bold rule |
| §6.1: the transaction, `_isolated_database`, `join_transaction_mode` | Moved | §6.1's rule, and `_isolated_database`'s docstring | §6.1's bold rule; `_isolated_database` docstring, first paragraph |
| §6.1: every session through `get_db()` joins | Kept | §6.1, "A test seeds and reads through `db_session`." | §6.1, first bullet |
| §6.1: the table of commit, rollback, test end and process killed | Moved, part deleted | `_isolated_database`'s docstring. Deleted: "every commit a session opened after it made in the meantime". | `_isolated_database` docstring, first and second paragraphs |
| §6.1: take `db_session`; never call `get_db()` or `db.get_session()` in a test | Kept; ban deleted | §6.1 keeps `db_session`. | §6.1, first bullet; no ban in §6 |
| §6.1: hand application code a session only before it opens its own | Moved, part deleted | `_isolated_database`'s docstring states the failure. Deleted: the remedy, `InvalidSavepointSpecification`, `TestMeetingsCondenseTokenLine`. | `_isolated_database` docstring, second paragraph |
| §6.1: a record committed inside another open transaction is discarded; the record test | Moved | §6.2, "An outside-action record" | §6.2, fifth bullet |
| §6.1: inject a database failure; never rely on one | Deleted | §6.2, "A test's result depends only on what it sets up", covers it | §6.2 Rules, second bullet |
| §6.1: leaving the transaction fails the test (`close()`, `SessionLocal`, own engine) | Moved | `_isolated_database`'s docstring; §6.1, "Everything a test reaches stays on the test's connection." | `_isolated_database` docstring, third paragraph; §6.1, second bullet |
| §6.1: the exceptions for `tests/test_database_isolation.py` and `tests/test_unit_of_work.py` | Deleted | Without the ban there is nothing to except | Absent from §6 |
| §6.1: a child process is outside the transaction | Deleted | §6.1, "Everything a test reaches stays on the test's connection." | §6.1, second bullet |
| §6.1: database work stays on the test's thread | Deleted | The same | §6.1, second bullet |
| §6.2: the example | Deleted | Ray's reasons (Decision Log) | Absent from §6.2 |
| §6.2 rule 1: take `db_session` | Moved | §6.1, "A test seeds and reads through `db_session`." | §6.1, first bullet |
| §6.2 rule 2: one assertion focus | Kept, reworded | §6.2, "Each test checks one path" | §6.2 Rules, fifth bullet |
| §6.2 rule 3: no manual cleanup | Deleted | §6.1's rollback, and "its changes stay inside `workmain_test` and its `tmp_path`" | §6.1's bold rule; §6.2 Rules, second bullet |
| §6.2 rule 4: group in `class Test<Topic>` | Kept, merged | §6.2, "Related tests share a `Test<Topic>` class." | §6.2 Rules, fourth bullet |
| §6.2 rule 5: a plain class, and arguments | Kept, reworded | §6.2, the same rule; it no longer limits where a fixture is defined | §6.2 Rules, fourth bullet |
| §6.2 rule 6: `tmp_path` | Kept, merged | §6.2, "…its changes stay inside `workmain_test` and its `tmp_path`." | §6.2 Rules, second bullet |
| §6.2 rule 7: provider routing | Deleted | The same rule, which names `config/` | §6.2 Rules, second bullet |
| §6.2 rule 8: pin behaviour meant to stay | Moved | `docs/standards/1-workflow.md` §1.3 | `docs/standards/1-workflow.md:102` |
| §6.2 rule 9: a defect fix's test is seen to fail first | Moved | `.claude/skills/session-start/references/anvil.md` § Working rules | `anvil.md:43`; `_TEMPLATE_RESULTS.md` cites it |
| §6.2: converting a group replaces every test of its commands; editing for another reason doesn't convert; a new test is always this section's kind | Kept, shortened | §6.2, "Converting code to a new form replaces every test of it, in whichever file it is." | §6.2, the sentence after the five bullets |
| §6.2: Service | Kept, reworded | §6.2, "Behaviour", with `fake_uow` | §6.2, first bullet; `fake_uow` in `tests/conftest.py` |
| §6.2: Repository fake | Moved | §6.2, "SQL", and `tests/mocks/fake_unit_of_work.py`'s module docstring | §6.2, second bullet; module docstring, second paragraph |
| §6.2: Repository loading | Kept, shortened | §6.2, "SQL". The step-by-step procedure is deleted. | §6.2, second bullet, last sentence |
| §6.2: Renderer | Kept, shortened | §6.2, "Printed text", which also takes the Command bullet's `Error:` line | §6.2, fourth bullet |
| §6.2: Click parameter types | Deleted | §6.2's rule, "Each piece of logic is tested in the layer that owns it", covers it | §6.2's bold rule |
| §6.2: Command | Kept, reworded | §6.2, "A command": one test per path. `mix_stderr=False` and `obj=renderer` are deleted. | §6.2, third bullet |
| §6.2: the `run_workmain` second entry path | Deleted | §6.2's rule, "Each piece of logic is tested in the layer that owns it" | §6.2's bold rule |

### AC3.3 run

```text
SKIPPED [1] tests/test_ai_providers_live.py:32: ANTHROPIC_API_KEY not set
SKIPPED [1] tests/test_ai_providers_live.py:53: GOOGLE_API_KEY not set
SKIPPED [1] tests/test_ai_providers_live.py:84: ANTHROPIC_API_KEY not set
SKIPPED [1] tests/test_ai_providers_live.py:84: GOOGLE_API_KEY not set
SKIPPED [1] tests/test_ai_providers_live.py:94: ANTHROPIC_API_KEY, GOOGLE_API_KEY not set
======================== 5 skipped, 2 warnings in 1.11s ========================
```

### AC3.4

Run from the repository root:

```python
import inspect, re, subprocess, sys
spec = open('docs/dev/specs/TESTING_STANDARD_RULES_SPEC.md').read()
step3 = spec[spec.index('### Step 3'):spec.index('### Step 4')]
blocks = re.findall(r'```python\n(.*?)```', step3, re.S)
def doc(block):
    return inspect.cleandoc(re.search(r'"""(.*?)"""', block, re.S).group(1))
expected = {'_test_database': doc(blocks[0]), '_isolated_database': doc(blocks[1]),
            'db_session': doc(blocks[2]), 'fake_uow': doc(blocks[3])}
out = subprocess.run(['pytest', '--fixtures', '-v', '-p', 'no:cacheprovider'],
                     capture_output=True, text=True).stdout.split('\n')
ok = True
for name, want in expected.items():
    i = next(k for k, l in enumerate(out) if re.match(rf'^{name}\b.*conftest\.py', l))
    got = []
    for l in out[i + 1:]:
        if l and not l.startswith(' '):
            break
        got.append(l[4:] if l.startswith('    ') else l.strip())
    while got and not got[-1]:
        got.pop()
    same = got == want.split('\n')
    ok &= same
    print(f'{name}: {"equal" if same else "DIFFERENT"} ({len(got)} lines)')
sys.exit(0 if ok else 1)
```

```text
_test_database: equal (8 lines)
_isolated_database: equal (18 lines)
db_session: equal (10 lines)
fake_uow: equal (4 lines)
```

### AC6.2

```bash
gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --json number,body | python3 -c '
import json,re,sys
for i in json.load(sys.stdin):
    if i["number"]==285: continue
    b=i["body"] or ""
    if "6-testing.md" not in b and "§6" not in b: continue
    for m in re.finditer(r"(?<![Dd]esign )\b[Rr]ule [0-9]+\b",b): print(i["number"],m.group(0))
'
```

Before Step 5 it printed 7 matches in #287 and 4 in #288. After Step 5 it printed nothing.

### Issue body diffs (Step 5)

Each body was read with `gh issue view <N> --json body --jq .body` and checked to be non-empty (#287: 2,812 bytes; #288: 2,725). It was edited in a file and written with `gh issue edit <N> --body-file`, then read back. The read-back equals the edited file byte for byte. `diff` of the original against the read-back:

Issue #287:

```diff
5c5
< `docs/standards/6-testing.md` §6.2 rule 5: "A test is a method of a plain class, and it takes what it needs as arguments. [...] anything else it needs, it builds in its own body." Some tests depend on a fixture they do not name as an argument, so a reader of the test body cannot see setup the test relies on. Measured on `origin/main` `54599de`, 20261114, with an AST walk over `tests/test_*.py`:
---
> `docs/standards/6-testing.md` §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments", as it read on 20261114: "A test is a method of a plain class, and it takes what it needs as arguments. [...] anything else it needs, it builds in its own body." Some tests depend on a fixture they do not name as an argument, so a reader of the test body cannot see setup the test relies on. Measured on `origin/main` `54599de`, 20261114, with an AST walk over `tests/test_*.py`:
7c7
< - **Autouse fixtures in a test file:** 2. `_no_writes` (`tests/test_ai_costs.py:749`, class `TestCostReads`) makes `AiCostRepository.create` and `.link_report` raise for every test in the class. `_no_editor` (`tests/test_notes_log.py:198`, class `TestNotesLogUnitOfWork`) deletes `EDITOR` for every test in the class. Both use `monkeypatch`. Neither sets an attribute on `self`, which is the autouse form rule 5's reason already rules out.
---
> - **Autouse fixtures in a test file:** 2. `_no_writes` (`tests/test_ai_costs.py:749`, class `TestCostReads`) makes `AiCostRepository.create` and `.link_report` raise for every test in the class. `_no_editor` (`tests/test_notes_log.py:198`, class `TestNotesLogUnitOfWork`) deletes `EDITOR` for every test in the class. Both use `monkeypatch`. Neither sets an attribute on `self`, which is the autouse form that rule's reason, as it read on 20261114, already ruled out: "pytest hands a fixture only to a test that names it as an argument".
12c12
< Rule 5 says nothing about either form, so whether the rule should name them or the tests should build the setup in their bodies is undecided. The design study for this issue measures again rather than taking the lists above (`docs/standards/1-workflow.md` §1.2), and settles each form one of those two ways.
---
> That rule, as it read on 20261114, said nothing about either form, so whether the rule should name them or the tests should build the setup in their bodies is undecided. The design study for this issue measures again rather than taking the lists above (`docs/standards/1-workflow.md` §1.2), and settles each form one of those two ways.
16,19c16,19
< - Every fixture a test in tests/ depends on is one it names as an argument, or one docs/standards/6-testing.md §6.2 rule 5 states a test may depend on without naming
<   - Checked by: `python3 -c "import ast,pathlib; [print(f'{p}:{n.lineno} {n.name}') for p in sorted(pathlib.Path('tests').rglob('test_*.py')) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) for d in n.decorator_list if 'usefixtures' in ast.unparse(d) or ('fixture' in ast.unparse(d) and 'autouse=True' in ast.unparse(d))]"` printing only lines rule 5 states are allowed once this issue's design is settled (9 lines on 20261114)
< - Rule 5 states, for an autouse fixture and for a usefixtures mark, whether a test may depend on it without naming it
<   - Checked by: a stated reading by Ray of docs/standards/6-testing.md §6.2 rule 5, for whether a test author knows from it alone whether a test may get setup from a fixture it does not name
---
> - Every fixture a test in tests/ depends on is one it names as an argument, or one docs/standards/6-testing.md §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments" states a test may depend on without naming
>   - Checked by: `python3 -c "import ast,pathlib; [print(f'{p}:{n.lineno} {n.name}') for p in sorted(pathlib.Path('tests').rglob('test_*.py')) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) for d in n.decorator_list if 'usefixtures' in ast.unparse(d) or ('fixture' in ast.unparse(d) and 'autouse=True' in ast.unparse(d))]"` printing only lines that rule states are allowed once this issue's design is settled (9 lines on 20261114)
> - §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments" states, for an autouse fixture and for a usefixtures mark, whether a test may depend on it without naming it
>   - Checked by: a stated reading by Ray of docs/standards/6-testing.md §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments", for whether a test author knows from it alone whether a test may get setup from a fixture it does not name
```

Issue #288:

```diff
1c1
< Split from #286's design study (`docs/dev/design/DESIGN_TEST_ARGUMENTS.md`, Q3), Ray 20261114. Rule 5 stays as written; the tests change.
---
> Split from #286's design study (`docs/dev/design/DESIGN_TEST_ARGUMENTS.md`, Q3), Ray 20261114. The rule that a test is a method of a plain class stays; the tests change.
5c5
< `docs/standards/6-testing.md` §6.2 rule 5: "A test is a method of a plain class [...]". Rule 4 adds why: "Group related tests in `class Test<Topic>` so `-k TestTopic` works." 86 tests are functions at module level instead. Measured on `origin/main` `54599de`, 20261114, by reading the top-level body of every `tests/test_*.py` for a function whose name starts with `test`:
---
> `docs/standards/6-testing.md` §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments", which also says "Related tests share a `Test<Topic>` class." 86 tests are functions at module level instead. Measured on `origin/main` `54599de`, 20261114, by reading the top-level body of every `tests/test_*.py` for a function whose name starts with `test`:
21c21
< The 60 tests in `unittest.TestCase` classes also break rule 5, and are not part of this issue: the command-group issues under #198 convert them.
---
> The 60 tests in `unittest.TestCase` classes also break that rule, and are not part of this issue: the command-group issues under #198 convert them.
```

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #285 body | Restate AC1.1, AC2.1, AC6.1, AC6.2, AC7.1 and AC7.2 as the spec's §5 states | Close-out makes the edit (`docs/standards/1-workflow.md` §1.2) |

# Testing Standard Rules — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261117
**Branch:** `hotfix/issue-285-testing-standard-rules` (from `main`)
**Target release:** set by `/closeout`
**Originating item:** Issue #285
**Design study:** `../design/DESIGN_TESTING_STANDARD_RULES.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261116 | Ray | Branch type: `hotfix/*`. | Adopted; header. |
| 20261117 | Ray | #285 adds no exceptions. A rule's apparent exception either follows from the section's governing rule, or is temporary non-compliance, which the open issue that removes it tracks and which is never written into the standard. | Withdrawn by Ray, 20261117 (row below). |
| 20261117 | Ray | Design study Q1: Option C. Each record test drops its later-scope block, and `tests/test_clockify_service.py` drops `_fail_a_later_scope`. §6.1 states that the fixture can't show a record surviving its caller's failure: the `record_scope` spy is the evidence for that property, and the read through `db_session` is the evidence that the record was written. The issue's first criterion is restated, and the issue body is edited at close-out. | Adopted; DR4, Step 2, AC1.1. The statement is now §6.2's Outside-action record bullet (row below). |
| 20261117 | Ray | The `get_db()` guidance is derived from the rule the isolation follows and from the rule on test arguments, with no exception by kind. The issue's second criterion becomes: every `get_db()` call in `tests/` either complies with §6.1, or is in a test an open issue converts, and the results table names that issue for each such hit. | The restated criterion stands (AC2.1). The derivation went with the restructure, Ray 20261117 (row below). |
| 20261117 | Ray | Design study Q2: Option A. The defect-fix rule moves to §6's opening, next to the rule on recorded test evidence. | Overridden by Ray, 20261117 (row below). |
| 20261117 | Ray | Design study Q3, Q6 and Q7: §6's opening states one principle for every test, *A test's result depends only on what it sets up, and it changes nothing outside the suite's own database and temporary directories.* "Temporary directories" means `tmp_path` and pytest's base directory for it. §6.1 states how the database meets the principle, and presents the per-test rollback as how the suite keeps the first half true for every test without each test cleaning up, not as a rule of its own. Provider routing, the Renderer's width and the database isolation follow from the principle. | Replaced by Ray, 20261117 (row below): the principle survives as a §6.2 rule. |
| 20261117 | Ray | Design study Q4: Option A. §6.2's table has rows only for the forms it states today, and code of a kind it doesn't name is tested by the principle. | Moot, Ray 20261117: there is no table (row below). |
| 20261117 | Ray | Design study Q5: Option A, `hotfix/*` with the patch release. The §2.2 gap is #291. | Adopted; header, §1 Out of scope. |
| 20261117 | Ray | Each test that depends on something it doesn't set up goes to the one issue that removes the dependence: #207, #214, #288 or #292. #285 changes none of them. | Adopted; §1 Out of scope. |
| 20261117 | Spanner | The issue names four later-scope sites. The census finds six tests: `tests/test_clockify_service.py`'s helper `_fail_a_later_scope` serves three (`test_s17_the_link_survives_a_later_failed_scope`, `test_s26_a_link_survives_a_later_failed_scope`, `test_s28_an_import_survives_a_later_failed_scope`). | Adopted; §2, Step 2. |
| 20261117 | Spanner | Each of the six test names says "survives a later failed scope", which is no longer what the test does. Each test is renamed, and its docstring reworded where it has one, to say what it checks. | Adopted; DR4, Step 2. |
| 20261117 | Spanner | The defect-fix rule doesn't apply to this work. #285 is labelled `gap`, not `defect`, so no test is run before a fix. | Adopted; Step 6. |
| 20261117 | Spanner | Rule 6's "the suite leaves nothing behind" is false: pytest keeps three sessions' `tmp_path` directories (design study F18). It is dropped, because the principle now says what a test may leave. | Moot: Ray's §6 text replaces rule 6 (row below). |
| 20261117 | Spanner | The issue's sixth criterion's search covers `.md` files only and finds "§6.2 rule N", but not the bare "Rule 4" in #288. It also matches this spec and its design study, which record the old numbers as history. Restated as AC6.1 and AC6.2. | Adopted; §5. |
| 20261117 | Spanner | The issue's seventh criterion diffs against `origin/dev`. This branch is cut from `origin/main` (design study F11). Restated as AC7.1, and AC7.2 is added to show the tests still check what they checked. | Adopted; §5. Ray, 20261117, widened AC7.1's file list (row below). |
| 20261117 | Spanner | The issue lists the child-process launch among the recipes. Patching the launch is required, not optional, because a child process leaves the transaction. It is stated in §6.1 as following from the principle, not as a recipe. | Moot: Ray's §6 text replaces the restructure (row below). |
| 20261117 | Ray | "#285 adds no exceptions" is withdrawn. It produced rewordings of exceptions rather than removing them. What stays is that temporary non-compliance is tracked in the issue that removes it, and is not written into the standard. | Adopted; §1 Out of scope. |
| 20261117 | Ray | Design study Q2 is overridden. The defect-fix rule leaves §6 entirely. It governs how the implementer works, so its one home is `.claude/skills/session-start/references/anvil.md` § Working rules. | Adopted; Step 5. |
| 20261117 | Ray | The restructure is replaced by Ray's own `docs/standards/6-testing.md`, used verbatim, with no rewording, reordering or addition. A question about its text is a departure, and goes to Ray. The §6 principle, the §6.2 layer table, the recipes and the "follows from" derivations are dropped. Q3, Q6 and Q7's principle survives as the §6.2 rule "A test's result depends only on what it sets up, and its changes stay inside `workmain_test` and its `tmp_path`". The provider-routing recipe is dropped. Q4 is moot. Q1 and Q5 stand. | Adopted; DR1, Step 1. |
| 20261117 | Ray | Fixture mechanics live in the fixtures' docstrings, which `pytest --fixtures -v` shows. A docstring describes what the code does and states no rule (`docs/standards/3-code.md` §3.1). | Adopted; DR5, Step 3, AC3.4, AC3.5. |
| 20261117 | Ray | §6.1 keeps only its rule and two bullets. "Everything a test reaches stays on the test's connection" covers the session order, the child process, the thread and the separate engine. The session-order explanation is in `_isolated_database`'s docstring. | Adopted; Step 1, Step 3. |
| 20261117 | Ray | The record test moves to §6.2 as the Outside-action record bullet. | Adopted; Step 1, Step 5 (`docs/standards/4-database.md:68`). |
| 20261117 | Ray | The §6.2 example is removed. It broke `ANN201`, implied a docstring requirement that the config turns off, and hid each fake's row shape. | Adopted; Step 1. |
| 20261117 | Ray | A test seeds as models added to `db_session`, or into `fake_uow`'s store. It does not seed through repositories or services. | Withdrawn by Ray, 20261117, answering Caliper's blocking finding on seeding (row below). |
| 20261117 | Ray | "A test pins behaviour meant to stay" moves to `docs/standards/1-workflow.md` §1.3. | Adopted; Step 5. |
| 20261117 | Ray | Config enforces what can be enforced: `--strict-markers` and `-rs`. Measured clean on 20261117: 1707 collected under `--strict-markers`, 0 skips in a full run, and no `pytest.skip(` or `mark.skip(` in `tests/`. | Adopted. Ray committed the `addopts` line himself at `8932582`, so Step 4 only deletes the comment line. AC3.3. |
| 20261117 | Ray | #288's "Rule 4" maps to "A test is a method of a plain class, and it takes what it needs as arguments", because the two rules merged. Rule 5's requirement changed (corrected by Ray, 20261117, answering question 1): it no longer limits where a fixture is defined, and it still requires a test to take its fixtures as arguments. #287's `autouse` and `usefixtures` cases remain non-compliant under the new text, because their tests do not take those fixtures as arguments. | Adopted; Step 5. |
| 20261117 | Ray | AC3.1 is the results artifact's table of where each old statement went (kept, moved with its new home, or deleted with its reason). AC4.1 reads the Command bullet. AC5.1 is deleted. AC7.1 adds `tests/conftest.py` and `tests/mocks/fake_unit_of_work.py`. New criteria: §6 has fewer words; `pytest` passes with the new `addopts`; `pytest --fixtures -v` shows the four fixtures' new docstrings; and no new or changed docstring gives an instruction. | Adopted; §5. |
| 20261117 | Spanner | The design study has no Decision Log: `docs/standards/1-workflow.md` §1.5 gives design artifacts none. Ray's overrides are recorded in the study's §5 answers and §6 Disposition instead. | Adopted. |
| 20261117 | Spanner | §1.3 has a run of bullets on opening an issue. The rule on narrowing behaviour goes after "An issue is opened when its body is written, it is on the board, and its dependencies are linked.", with its first sentence in bold like its neighbours. | Adopted; Step 5. |
| 20261117 | Spanner | Ray's word counts are 1,872 old and 633 new. The 633 includes the three §6.3 lines; everything before `### 6.3` in the new file was 626 words, and is 660 with Ray's answers and rulings of 20261117. AC3.2 counts both files before `### 6.3`. | Adopted; AC3.2. |
| 20261117 | Spanner | With no skips, `-rs` prints nothing, and pytest's last line leaves out a zero skip count. "Its summary shows the skip count" can only be shown on a run that skips. AC3.3 checks the config, and shows a forced skip reported with its reason. | Adopted; AC3.3. |
| 20261117 | Spanner | #292's body called the rule "a principle for every test" in §6. It is a §6.2 rule. Corrected in #292's body, 20261117. | Done. |
| 20261117 | Spanner | Ray's text, question 1: the old rule 5 limited where an argument may come from to a fixture pytest provides, a fixture in `tests/conftest.py`, or a `parametrize` mark. The new text, "A test takes its fixtures and `parametrize` values as arguments", doesn't say where a fixture may be defined, so a fixture defined in a test file now complies. That widens the requirement. Two such fixtures exist (`_no_writes`, `tests/test_ai_costs.py:750`; `_no_editor`, `tests/test_notes_log.py:200`), both #287's. **Option A:** the wider requirement is intended, and #287 is re-read against it. **Option B:** the text names where a fixture may come from, as rule 5 did. Recommendation: B. Ray recorded the requirement as unchanged, and #286 delivered against the narrower one. | Ray, 20261117: Option A. The widening is intended. A fixture defined in a test file complies when the test takes it as an argument. |
| 20261117 | Spanner | Ray's text, question 2: "Printed text is read only by renderer tests" forbids what the old Command bullet allowed, "an `Error:` line on `result.stderr`". 22 assertions in 10 test files read that line, including command tests already in the converted form (`tests/test_clients_commands.py`, `tests/test_calendar.py`). No open issue would remove them. **Option A:** the Printed text bullet allows a command test the `Error:` line on `result.stderr`. **Option B:** the 22 become non-compliance, and an issue is opened to remove them. Recommendation: A. The error wiring is checked once in the renderer, and the command test checks only that it reached it. | Ray, 20261117: Option A. The Printed text bullet allows a command test the `Error:` line on `result.stderr`; Step 1. |
| 20261117 | Spanner | Ray's text, question 3: `db_session`'s docstring says "get() and attribute access return those objects as they were when loaded". The fixture's sessionmaker keeps the default `expire_on_commit=True`, so after `db_session.commit()`, which the same docstring invites, or after `expire_all()`, attribute access reads the current row. A probe renamed a client from another session: before any expiry the attribute, `get()` and a query all returned the old name; after a commit, or after `expire_all()`, the attribute returned the new one. **Option A:** "…return those objects as they were when loaded, until db_session commits or expire_all() is called; after that, they are read from the rows again, as a query after expunge_all() is". **Option B:** keep the text as given. Recommendation: A. A docstring that is wrong about what the code does breaks `docs/standards/3-code.md` §3.1. | Ray, 20261117: Option A, worded "until db_session commits or expire_all() is called, get() and attribute access return those objects as they were when loaded"; Step 3. |
| 20261117 | Spanner | Ray's text, question 4: two tests reach a connection outside the test's: `tests/test_database_isolation.py::TestTestDatabaseBuild::test_the_build_empties_the_schema_and_upgrades_to_head` builds its own engine, and `::test_a_run_builds_the_database_before_its_first_test` also runs a child `pytest`, which connects and rebuilds the database. "Everything a test reaches stays on the test's connection" refuses both, and neither is temporary: the build can't run inside the transaction. **Option A:** §6.1 states that a test of the build itself reaches it on a connection of its own and leaves the schema as it found it. **Option B:** the tests move to a suite of their own, as non-application suites already are. **Option C:** leave the text, and the two tests stand as unstated non-compliance. Recommendation: A. It is one clause, and the build is the only code that must run outside the transaction. | Ray, 20261117: Option A, as the rule's reason, not an exception: tests of the database build are the only ones that run outside the test's connection, because the build comes before the transaction, and they undo what they change; Step 1. |
| 20261117 | Caliper | 3, Spec defect, blocking: Step 2 renames six `def` lines, and `automation/style_check.py` checks every changed line with ruff. `tests/**` ignores only D101–D103, so each renamed line is reported for ANN201 and ANN001. Ruff at `c2f0118` reports both on `tests/test_ai_costs.py:627`, `tests/test_clockify_service.py:330`, `:497`, `:557`, `tests/test_gdrive.py:261` and `tests/test_slack.py:585`, which is 12 violations. `references/anvil.md` § Working rules step 5 says a style violation "is fixed before the commit". The fix is `db_session: Session` and `-> None`, plus a `Session` import where a file has none. That conflicts with Step 2's "No other line in the four files changes." and with DR4. The implementer either stops at every Step 2 commit or guesses. | Accepted. Step 2 adds `db_session: Session` and `-> None` to each renamed `def` line, and `from sqlalchemy.orm import Session` to each of the four files, none of which has it. DR4 now says every line Step 2 changes passes `automation/style_check.py`. |
| 20261117 | Caliper | 3, Spec defect, blocking: AC2.1 and Step 6 match every `get_db()` hit to "the §6.1 statement it complies with", an open issue, or "not a call". The new §6.1 has two bullets, and neither covers several call sites. The first is the three fixture calls in `tests/conftest.py` (`:88`, `:135`, `:176`). These are calls, and no test is in them. The second is the 13 calls in `tests/test_unit_of_work.py`. The third is the non-build calls in `tests/test_database_isolation.py` (`:47` `get_db().get_session()`, `:59`, `:69`, `:76`, `:100`). §6.1's only carve-out is for tests of the database build. The derivation that placed these calls (design study F14: (a) conftest, (b)/(c) "a test calling what it tests") was dropped with the restructure (Decision Log row "The `get_db()` guidance is derived…": "The derivation went with the restructure"). The implementer has to invent the mapping. | Accepted. AC2.1 and Step 6 name the categories a hit is matched to: the suite's own setup in `tests/conftest.py`; a test whose code under test is the connection or the session machinery; a test of the database build; a test an open issue converts; or not a call. This is Spanner's reading of §6.1's text, not a derivation added to the standard, and Ray can reverse it. |
| 20261117 | Caliper | 2, Design gap, blocking: §1 Out of scope says "Each test that doesn't meet the new text is temporary non-compliance, owned by the issue that removes it". It names owners only for `TestCase` setups, width and untracked dependences. The new §6.2 seeding rule ("does not seed through repositories or services", Decision Log, Ray 20261117) was never run over `tests/`, and §2 has no census for it. Two of the six tests this spec rewrites already break it: `test_s17_…` and `test_s26_…` seed through `_seed_entry`, which calls `notes_service.create_note` (`tests/test_clockify_service.py:68`). DR4 keeps every seed as it is. A rough search for seeding through a repository or service (`Repository(db_session)`, `_service.create_*(session)`) matches 40 test files. Ray's rule (Decision Log, "What stays is that temporary non-compliance is tracked in the issue that removes it") needs an owner for this non-compliance, or the six tests need to comply. Ray rules. | Ray, 20261117: Option C. The decision that a test does not seed through repositories or services is withdrawn. The rule reads "**A test seeds the rows it needs**: on `db_session` for the database, or into `fake_uow`'s store, in the row shape its fake repository's docstring describes." No new issue; Step 2 leaves seeds unchanged. Step 1. |
| 20261117 | Caliper | 8, Spec defect, non-blocking: DR3 says every old statement is kept, moved, or deleted with a reason. Four rows of the Step 1 table say "Moved" or "Kept" for text whose substance is not in the stated home. **(1)** The rollback row: "and every commit a session opened after it made in the meantime" is not in Step 3's `_isolated_database` docstring, which says only "rollback() returns to one". **(2)** "Hand application code a session only before…": the remedy, the error name `InvalidSavepointSpecification` and the `TestMeetingsCondenseTokenLine` example are in no home. **(3)** Old §6.1 bullet 1: "The rest of the connection comes from `.env`" and the `(§4.5)` citation are in no row and in no docstring. **(4)** The Command row: "with nothing patched" is in neither the new Command bullet nor the row's reason. | Accepted. The four rows now say what is kept, and what is deleted and why. |
| 20261117 | Caliper | 5, Spec defect, non-blocking: Step 3's `db_session` docstring says the identity map returns objects "as they were when loaded" "until db_session commits or expire_all() is called". `db_session.rollback()` expires them too. A probe on `workmain_test` loaded a client, called `db_session.rollback()`, renamed the row from another session, and then read the attribute: it returned the new name (`probe-b`). DR5 requires the docstring to say what the code does. | Ray, 20261117: accepted, worded "until db_session commits, rolls back or expire_all() is called". Step 3. |
| 20261117 | Caliper | 8, Spec defect, non-blocking: §2 says "After Step 2, `tests/test_clockify_service.py` and `tests/test_gdrive.py` name `get_db` only in their import". Step 2's "Remove any import the deletion leaves unused" removes that import: the module-level `get_db` at `:18` in both files has no other use. The same holds for `tests/test_slack.py:36`, whose only other `get_db` is the local import at `:413`. | Accepted. §2 is corrected: after Step 2, `get_db` is unused at module level in all three files, and Step 2's removal of unused imports takes it out of each. |
| 20261117 | Caliper | 7, Spec defect, non-blocking: AC3.4's criterion is that the fixtures show "the docstrings Step 3 states". The check records only the first line of each. `pytest --fixtures -v` prints the whole docstring (observed for `_isolated_database` and `db_session` at `c2f0118`), so a body that departs from Step 3's text still passes. | Accepted. AC3.4 compares each fixture's whole docstring with Step 3's text. |
| 20261117 | Caliper | 1, Spec defect, non-blocking: AC1.1's criterion has two halves: "states how a test of an outside-action record is written" and "that form opens no session through `get_db()`". Its check, Ray reading whether "a test author knows from it alone how to write a record test", tests only the first. The Outside-action record bullet does not mention `get_db()`. | Accepted. AC1.1's check reads both halves, and a search shows that no record test names `get_db`. |
| 20261117 | Caliper | 8, Spec defect, non-blocking: Step 5's mapping turns #288's "Rule 4 adds why: \"Group related tests in `class Test<Topic>` so `-k TestTopic` works.\"" into the merged rule giving a reason for itself, quoting a sentence §6 no longer holds. #287's "rule 5's reason" (body line 7) would name a reason the new rule does not state. "A grammatical form … becomes the same form of the name" doesn't settle either case. | Accepted. Step 5 states each of the eleven replacements exactly. Where the old text gave a reason the new rule does not state, the replacement says how the rule read on 20261114. |
| 20261117 | Caliper | Pass at c2f0118, full: 42 items checked, 3 blocking, 6 non-blocking. | n/a |
| 20261117 | Caliper | 3, Spec defect, non-blocking: Step 6's second category ("A test whose code under test is the connection or the session machinery: `get_db()`, `session_scope()`, `record_scope()`, `DatabaseConnection.close()` or the connection's URL") justifies itself with "The call is that code." That is not true of five hits: `tests/test_unit_of_work.py:195`, `:222`, `:234`, `:246` and `:252`. In each, the `get_db().session_scope()` call is setup. It opens a scope so the test can check whether `UnitOfWork` is refused or enters (`TestUnitOfWork::test_refused_by_open_scope_check_enters_after_scope_closes`, `test_refused_in_open_scope_opens_no_session`, and `TestOpenScopeCheck`). The code under test is `UnitOfWork`, which the category's list doesn't name. No other category fits: no open issue names `tests/test_unit_of_work.py`, and these are not tests of the build. The implementer would place these five hits under category 2 even though its stated reason doesn't hold for them. The rest of the category's reasoning does hold: the scope joins the transaction (§6.1's first bullet). | Accepted. Step 6's second category names `UnitOfWork`'s check for an open scope, and says the call is either the code under test or the scope that check's test opens. |
| 20261117 | Caliper | Pass at 6596651, changes since c2f0118: 24 items checked, 0 blocking, 1 non-blocking. | n/a |
| 20261117 | Caliper (post-implementation) | No findings. | n/a |

---

## 1. Scope

**In scope:**

- `docs/standards/6-testing.md`: everything before `### 6.3 Placement`, replaced by Ray's text in Step 1, verbatim.
- The six record tests that fail a later scope, and the helper three of them use (Step 2): `tests/test_ai_costs.py`, `tests/test_clockify_service.py`, `tests/test_gdrive.py`, `tests/test_slack.py`.
- Fixture and fake docstrings, and a new fixture `fake_uow` (Step 3): `tests/conftest.py`, `tests/mocks/fake_unit_of_work.py`. Owner: `tests/conftest.py` holds the suite's shared fixtures (`docs/standards/7-file-placement.md` §7 places tests and their fixtures, and `docs/ARCHITECTURE.md` covers only the application). `fake_uow` is a test fixture, not application code.
- `pyproject.toml`: the comment line above `"tests/**" = ["D101", "D102", "D103"]` (Step 4).
- The rules that leave §6, and every citation of a §6 rule by number (Step 5): `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/standards/4-database.md`, `docs/standards/1-workflow.md` §1.3, and the bodies of #287 and #288.

**Out of scope:**

- What any test requires beyond the six record tests. Each test that doesn't meet the new text is temporary non-compliance, owned by the issue that removes it: the `TestCase` setups by #208, #209, #212, #214 and #216; the width dependences by #198; the other untracked dependences by #207, #214, #288 and #292 (design study § Who removes each untracked dependence).
- The recording renderer fixture and its docstring: #279.
- `docs/standards/2-git.md` §2.2: #291.
- The edit to #285's own body, which `docs/standards/1-workflow.md` §1.2 leaves to close-out.
- Any file under `workmain/`, `config/` or `templates/`.

## 2. Verified current state

On `hotfix/issue-285-testing-standard-rules` at `8932582`, 20261117. Its `tests/` and `workmain/` are `origin/main` `bd9b0dc`'s.

| Claim | Evidence |
| --- | --- |
| `docs/standards/6-testing.md` is §6's opening (lines 1–13), §6.1 (15–35), §6.2 (37–76) and §6.3 (78–80). Everything before `### 6.3` is 1,872 words. Ray's replacement is 660 words before `### 6.3`. | `docs/standards/6-testing.md`; `sed '/^### 6.3/,$d' docs/standards/6-testing.md \| wc -w` |
| Six tests fail a later scope after calling a function that writes an outside-action record, and each wraps the call in a `record_scope` spy: `tests/test_ai_costs.py::TestAiCostService::test_record_reply_survives_a_later_failed_scope` (`:627`, scope at `:645-648`, `spy.assert_called_once()`); `tests/test_gdrive.py::TestDriveUploadRecord::test_t18_record_survives_a_later_failed_scope` (`:261`, scope at `:272-275`, `spy.assert_called_once()`); `tests/test_slack.py::TestSlackPostRecord::test_t19_record_survives_a_later_failed_scope` (`:585`, scope at `:601-605`, `spy.assert_called_once()`); `tests/test_clockify_service.py::TestPush::test_s17_the_link_survives_a_later_failed_scope` (`:330`), `::TestPull::test_s26_a_link_survives_a_later_failed_scope` (`:497`) and `::TestPull::test_s28_an_import_survives_a_later_failed_scope` (`:557`), each calling `_fail_a_later_scope()` (`:107-112`) and asserting `spy.assert_called()`. Only the first has a docstring, and it describes the later scope. | `pytest --collect-only -q \| grep later_failed_scope`; `grep -n "_fail_a_later_scope\|later" tests/test_clockify_service.py tests/test_ai_costs.py tests/test_gdrive.py tests/test_slack.py` |
| Under the fixture, failing a later scope can't change whether a record test passes. | design study F2 (probe) |
| After Step 2's deletions, the module-level `get_db` import has no use in `tests/test_clockify_service.py` (`:18`), `tests/test_gdrive.py` (`:18`, whose other mention, `:236`, is a string patch target) or `tests/test_slack.py` (`:36`, whose other `get_db` is a local import at `:413`, in a `TestCase` setup). None of the four files imports `Session`. Ruff reports `ANN001` and `ANN201` on each of the six `def` lines Step 2 renames. | `grep -n "get_db" tests/test_clockify_service.py tests/test_gdrive.py tests/test_slack.py`; `ruff check --select ANN` on the four files |
| `git grep -n 'get_db()' tests/` prints 49 lines in six kinds. Step 2 removes the four record-test lines, leaving 45. | design study F3 |
| `tests/conftest.py`'s docstrings for `_test_database` (`:113`), `_isolated_database` (`:119-128`) and `db_session` (`:168-173`) are the ones Step 3 replaces. | `tests/conftest.py` |
| The fixture's sessionmaker sets no `expire_on_commit`, so it is `True`. After `db_session.commit()` or `expire_all()`, attribute access reads the current row. | `tests/conftest.py` `_isolated_database` `sessionmaker(...)`; probe 20261117 (Decision Log, question 3) |
| Importing `tests.mocks.fake_unit_of_work` imports `workmain.database.connection`, which reads `DB_NAME` when it is first imported (`workmain/database/connection.py:36`). A top-level import in `tests/conftest.py` would read it before `pytest_configure` sets it. | `python -c "import tests.mocks.fake_unit_of_work, sys; print('workmain.database.connection' in sys.modules)"` printing `True` |
| `tests/mocks/fake_unit_of_work.py`'s module docstring is the first paragraph of the Step 3 text. The second paragraph's claims hold: each fake repository takes the store and keeps its rows under its table's name (`FakeSystemStateRepository.__init__`); `REPOSITORIES` uses `UnitOfWork.REPOSITORIES`'s names (`TestFakeParity::test_repository_names_are_real`); signatures are checked (`TestFakeParity::test_fake_methods_exist_on_real_with_equal_signatures`); and contract tests run against both (`TestSystemStateContract`, parametrized over `real` and `fake`). | `tests/mocks/fake_unit_of_work.py`; `tests/test_fake_unit_of_work.py` |
| `FakeUnitOfWork()` builds an empty store, and `.store` is the dict a second `FakeUnitOfWork(store=...)` shares. | `tests/mocks/fake_unit_of_work.py` `FakeUnitOfWork.__init__` |
| `pyproject.toml` holds `addopts = "--strict-markers -rs"` (Ray, `8932582`). Line 29 is the comment `# A test is named for what it checks; its name is its description (docs/standards/6-testing.md §6.2).`, above `"tests/**" = ["D101", "D102", "D103"]`. | `pyproject.toml:3`, `:29-30` |
| Under `--strict-markers` the suite collects 1707 tests. A full run skips none, and no `pytest.skip(` or `mark.skip(` is in `tests/`. | `pytest --collect-only -q`; `grep -rnE 'pytest\.skip\(\|mark\.skip\(' tests/` |
| `.claude/skills/session-start/references/anvil.md:43` is step 2 of § Working rules' "Each step runs in this order", and cites "§6.2 rule 9". `docs/dev/results/_TEMPLATE_RESULTS.md:63` cites "§6.2 rule 9". | `.claude/skills/session-start/references/anvil.md` § Working rules; `docs/dev/results/_TEMPLATE_RESULTS.md:63` |
| `docs/standards/4-database.md:68` reads "  - It is tested at the function that writes it (§6.1)." `:35` ("tests follow §6.1") and `:64` ("§6.2 states how the loading is tested") still resolve under Step 1. | `docs/standards/4-database.md` |
| `docs/standards/1-workflow.md` §1.3's bullets on opening an issue are "An issue is opened only for what no open issue already covers.", "An issue is opened when its body is written, it is on the board, and its dependencies are linked." and "An issue split by its design study takes its findings with it." | `docs/standards/1-workflow.md` §1.3 |
| Open issues that cite a §6 rule by number: #287, 7 times, and #288, 4 times. No other open issue does, apart from #285. | The AC6.2 command, run 20261117 |
| Open issues that cite §6.2's earlier forms by content, such as "one more for each flag that makes it call a different service function" (#205, #207–#216) and `tests/test_output.py`'s `TestWiring`, keep their text. An issue's criteria validate and do not design, and each conversion's spec restates them against the §6 it is written under (`docs/standards/1-workflow.md` §1.2). | `gh issue list` bodies, design study F6 |
| Suite: `1707 passed, 0 failed, 0 skipped`. | `CHANGELOG.md` 1.58.6; a bare `pytest`, 20261117 |

## 3. Design rules

- **DR1 — Ray's text is the standard.** Step 1's text replaces everything before `### 6.3`, verbatim. A question about its text is a departure, and goes to Ray.
- **DR3 — Every old statement has a place.** Each statement of the old opening, §6.1 and §6.2 is kept, moved to the home the Step 1 table names, or deleted for the reason it gives.
- **DR4 — A record test keeps what it checks.** Step 2 removes each test's later-scope block, and `_fail_a_later_scope` once nothing calls it, and renames the tests. Every assertion, spy, seed and call to the function under test stays as it is. Every line Step 2 changes passes `automation/style_check.py`.
- **DR5 — A docstring describes and instructs nothing.** Each docstring Step 3 writes says what the code does (`docs/standards/3-code.md` §3.1). The texts are Ray's, verbatim.

DR2 was withdrawn with the restructure (Decision Log). Anything this spec does not decide is a departure: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §6's opening, §6.1 and §6.2 replaced by Ray's text | `docs/standards/6-testing.md` |
| 2 | The six record tests without a later scope | `tests/test_ai_costs.py`, `tests/test_clockify_service.py`, `tests/test_gdrive.py`, `tests/test_slack.py` |
| 3 | Fixture docstrings, `fake_uow`, and the fake unit of work's module docstring | `tests/conftest.py`, `tests/mocks/fake_unit_of_work.py` |
| 4 | The `pyproject.toml` comment that cited §6.2 is deleted | `pyproject.toml` |
| 5 | The rules that left §6 have their homes, and no citation names a §6 rule by number | `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/standards/4-database.md`, `docs/standards/1-workflow.md`; the bodies of #287 and #288 |
| 6 | Results artifact | `docs/dev/results/TESTING_STANDARD_RULES_RESULTS.md` |

### Step 1 — the testing standard

In `docs/standards/6-testing.md`, replace everything from the line `## 6. Testing Standards` up to the line before `### 6.3 Placement` with the text below, followed by one blank line. `### 6.3 Placement` and what follows it are unchanged.

````markdown
## 6. Testing Standards

- pytest is the exclusive runner.
- **The application suite is a bare `pytest` from the repository root.** Any other run offered as the suite's result names the alternative and states why.
- Non-application suites, such as `pytest automation/`, are separate suites, each reached by its own path.
- **A test reports what actually happened.**
  - Passed means it ran to its end and its assertions held.
  - Failed means it ran and raised an error, timed out or gave a wrong answer.
  - Skipped means a precondition declared with `@pytest.mark.skipif` was absent, decided before the test exercises anything.
- **Recorded test evidence states all three counts, in the form `<passed> passed, <failed> failed, <skipped> skipped`, and writes each one even when it is zero**, so the record shows whether the whole suite ran.

### 6.1 Test isolation from the database

**Every test runs in `workmain_test`, inside one transaction that rolls back when the test ends.** The fixtures in `tests/conftest.py` build the database and hold the transaction, and `pytest --fixtures -v` shows how each one works.

- **A test seeds and reads through `db_session`.** Every session the code under test opens through `get_db()` joins the same transaction, so the test and the code see each other's writes.
- **Everything a test reaches stays on the test's connection.** Tests of the database build are the only ones that run outside it, because the build comes before the transaction, and they undo what they change.

### 6.2 Writing a test

**Each piece of logic is tested in the layer that owns it** (`docs/ARCHITECTURE.md` §1).

- **Behaviour** is tested at the service. The test calls the service function and asserts the result's fields or the exception it raises. A service that takes a unit of work gets `fake_uow`, a `FakeUnitOfWork`, and one that still takes a session gets `db_session`.
- **SQL** is tested at the repository, on `db_session`. Each fake repository method is tested against the real one, in a class parametrized over both, so the fake answers as the database does. A method that loads related records with its rows (§4.3) has a test that its statement count stays the same as its rows grow, with each row seeded with related rows of its own and `db_session.expunge_all()` called before counting, so a lazy load shows in the count.
- **A command** has one end-to-end test per path through it: each outcome of a flag, a prompt's answer or a pick. The test runs the command through `CliRunner` against the test's database, with a recording renderer, and asserts the exit code, what the renderer received, and the rows the path writes or leaves alone.
- **Printed text** is read only by renderer tests, at a width the test sets, and by a command test reading the `Error:` line on `result.stderr`.
- **An outside-action record** (§4.3) is tested at the function that writes it: a spy shows the function opened `record_scope()`, and the record is read through `db_session`. The spy stands for the record surviving its caller's failure, which only production shows.

Converting code to a new form replaces every test of it, in whichever file it is.

Rules:

- **A test's name says what it checks, and is its description.**
- **A test's result depends only on what it sets up, and its changes stay inside `workmain_test` and its `tmp_path`.** Anything it needs from `config/`, `.env`, `~/.workmain/`, the terminal's width or the network, it sets up itself.
- **A test seeds the rows it needs**: on `db_session` for the database, or into `fake_uow`'s store, in the row shape its fake repository's docstring describes.
- **A test is a method of a plain class, and it takes what it needs as arguments.** Related tests share a `Test<Topic>` class. A test takes its fixtures and `parametrize` values as arguments and builds everything else in its own body.
- **Each test checks one path**, with as many assertions as that path needs.
````

Where each old statement goes. The results artifact's §3 copies this table, with each row checked against the delivered files (AC3.1).

| Old statement | Status | Home, or reason |
| --- | --- | --- |
| Opening: pytest is the exclusive runner | Kept | §6 |
| Opening: the application suite is a bare `pytest`; `testpaths` resolves it; no other invocation stands in unless a spec names it and says why, including a path subset, a filter or an environment variable | Kept, shortened | §6: "Any other run offered as the suite's result names the alternative and states why." The `testpaths` mechanism and the list of alternatives are deleted; `pyproject.toml` holds the first, and "any other run" covers the second. |
| Opening: non-application suites; "§7 owns test placement" | Kept, shortened | §6. The pointer to §7 is deleted: `docs/standards/README.md`'s index names §7. |
| Opening: a test reports what actually happened | Kept, shortened | §6's three sub-bullets. "never reports passed without having run" is covered by "ran to its end". "only way a test is skipped" and "never reports skipped after it has run" are covered by the Skipped sub-bullet. "A skip is never added to turn a red suite green" is deleted: `-rs` reports every skip with its reason. |
| Opening: recorded evidence states all three counts | Kept, shortened | §6 |
| Opening: the command examples | Deleted | pytest's own usage; they state no rule |
| §6.1: the build from empty, the `DB_NAME` guard, `workmain_test`'s creation; "The rest of the connection comes from `.env`"; the `(§4.5)` citation | Moved, part deleted | `_test_database`'s docstring; §6.1's rule names `workmain_test`. Where the rest of the connection comes from, and the `(§4.5)` citation, are deleted: the connection settings belong to the application's configuration (`workmain/database/connection.py`), and §4.5 owns migrations, which the docstring names by its command. |
| §6.1: the transaction, `_isolated_database`, `join_transaction_mode` | Moved | §6.1's rule, and `_isolated_database`'s docstring |
| §6.1: every session through `get_db()` joins | Kept | §6.1, "A test seeds and reads through `db_session`." |
| §6.1: the table of commit, rollback, test end and process killed | Moved, part deleted | `_isolated_database`'s docstring: a commit releases a savepoint, a rollback returns to one, teardown discards every write, and a killed run is rolled back. Deleted: that a rollback also discards "every commit a session opened after it made in the meantime". That is SQLAlchemy's savepoint behaviour, and the docstring's last-in, first-out paragraph covers the case a test meets. |
| §6.1: take `db_session`; never call `get_db()` or `db.get_session()` in a test | Kept; ban deleted | §6.1 keeps `db_session`. The ban protects nothing under this fixture (design study F13). |
| §6.1: hand application code a session only before it opens its own | Moved, part deleted | `_isolated_database`'s docstring states the failure: an object built on `db_session` and handed to code that opens its own session fails at that code's commit. Deleted: the remedy, the error's name `InvalidSavepointSpecification`, and the `TestMeetingsCondenseTokenLine` example. The remedy is the converse of the failure the docstring states, and the error names itself when it is raised. |
| §6.1: a record committed inside another open transaction is discarded; the record test | Moved | §6.2, "An outside-action record" |
| §6.1: inject a database failure; never rely on one | Deleted | §6.2, "A test's result depends only on what it sets up", covers it |
| §6.1: leaving the transaction fails the test (`close()`, `SessionLocal`, own engine) | Moved | `_isolated_database`'s docstring; §6.1, "Everything a test reaches stays on the test's connection." The build's own tests are the one case outside it, and §6.1 gives the reason. |
| §6.1: the exceptions for `tests/test_database_isolation.py` and `tests/test_unit_of_work.py` | Deleted | Without the ban there is nothing to except |
| §6.1: a child process is outside the transaction | Deleted | §6.1, "Everything a test reaches stays on the test's connection." |
| §6.1: database work stays on the test's thread | Deleted | The same |
| §6.2: the example | Deleted | Ray's reasons (Decision Log) |
| §6.2 rule 1: take `db_session` | Moved | §6.1, "A test seeds and reads through `db_session`." |
| §6.2 rule 2: one assertion focus | Kept, reworded | §6.2, "Each test checks one path" |
| §6.2 rule 3: no manual cleanup | Deleted | §6.1's rollback, and "its changes stay inside `workmain_test` and its `tmp_path`" |
| §6.2 rule 4: group in `class Test<Topic>` | Kept, merged | §6.2, "A test is a method of a plain class…": "Related tests share a `Test<Topic>` class." |
| §6.2 rule 5: a plain class, and arguments | Kept, reworded | §6.2, the same rule. Its requirement changed: it no longer limits where a fixture is defined (Decision Log, question 1). |
| §6.2 rule 6: `tmp_path` | Kept, merged | §6.2, "A test's result depends only on what it sets up, and its changes stay inside `workmain_test` and its `tmp_path`." |
| §6.2 rule 7: provider routing | Deleted | The same rule, which names `config/` |
| §6.2 rule 8: pin behaviour meant to stay | Moved | `docs/standards/1-workflow.md` §1.3 |
| §6.2 rule 9: a defect fix's test is seen to fail first | Moved | `.claude/skills/session-start/references/anvil.md` § Working rules |
| §6.2: converting a group replaces every test of its commands; editing for another reason doesn't convert; a new test is always this section's kind | Kept, shortened | §6.2, "Converting code to a new form replaces every test of it, in whichever file it is." The other two sentences are deleted: a test edited for another reason isn't converted code, and every new test is held to the standard as written. |
| §6.2: Service | Kept, reworded | §6.2, "Behaviour", with `fake_uow` |
| §6.2: Repository fake | Moved | §6.2, "SQL" (tested against the real repository, parametrized over both), and `tests/mocks/fake_unit_of_work.py`'s module docstring (the store, `REPOSITORIES`, the signature check) |
| §6.2: Repository loading | Kept, shortened | §6.2, "SQL". The step-by-step procedure is deleted. |
| §6.2: Renderer | Kept, shortened | §6.2, "Printed text", which also takes the Command bullet's `Error:` line. The `Console` construction, the picker's input and `tests/test_output.py` are deleted. |
| §6.2: Click parameter types | Deleted | §6.2's rule, "Each piece of logic is tested in the layer that owns it", covers it |
| §6.2: Command | Kept, reworded | §6.2, "A command": one test per path. The `Error:` line on `result.stderr` moves to the Printed text bullet. "with nothing patched" is kept in substance by "against the test's database", which only the real service reaches. `mix_stderr=False` and `obj=renderer` are deleted, because they are how a test meets the bullet. |
| §6.2: the `run_workmain` second entry path | Deleted | §6.2's rule, "Each piece of logic is tested in the layer that owns it", puts the step's handling in the workflow's own tests |

### Step 2 — record tests

For each of the six tests in §2, by DR4:

- Delete the block that opens a `session_scope()` through `get_db()`, writes, and raises, together with its `pytest.raises` wrapper. In `tests/test_clockify_service.py`, delete the `_fail_a_later_scope()` call and the helper `_fail_a_later_scope`.
- Rename the test so its name says what it checks, and reword its docstring where it has one. The new names are below the contract.
- Annotate each renamed `def` line, `db_session: Session` and `-> None`, because `automation/style_check.py` checks every changed line with ruff, and `tests/**` enforces `ANN001` and `ANN201`. Add `from sqlalchemy.orm import Session` to each of the four files, none of which has it.
- Remove any import the deletion leaves unused. That includes the module-level `get_db` in `tests/test_clockify_service.py:18`, `tests/test_gdrive.py:18` and `tests/test_slack.py:36`.

No other line in the four files changes.

### Step 3 — fixture and fake docstrings

In `tests/conftest.py`, by DR5:

- Replace the docstring of `_test_database` with:

```python
    """
    Build the test database once, before the run's first test.

    Every object the application's user owns in workmain_test is dropped, and
    the schema is built again by `alembic upgrade head` in a child process.
    pytest_configure has already pointed DB_NAME at workmain_test, and the run
    stops before the first test when DB_NAME names another database.
    workmain_test is created once by the database server's administrator,
    owned by the application's user.
    """
```

- Replace the docstring of `_isolated_database` with:

```python
    """
    Run every test inside one database transaction, rolled back at teardown.

    The application's session factory is bound to a connection this fixture
    owns, inside a transaction it began, with
    join_transaction_mode="create_savepoint". Every session opened through
    get_db() joins that transaction: commit() releases a savepoint and
    rollback() returns to one, so all sessions in a test see each other's
    writes, and the rollback at teardown discards them all. A run killed
    mid-test leaves the transaction open, and PostgreSQL rolls it back when
    the connection drops.

    Sessions on this one connection finish last-in, first-out: an object a
    test builds on db_session and hands to code that opens its own session
    fails at that code's commit.

    DatabaseConnection.close() raises during a test, and a test that replaces
    the session factory fails at teardown, because either would move the
    test's code to a connection outside this transaction.
    """
```

- Replace the docstring of `db_session` with:

```python
    """
    A session for the test's own seeding and reads.

    It comes from the same factory application code uses, so the test and the
    code it calls share one transaction and see each other's writes. Commit
    it freely; every write rolls back with the test.

    Its identity map keeps every object it has loaded: until db_session
    commits, rolls back or expire_all() is called, get() and attribute
    access return those objects as they were when loaded, and a query after
    expunge_all() reads the rows as they are now.
    """
```

- Add the fixture `fake_uow`. The import of `FakeUnitOfWork` is made under `TYPE_CHECKING` for the annotation and inside the fixture for the call, never at the top of the module, because it would import `workmain` before `pytest_configure` sets `DB_NAME` (§2).

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.mocks.fake_unit_of_work import FakeUnitOfWork


@pytest.fixture
def fake_uow() -> "FakeUnitOfWork":
    """
    A FakeUnitOfWork over a fresh, empty store, for a service test.

    A second unit of work over the same rows is
    FakeUnitOfWork(store=fake_uow.store).
    """
    from tests.mocks.fake_unit_of_work import FakeUnitOfWork

    return FakeUnitOfWork()
```

In `tests/mocks/fake_unit_of_work.py`, replace the module docstring with:

```python
"""
An in-memory stand-in for workmain/services/unit_of_work.py's UnitOfWork.

A FakeUnitOfWork holds its rows in a store, a dict keyed by table name that
every fake repository it builds shares, so a test that passes one store to
several fake units of work sees each one's committed writes in the next. It
commits by keeping the store as it is, and rolls back by restoring the store,
in place, to a deep copy taken on entry. It refuses re-entry, and a non-record
fake inside another open fake, with the real unit of work's messages, so a
service test refuses the nesting production refuses.

Each fake repository takes the store and keeps its rows under its table's
name. FakeUnitOfWork.REPOSITORIES maps the attribute names
UnitOfWork.REPOSITORIES uses to the fake classes, and
tests/test_fake_unit_of_work.py checks every fake method's signature against
the real repository's and runs each fake's contract tests against both the
fake and the real repository on db_session.
"""
```

No code in either file changes except the `fake_uow` fixture and its import.

### Step 4 — `pyproject.toml`

Delete line 29, `# A test is named for what it checks; its name is its description (docs/standards/6-testing.md §6.2).`, and keep the line below it, `"tests/**" = ["D101", "D102", "D103"]`. Nothing else changes. `addopts` is already present (Decision Log).

### Step 5 — the rules that left §6, and citations by number

- `.claude/skills/session-start/references/anvil.md:43`: replace "For a defect fix, the test that shows the defect is run before the fix and after it (`docs/standards/6-testing.md` §6.2 rule 9)." with "For a defect fix, the test that shows the defect is run before the fix, where it fails, and after it, where it passes. The results artifact records both runs."
- `docs/dev/results/_TEMPLATE_RESULTS.md:63`: replace `` `docs/standards/6-testing.md` §6.2 rule 9 `` with `` `.claude/skills/session-start/references/anvil.md` § Working rules ``.
- `docs/standards/4-database.md:68`: replace `(§6.1)` with `(§6.2)`.
- `docs/standards/1-workflow.md` §1.3: insert this bullet after the bullet that begins "**An issue is opened when its body is written, it is on the board, and its dependencies are linked.**":

  > - **A test uses inputs that every open issue leaves valid.** Opening an issue that narrows behaviour includes rewriting the open criteria and tests that exercise the narrowed path, and both issues say why.

- **The bodies of #287 and #288.** Make exactly these eleven replacements. Each quote is the whole of the text it replaces, and nothing else in either body changes. Where the old text gave a reason the new rule doesn't state, the replacement says how the rule read on 20261114.

| Issue | Text | Replacement |
| --- | --- | --- |
| #287 | `` `docs/standards/6-testing.md` §6.2 rule 5: "A test is `` | `` `docs/standards/6-testing.md` §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments", as it read on 20261114: "A test is `` |
| #287 | `which is the autouse form rule 5's reason already rules out.` | `which is the autouse form that rule's reason, as it read on 20261114, already ruled out: "pytest hands a fixture only to a test that names it as an argument".` |
| #287 | `Rule 5 says nothing about either form` | `That rule, as it read on 20261114, said nothing about either form` |
| #287 | `or one docs/standards/6-testing.md §6.2 rule 5 states a test may depend on without naming` | `or one docs/standards/6-testing.md §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments" states a test may depend on without naming` |
| #287 | `printing only lines rule 5 states are allowed` | `printing only lines that rule states are allowed` |
| #287 | `- Rule 5 states, for an autouse fixture` | `- §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments" states, for an autouse fixture` |
| #287 | `a stated reading by Ray of docs/standards/6-testing.md §6.2 rule 5, for whether` | `a stated reading by Ray of docs/standards/6-testing.md §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments", for whether` |
| #288 | `Ray 20261114. Rule 5 stays as written; the tests change.` | `Ray 20261114. The rule that a test is a method of a plain class stays; the tests change.` |
| #288 | `` `docs/standards/6-testing.md` §6.2 rule 5: "A test is a method of a plain class [...]". Rule 4 adds why: "Group related tests in `class Test<Topic>` so `-k TestTopic` works." `` | `` `docs/standards/6-testing.md` §6.2's rule "A test is a method of a plain class, and it takes what it needs as arguments", which also says "Related tests share a `Test<Topic>` class." `` |
| #288 | `also break rule 5, and are not part of this issue` | `also break that rule, and are not part of this issue` |

The #288 row on `§6.2 rule 5` and `Rule 4` makes two of the eleven replacements in one.

  - Each body is read to a file first, checked to be non-empty, edited in that file, and written back with `gh issue edit <N> --body-file`, run from the repository root.
  - It is then read back to show that only those replacements were made: the `diff` of the two files goes in the results artifact.

### Step 6 — results artifact

`docs/dev/results/TESTING_STANDARD_RULES_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. It records:

- the table of every `git grep -n 'get_db()' tests/` hit, each matched to one of these categories (AC2.1):
  - **The suite's own setup** in `tests/conftest.py`, which §6.1 says builds the database and holds the transaction. This is not a test.
  - **A test of the connection or the session machinery**: `get_db()`, `session_scope()`, `record_scope()`, `DatabaseConnection.close()`, the connection's URL, or `UnitOfWork`'s check for an open scope. The call is either the code under test, or the scope a test of `UnitOfWork`'s check opens so it can see the unit of work refused or entered (`tests/test_unit_of_work.py:195`, `:222`, `:234`, `:246`, `:252`). Either way, the session it opens joins the transaction, as §6.1's first bullet states, so it stays on the test's connection.
  - **A test of the database build**, which §6.1 states runs outside the transaction and undoes what it changes.
  - **A test an open issue converts**, named for each hit.
  - **Not a call**: a docstring, or `def fake_get_db():`.
- the Step 1 table, each row checked against the delivered files (AC3.1)
- the Step 5 diffs of #287's and #288's bodies (AC6.2)

"Defect shown before the fix" is omitted: #285 is a `gap` (Decision Log). Each criterion whose check names Ray is recorded `Not met`, `Awaiting Ray` (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None.

## 5. Acceptance criteria

The issue's ACs are numbered in its order. AC1.1, AC2.1, AC6.1, AC6.2, AC7.1 and AC7.2 restate the issue's criteria (Decision Log), and the issue body's edit is made at close-out.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §6.2 states how a test of an outside-action record is written, and that form opens no session through `get_db()` | A stated reading by Ray of `docs/standards/6-testing.md` §6.2's Outside-action record bullet, for whether a test author knows from it alone how to write a record test, and whether the form it states needs a session of the test's own; and, for the six tests Step 2 changes, no line of their bodies naming `get_db`, shown by reading each test's body in the results artifact |
| AC2.1 | Every `get_db()` call in `tests/` either complies with §6.1, or is in a test an open issue converts | `git grep -n 'get_db()' tests/`, each hit matched in the results artifact's table to one of the Step 6 categories. The table is read by Ray. |
| AC3.1 | Every statement of the old opening, §6.1 and §6.2 is accounted for: kept, moved with its new home, or deleted with its reason | A stated reading by Ray of the results artifact's table of where each old statement went |
| AC3.2 | §6 says what it requires in fewer words | `sed '/^### 6.3/,$d' docs/standards/6-testing.md \| wc -w` printing fewer than 1,872 (660 expected) |
| AC3.3 | The suite refuses an unregistered marker, and reports every skip with its reason | `python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['tool']['pytest']['ini_options']['addopts'])"` printing `--strict-markers -rs`; and `ANTHROPIC_API_KEY= GOOGLE_API_KEY= pytest tests/test_ai_providers_live.py` reporting `5 skipped`, with a `SKIPPED` line and its reason for each |
| AC3.4 | `pytest --fixtures -v` shows `_test_database`, `_isolated_database`, `db_session` and `fake_uow` with the docstrings Step 3 states | For each of the four fixtures, the block `pytest --fixtures -v -p no:cacheprovider` prints under its name equals its whole Step 3 docstring, as `inspect.cleandoc` gives it, line for line. The comparison script and its output are recorded in the results artifact. |
| AC3.5 | No docstring Step 3 writes gives an instruction | A stated reading by Ray of the four fixture docstrings and the `tests/mocks/fake_unit_of_work.py` module docstring, against `docs/standards/3-code.md` §3.1 |
| AC4.1 | §6.2 states how a command branch that skips or changes a service call is tested, as a path through the command | A stated reading by Ray of §6.2's Command bullet |
| AC6.1 | No rule in §6 is numbered, and no live document cites a §6 rule by number | `grep -nE '^[0-9]+\. ' docs/standards/6-testing.md` printing nothing, and `grep -rnE '§6(\.[0-9]+)? rule [0-9]\|[Rr]ule [0-9]+ (of\|in) §6' --include=*.md --include=*.py . \| grep -v -e CHANGELOG.md -e docs/archive/ -e DESIGN_TESTING_STANDARD_RULES.md -e TESTING_STANDARD_RULES_SPEC.md -e TESTING_STANDARD_RULES_RESULTS.md` printing nothing |
| AC6.2 | No open issue other than #285 cites a §6 rule by number | `gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --json number,body`, piped to a Python filter that prints each match of `(?<![Dd]esign )\b[Rr]ule [0-9]+\b` in the body of each issue other than #285 that names `6-testing.md` or `§6`, printing nothing. The filter is recorded in the results artifact. |
| AC6.3 | Each rule that left §6 has exactly one home | `grep -rnF 'A test uses inputs that every open issue leaves valid' CLAUDE.md docs/standards .claude` printing one line, in `docs/standards/1-workflow.md`; `grep -rnF 'where it fails, and after it, where it passes' CLAUDE.md docs/standards .claude docs/dev/*/_TEMPLATE_*.md` printing one line, in `.claude/skills/session-start/references/anvil.md` |
| AC7.1 | No test file changes except the six record tests' files, `tests/conftest.py` and `tests/mocks/fake_unit_of_work.py` | `git diff --stat origin/main...HEAD -- tests/` listing exactly `tests/conftest.py`, `tests/mocks/fake_unit_of_work.py`, `tests/test_ai_costs.py`, `tests/test_clockify_service.py`, `tests/test_gdrive.py` and `tests/test_slack.py` |
| AC7.2 | Each record test still checks what it checked: no assertion or spy changed, and none was added or removed | `git diff -U0 origin/main...HEAD -- tests/test_ai_costs.py tests/test_clockify_service.py tests/test_gdrive.py tests/test_slack.py \| grep -E '^[-+]\s*(assert\b\|.*\.assert_\w+\(\|with _record_scope_spy\|with patch\.object\(\s*$\|DatabaseConnection, .record_scope)'` printing nothing |
| AC8.1 | The full suite passes, with no test lost or added | `pytest` reporting `1707 passed, 0 failed, 0 skipped` |

## 6. Test plan

- **Baseline before this work:** `1707 passed, 0 failed, 0 skipped` (`CHANGELOG.md` 1.58.6).
- **Expected after:** `1707 passed, 0 failed, 0 skipped`. Step 2 renames six tests and removes none, and `fake_uow` adds no test.
- No test is added. The changes to the standard are checked by reading (AC1.1, AC3.1, AC3.5, AC4.1), by search (AC2.1, AC6.1–AC6.3), and by the pytest runs in AC3.3 and AC3.4.

## 7. Risks and rollback

- **A citation of §6.1 or §6.2 by content no longer finds what it cites.** `docs/standards/4-database.md` is repointed (Step 5). Open issues that cite earlier forms keep their text, and their specs restate them (§2). Rollback: revert Step 1.
- **Tests that don't meet the new text.** The suite has tests that don't, and §1 Out of scope names the issue that owns each kind. #287 owns the fixtures its tests don't take as arguments.
- **A record test loses what it checked.** AC7.2 shows that no assertion or spy changed. Rollback: revert Step 2.
- **An issue body is blanked by a failed edit.** Step 5 reads each body to a file and checks it is non-empty before writing, and the results artifact keeps the diff, so the earlier body can be restored from it.

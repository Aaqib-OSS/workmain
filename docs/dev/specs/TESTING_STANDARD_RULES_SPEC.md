# Testing Standard Rules — Spec

**Status:** Draft
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
| 20261117 | Ray | #285 adds no exceptions. A rule's apparent exception either follows from the section's governing rule, or is temporary non-compliance, which the open issue that removes it tracks and which is never written into the standard. | Adopted; DR1, Step 1. |
| 20261117 | Ray | Design study Q1: Option C. Each record test drops its later-scope block, and `tests/test_clockify_service.py` drops `_fail_a_later_scope`. §6.1 states that the fixture can't show a record surviving its caller's failure: the `record_scope` spy is the evidence for that property, and the read through `db_session` is the evidence that the record was written. The issue's first criterion is restated, and the issue body is edited at close-out. | Adopted; DR4, Steps 1 and 2, AC1.1. |
| 20261117 | Ray | The `get_db()` guidance is derived from the rule the isolation follows and from the rule on test arguments, with no exception by kind. The issue's second criterion becomes: every `get_db()` call in `tests/` either complies with §6.1, or is in a test an open issue converts, and the results table names that issue for each such hit. | Adopted; DR2, Step 1, AC2.1. |
| 20261117 | Ray | Design study Q2: Option A. The defect-fix rule moves to §6's opening, next to the rule on recorded test evidence. | Adopted; Step 1, Step 3. |
| 20261117 | Ray | Design study Q3, Q6 and Q7: §6's opening states one principle for every test, *A test's result depends only on what it sets up, and it changes nothing outside the suite's own database and temporary directories.* "Temporary directories" means `tmp_path` and pytest's base directory for it. §6.1 states how the database meets the principle, and presents the per-test rollback as how the suite keeps the first half true for every test without each test cleaning up, not as a rule of its own. Provider routing, the Renderer's width and the database isolation follow from the principle. | Adopted; DR1, Step 1. |
| 20261117 | Ray | Design study Q4: Option A. §6.2's table has rows only for the forms it states today, and code of a kind it doesn't name is tested by the principle. | Adopted; Step 1. |
| 20261117 | Ray | Design study Q5: Option A, `hotfix/*` with the patch release. The §2.2 gap is #291. | Adopted; header, §1 Out of scope. |
| 20261117 | Ray | Each test that depends on something it doesn't set up goes to the one issue that removes the dependence: #207, #214, #288 or #292. #285 changes none of them. | Adopted; §1 Out of scope. |
| 20261117 | Spanner | The issue names four later-scope sites. The census finds six tests: `tests/test_clockify_service.py`'s helper `_fail_a_later_scope` serves three (`test_s17_the_link_survives_a_later_failed_scope`, `test_s26_a_link_survives_a_later_failed_scope`, `test_s28_an_import_survives_a_later_failed_scope`). | Adopted; §2, Step 2. |
| 20261117 | Spanner | Each of the six test names says "survives a later failed scope", which is no longer what the test does. Each test is renamed, and its docstring reworded where it has one, to say what it checks. | Adopted; DR4, Step 2. |
| 20261117 | Spanner | The defect-fix rule doesn't apply to this work. #285 is labelled `gap`, not `defect`, so no test is run before a fix. | Adopted; Step 4. |
| 20261117 | Spanner | Rule 6's "the suite leaves nothing behind" is false: pytest keeps three sessions' `tmp_path` directories (design study F18). It is dropped, because the principle now says what a test may leave. | Adopted; Step 1. |
| 20261117 | Spanner | The issue's sixth criterion's search covers `.md` files only and finds "§6.2 rule N", but not the bare "Rule 4" in #288. It also matches this spec and its design study, which record the old numbers as history. Restated as AC6.1 and AC6.2. | Adopted; §5. |
| 20261117 | Spanner | The issue's seventh criterion diffs against `origin/dev`. This branch is cut from `origin/main` (design study F11). Restated as AC7.1, and AC7.2 is added to show the tests still check what they checked. | Adopted; §5. |
| 20261117 | Spanner | The issue lists the child-process launch among the recipes. Patching the launch is required, not optional, because a child process leaves the transaction. It is stated in §6.1 as following from the principle, not as a recipe. | Adopted; Step 1. |

---

## 1. Scope

**In scope:**

- `docs/standards/6-testing.md`: the opening, §6.1 and §6.2, replaced by the text Step 1 states. §6.3 is unchanged.
- The six record tests that fail a later scope, and the helper three of them use (Step 2): `tests/test_ai_costs.py`, `tests/test_clockify_service.py`, `tests/test_gdrive.py`, `tests/test_slack.py`.
- Every live citation of a §6 rule by number (Step 3): `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, and the bodies of #287 and #288.

**Out of scope:**

- What rule 5 requires. Its text moves unchanged, and only how it is cited changes. #287 and #288 apply it.
- The 17 `unittest.TestCase` classes that open a session through `get_db()` (design study F3 (e), F4). Their sessions join the test's transaction, so they meet §6.1. They don't meet the rule on test arguments, and #208, #209, #212, #214 and #216 replace them.
- The tests that depend on something they don't set up (design study § Measurement for Q3). #198 owns the width dependences. Each of the other twelve is owned by #207, #214, #288 or #292, as the design study's § Who removes each untracked dependence states.
- Forms for the layers §6.2 has no row for today: capabilities, shared code, the daemon and the Slack surface (design study Q4).
- `docs/standards/2-git.md` §2.2: #291.
- The edit to #285's own body, which `docs/standards/1-workflow.md` §1.2 leaves to close-out.
- Any file under `workmain/`, `config/` or `templates/`.

## 2. Verified current state

On `hotfix/issue-285-testing-standard-rules` at `e206063`, whose `tests/`, `docs/standards/` and `.claude/` are `origin/main` `bd9b0dc`'s, 20261117.

| Claim | Evidence |
| --- | --- |
| `docs/standards/6-testing.md` is §6's opening (lines 1–13), §6.1 (15–35), §6.2 (37–76) and §6.3 (78–80). §6.2 has a code example, nine numbered rules and seven layer bullets. | `docs/standards/6-testing.md` |
| §6.1 says "Never call `get_db()` or `db.get_session()` in a test", names `tests/test_database_isolation.py` and `tests/test_unit_of_work.py` as the only exceptions, and tells a record test to "fail a later scope". | `docs/standards/6-testing.md:28`, `:30`, `:33` |
| `db_session` is a session from `get_db().get_session()`, and `_isolated_database` binds `DatabaseConnection.SessionLocal` to the test's connection with `join_transaction_mode="create_savepoint"`. Every session opened through `get_db()` therefore joins the test's transaction. | `tests/conftest.py` `_isolated_database`, `db_session` (`:176`) |
| The ban on `get_db()` dates from the fixture before #136, and its stated reason was removed when #136 replaced that fixture. | `git show c283f20 -- docs/DEVELOPMENT_STANDARDS.md`; design study F13 |
| Six tests fail a later scope after calling a function that writes an outside-action record, and each wraps the call in a `record_scope` spy: `tests/test_ai_costs.py::TestAiCostService::test_record_reply_survives_a_later_failed_scope` (`:627`, scope at `:645-648`, `spy.assert_called_once()`); `tests/test_gdrive.py::TestDriveUploadRecord::test_t18_record_survives_a_later_failed_scope` (`:261`, scope at `:272-275`, `spy.assert_called_once()`); `tests/test_slack.py::TestSlackPostRecord::test_t19_record_survives_a_later_failed_scope` (`:585`, scope at `:601-605`, `spy.assert_called_once()`); `tests/test_clockify_service.py::TestPush::test_s17_the_link_survives_a_later_failed_scope` (`:330`), `::TestPull::test_s26_a_link_survives_a_later_failed_scope` (`:497`) and `::TestPull::test_s28_an_import_survives_a_later_failed_scope` (`:557`), each calling `_fail_a_later_scope()` (`:107-112`) and asserting `spy.assert_called()`. Only the first has a docstring, and it describes the later scope. | `pytest --collect-only -q \| grep later_failed_scope`; `grep -n "_fail_a_later_scope\|later" tests/test_clockify_service.py tests/test_ai_costs.py tests/test_gdrive.py tests/test_slack.py` |
| Under the fixture, failing a later scope can't change whether a record test passes. | design study F2 (probe) |
| After Step 2, `get_db` is no longer named in `tests/test_clockify_service.py` or `tests/test_gdrive.py` except the import, and `tests/test_gdrive.py:236` patches `workmain.cli.commands.gdocs.get_db` by string. `tests/test_slack.py` still calls `get_db()` at `:414`, in a `TestCase` setup. | `grep -n "get_db" tests/test_clockify_service.py tests/test_gdrive.py tests/test_slack.py` |
| `git grep -n 'get_db()' tests/` prints 49 lines in six kinds. Step 2 removes the four record-test lines and leaves 45. | design study F3 |
| Live citations of a §6 rule by number: `.claude/skills/session-start/references/anvil.md:43` and `docs/dev/results/_TEMPLATE_RESULTS.md:63` cite "§6.2 rule 9". No other file in the document set cites one, or restates a rule Step 1 changes. | `grep -rnE '§6\.[0-9]+ rule [0-9]' --include=*.md . \| grep -v -e CHANGELOG.md -e docs/archive/`; `grep -rnE "later scope\|Never call .get_db\|db_session\|one assertion focus\|pins behaviour\|seen to fail first\|stubbed_manager\|recording renderer\|end-to-end test per\|leaves nothing behind\|test_database_isolation\|test_unit_of_work" CLAUDE.md docs/standards .claude docs/dev/*/_TEMPLATE_*.md docs/ARCHITECTURE.md .github automation/*.py \| grep -v -e docs/standards/6-testing.md -e _test.py:` printing nothing |
| Open issues that cite a §6 rule by number: #287, 7 times, and #288, 4 times. No other open issue does, apart from #285. | The AC6.2 command, run 20261117 |
| Every other live citation names §6, §6.1 or §6.2, and still resolves after Step 1, which keeps the loading recipe in §6.2 and the record test in §6.1. That covers `docs/standards/4-database.md:35`, `:64` and `:68`, `tests/test_time_tracking.py:7`, the templates, and the open issues that cite the service, command and renderer forms. | design study F6 |
| `tests/mocks/fake_unit_of_work.py`'s `FakeUnitOfWork(store=...)` keeps rows under each table's name, and sets `committed` or `rolled_back` when it exits. No service takes a unit of work on `main` yet. | `tests/test_fake_unit_of_work.py::TestFakeUnitOfWork`; design study F8 |
| `clients delete` confirms through `click.confirm`, which `CliRunner`'s `input` answers. A pick goes through `Renderer.pick`. | `workmain/cli/commands/clients.py:163`; `workmain/cli/output.py:310` |
| Suite: `1707 passed, 0 failed, 0 skipped`. | `CHANGELOG.md` 1.58.6; a bare `pytest` at `bd9b0dc`, 20261116 |

## 3. Design rules

- **DR1 — One principle, stated once.** §6's opening states the principle for every test. §6.1 and §6.2 state how it is met, and nothing in either is an exception to it. A statement that needed one is either derived from the principle or the rule on test arguments, or is temporary non-compliance, which is left to the issue that removes it and not written into the standard.
- **DR2 — Which session a test uses is the rule on test arguments' question, not isolation's.** §6.1 says nothing that forbids `get_db()` as such. It says a test that seeds or reads takes `db_session`, and that a test whose subject is the session machinery calls it.
- **DR3 — Every old statement has a place.** Each statement of the old opening, §6.1 and §6.2 goes to the new place the table in Step 1 states, or is dropped for the reason it gives.
- **DR4 — A record test keeps what it checks.** Step 2 removes each test's later-scope block, and `_fail_a_later_scope` once nothing calls it, and renames the tests. Every assertion, spy, seed and call to the function under test stays as it is.

Anything this spec does not decide is a departure: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §6's opening, §6.1 and §6.2 as Step 1 states them | `docs/standards/6-testing.md` |
| 2 | The six record tests without a later scope | `tests/test_ai_costs.py`, `tests/test_clockify_service.py`, `tests/test_gdrive.py`, `tests/test_slack.py` |
| 3 | Every citation of a §6 rule by number names the rule instead | `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`; the bodies of #287 and #288 |
| 4 | Results artifact | `docs/dev/results/TESTING_STANDARD_RULES_RESULTS.md` |

### Step 1 — the testing standard

In `docs/standards/6-testing.md`, replace everything from the line `## 6. Testing Standards` up to the line before `### 6.3 Placement` with the text below. `### 6.3 Placement` and what follows it are unchanged.

````markdown
## 6. Testing Standards

**A test's result depends only on what it sets up, and it changes nothing outside the suite's own database and temporary directories.** The suite's own database is `workmain_test` (§6.1). Its temporary directories are each test's `tmp_path` and the base directory pytest creates them in. Anything a person or the machine can change between runs is something a test did not set up: for example, a setting in `config/`, a value in `.env`, the terminal's width, a file under `~/.workmain/`, or a service on the network. §6.1 states how the database meets this principle, and §6.2 how each kind of test does.

- pytest is the exclusive runner.
- **The application suite is a bare `pytest` from the repository root.** `testpaths` in `pyproject.toml` is what resolves it to `tests/`. No other invocation stands in for it unless a spec names the alternative and states why. That covers a path subset, a `-k` or `-m` filter, and an environment variable that changes what runs.
- Non-application suites, such as `pytest automation/`, are reached by their own path. Each is a separate suite, not an alternative to this one. §7 owns test placement.
- **A test reports what actually happened.** Passed means it ran and its assertions held. Failed means it ran and did not — an error, a timeout or a wrong answer. Skipped means it did not run because a precondition declared with `@pytest.mark.skipif` was absent; that is the only way a test is skipped, and it is decided before the test exercises anything. A test never reports passed without having run, which is what an early `return` does, and never reports skipped after it has run. A skip is never added to turn a red suite green.
- **Recorded test evidence states all three counts, in the form `<passed> passed, <failed> failed, <skipped> skipped`, and writes each one even when it is zero.** pytest counts a skipped test separately from a passed one, so a record without the skipped count can't show whether a run did less than the full suite.
- **A defect fix's test is seen to fail first.** The implementer runs the test that shows the defect before the fix, where it fails, and again after, where it passes. The results artifact records both runs.

  ```bash
  pytest                              # full suite
  pytest -v                           # verbose
  pytest tests/test_x.py::TestClass::test_name
  ```

### 6.1 Test isolation from the database

The database meets §6's principle in two ways. The suite builds its own database from empty before the first test, so no test sees what an earlier run or the live database left. And it runs every test inside one transaction that is rolled back when the test ends. The rollback isn't a rule a test follows. It is how the suite keeps the first half of the principle true for every test without any test cleaning up: no test sees a row another test wrote. What a test itself does follows the description below.

- **The suite runs on its own database, `workmain_test`, and builds it from empty at the start of every run.** Before the first test, `tests/conftest.py` drops every object the application's user owns in it and builds the schema again with `alembic upgrade head` (§4.5), run as a child process. The rest of the connection comes from `.env`. A run against any other database is refused: `conftest.py` sets `DB_NAME` to `workmain_test` when it is unset, and stops the run, before any test, when it names another database. `workmain_test` is created once, by the server's administrator, owned by the application's user.
- **Every test runs inside one database transaction that is rolled back when it ends.** The autouse fixture `_isolated_database` in `tests/conftest.py` binds the application's session factory (`DatabaseConnection.SessionLocal`) to a connection the fixture owns, inside a transaction it began, with SQLAlchemy's `join_transaction_mode="create_savepoint"`. No test requests it and no test can opt out of it.
- Every session any code opens through `get_db()` joins that transaction: the test's own, a command run through `CliRunner`, and application code the test reaches without naming it. They share one connection, so each sees what the others wrote.

| Action | Effect |
| --- | --- |
| `commit()` anywhere | Releases a savepoint. The rows stay visible to every session in the test; nothing reaches the database. |
| `rollback()` anywhere | Discards that session's writes since its last commit, and every commit a session opened after it made in the meantime. Rows written before it began survive. |
| Test ends | The transaction rolls back; every write is discarded. |
| Process killed mid-test | The transaction was never committed; PostgreSQL discards it when the connection drops. |

A test meets the principle against the database as follows.

- **A test that seeds or reads takes `db_session`.** It is a session from the same factory, so a command or service the test then calls sees what the test seeded. Commit it freely. A session the test opened through `get_db()` would join the same transaction. A test takes `db_session` because it is a fixture in `tests/conftest.py` (§6.2, "A test is a method of a plain class, and it takes what it needs as arguments").
- **A test of the session machinery calls it.** A test of `get_db()`, `session_scope()`, `record_scope()` or `DatabaseConnection.close()` calls them, as any test calls the code it tests. A test of code that runs outside any transaction, such as the build, undoes what it changed before it ends.
- **Hand application code a session only before that code opens its own.** Sessions sharing the connection must finish last-in, first-out, because releasing a savepoint also releases every savepoint opened after it. A test that builds an application object on `db_session` and then runs a command that opens its own session fails with `InvalidSavepointSpecification` at the command's commit. Let the command build the object from the session it opens, as `tests/test_cost_display.py`'s `TestMeetingsCondenseTokenLine` does.
- **An outside-action record (§4.3) is tested at the function that writes it, by what a test can show.** In production `record_scope()` commits on a connection of its own, so the record survives a later failure of its caller. A test can't show that, because every session in it shares one transaction: a failed scope opened after the record can't discard it, and one opened before the record discards it, though production keeps it. The test calls the function, and asserts two things:
  - a spy that wraps `DatabaseConnection.record_scope` shows the function opened `record_scope()`, which is the evidence that the record commits on its own
  - the record can be read through `db_session`, which is the evidence it was written: a record whose session closed without a commit is gone by then
- **Inject a database failure; never rely on one.** Patch the module's `get_db` to raise, as `tests/test_ai_costs.py` does.
- **Nothing a test reaches leaves the transaction.** During a test `DatabaseConnection.close()` raises, and replacing `SessionLocal` fails the test at teardown. Code that builds its own engine is outside the transaction. A test reaches it only when it is the code under test, and then undoes what it changed.
- **A child process is outside the transaction.** A test that reaches code which launches `workmain` (`workmain/utils/self_invoke.py`, `workmain/workflows/eod_workflow.py`) patches the launch.
- **Every session in a test shares one connection, so database work stays on the test's thread.** A test that reaches a step thread replaces `threading.Thread`, as `tests/test_orchestration.py` does.

### 6.2 Writing a test

**Each piece of logic is tested in the layer that owns it, through the lightest setup that reaches it, with one test per path through that code.** `docs/ARCHITECTURE.md` §1 states the layers and what each owns. A path is one way through the code. A branch that changes what the code calls, returns, writes or raises is a path of its own. The table states the form for each kind of code that has one. Code of a kind the table doesn't name is tested by this principle.

| Code | What it owns | Form | Fixture | File |
| --- | --- | --- | --- | --- |
| **Service** — application layer, `workmain/services/` | Every decision, and what it returns or raises | Call the service function and assert the result's fields, or the exception it raises. A service that takes a unit of work is handed a fake one holding the rows the test needs. A service that takes a session is handed `db_session` after the test seeds it. | `FakeUnitOfWork` (`tests/mocks/fake_unit_of_work.py`), or `db_session` | The service's test file |
| **Repository** — data layer, `workmain/database/repositories/` | Its queries and writes, and the related records each method loads (§4.3) | Call the method on `db_session` after seeding, and assert the rows. A method that loads related records also has a test that counts its statements ("Counting a method's statements", below). | `db_session` | The repository's test file |
| **Fake repository** — `tests/mocks/fake_unit_of_work.py` (§7) | Standing in for its repository in a service test | A test asserts that each fake method exists on the real repository with an equal signature. Each fake method's behaviour is tested in one class parametrized over the real repository on `db_session` and the fake, so both must give the same answer. | `db_session`, for the real repository | `tests/test_fake_unit_of_work.py` |
| **Renderer** — CLI surface, `workmain/cli/output.py` | How a result is printed | Build a view and a result by hand, and render them through `Renderer(console=Console(file=io.StringIO(), width=N))`, with the width written in the test so the terminal's width can't change the outcome. A picker test feeds its answers through `CliRunner().isolation(input=...)`. These are the only tests that read printed text. | none | `tests/test_output.py` |
| **Click parameter type** — CLI surface, `workmain/cli/params.py` | Turning an argument into a value | Call `convert`, and run a usage error through `CliRunner` for its exit. | none | `tests/test_cli_params.py` |
| **Command** — CLI surface, `workmain/cli/commands/` | Which service function the command calls and with what, and every branch in the command that skips, repeats or changes a service call. Examples are a declined or interrupted prompt, a cancelled pick, a flag such as `--force`, and an option mapped to an argument such as `--all`. | One end-to-end test per path through the command. A group on its own has none. Run the command through `CliRunner(mix_stderr=False).invoke(group, args, input=..., obj=renderer)` with nothing patched, so the real service runs against the test's database (§6.1). `renderer` is a recording renderer: a fake in `tests/` with `Renderer`'s methods, which keeps what each one is handed instead of printing it, and returns the answer the test gave it for a pick. The command's arguments and its answers choose the path: a Click prompt's answer through `input`, a pick's through the recording renderer. Assert the exit code, the values the renderer received, and, through `db_session`, the rows the path writes or leaves alone. Read no printed text except an `Error:` line on `result.stderr`. Edge cases are tested at the service, and the error wiring once, in `tests/test_output.py`'s `TestWiring`. | `db_session`, to seed and to read | The group's test file |
| **EOD workflow step** — application layer, `workmain/workflows/eod_workflow.py` | What a step does with the exit code and output of a command it runs as a child process through `run_workmain` | The step's own test patches `run_workmain` to return each exit code and output, and asserts what the step does. A command test covers only the `CliRunner` path, because a child process is outside the transaction (§6.1). | as the step needs | `tests/test_eod_workflow.py` |

A service test on a fake unit of work:

```python
"""
<Service> tests.
"""

from tests.mocks.fake_unit_of_work import FakeUnitOfWork
from workmain.services import <service>


class Test<UseCase>:
    """<What this class tests>."""

    def test_<path>(self) -> None:
        uow = FakeUnitOfWork(store={'<table>': {<key>: <row>}})
        result = <service>.<use_case>(uow, <arguments>)
        assert result.<field> == <expected>
        assert uow.committed is True
```

**Rules for every test.**

- **A test is a method of a plain class, and it takes what it needs as arguments.** An argument is a fixture pytest itself provides, a fixture in `tests/conftest.py`, or a name a `parametrize` mark on the test or its class supplies; anything else, the test builds in its own body. pytest hands a fixture only to a test that names it as an argument, so this is the one form in which every test can reach every fixture.
- **Related tests share a class.** Group related tests in `class Test<Topic>` so `-k TestTopic` works.
- **One assertion focus per test.** Prefer several small tests over one large one.
- **A test cleans up nothing.** §6.1's rollback discards its database writes, and its directory is `tmp_path`.
- **A test's directory is `tmp_path`.** pytest creates it for the test and keeps only its last three runs, so a test has no directory to clean up.
- **A test pins behaviour meant to stay.** It never exercises a path an open issue is about to remove or narrow; it proves the same property with inputs that issue leaves valid. Opening an issue that narrows behaviour includes rewriting the open criteria and tests that exercise the narrowed path, and both issues say why.
- **A new test takes the form this section states.** Converting code to a new form replaces every test of it, in whichever file the test is: converting a command group to a service replaces every test of its commands. Editing a test for any other reason does not convert it or its file.

**Recipes.** Each is how to meet a rule or row above, not a rule of its own.

- **Routing for a real `ProviderManager`** meets §6's principle, because `workmain providers set default` changes the routing in `config/ai_settings.json` in ordinary use. A test that builds a real `ProviderManager` passes the primary and fallback of every call type it exercises, and leaves no provider it doesn't stub reachable. `tests/mocks/stub_providers.py`'s `stubbed_manager` takes the routing as a required argument and makes every unstubbed provider raise.
- **Counting a method's statements** meets the Repository row. The test goes in the repository's test file:
  - **Seed.** One row on one value of the method's filter, and five rows on another. Each of the five points at its own related rows, because a lazy many-to-one costs one query per distinct related row, so five rows sharing one would count the same as one with no loading at all. For a one-to-many, each of the five parents has at least one child. A method with no filter is counted twice, after seeding one row and again after seeding four more.
  - **Expunge.** The test calls `db_session.expunge_all()` after seeding, so no related row is already in the session.
  - **Count.** A `before_cursor_execute` listener on `db_session.connection()` counts statements around the method call and a read, on each row, of every relationship the method loads. The count is equal for one row and for five.
  - **Patch out records.** Every session in a test shares that connection (§6.1), so an outside-action record (§4.3) on the path is patched out of the count. That record keeps its own test at the function that writes it.
- **Writing a fake repository** meets the Fake repository row. The fake takes the fake unit of work's store, keeps its rows under its table's name, and is added to `FakeUnitOfWork.REPOSITORIES` under the same attribute name as in `UnitOfWork.REPOSITORIES`.

````

Where each old statement goes. The results artifact's §3 copies this table, with each row checked against the delivered file (AC3.1).

| Old statement | New place | How it stands there |
| --- | --- | --- |
| Opening: pytest is the runner; the bare `pytest`; non-application suites; a test reports what happened; recorded evidence; the command examples | §6 opening | Unchanged |
| §6.1 bullets 1–3 (the build, the transaction, every `get_db()` session joins) and the table | §6.1 | Unchanged; how the database meets the principle |
| §6.1 "A test that seeds or reads takes `db_session` … Never call `get_db()` or `db.get_session()` in a test." | §6.1 "A test that seeds or reads takes `db_session`." | Derived from the rule on test arguments. The ban is dropped, because it protects nothing under this fixture (design study F13). |
| §6.1 "Hand application code a session only before that code opens its own." | §6.1, same | Unchanged; derived from the transaction |
| §6.1 "A record committed inside another session's open transaction is discarded …" and "Test an outside-action record … fail a later scope …" | §6.1 "An outside-action record (§4.3) is tested at the function that writes it, by what a test can show." | Derived; rewritten by design study Q1 |
| §6.1 "Inject a database failure; never rely on one." | §6.1, same | Unchanged; derived from the principle |
| §6.1 "Leaving the transaction fails the test." | §6.1 "Nothing a test reaches leaves the transaction." | Derived. "No test may reach" code that builds its own engine becomes "only when it is the code under test, and then undoes what it changed". |
| §6.1 exceptions for `tests/test_database_isolation.py` and `tests/test_unit_of_work.py` | §6.1 "A test of the session machinery calls it." | Derived; no longer an exception (design study F14) |
| §6.1 child process; one thread | §6.1, same | Unchanged; derived from the principle |
| §6.2 example: a repository test on `db_session` | §6.2 example: a service test on `FakeUnitOfWork` | Replaced |
| §6.2 rule 1 (take `db_session`) | §6.1 "A test that seeds or reads takes `db_session`." | Derived |
| §6.2 rule 2 (one assertion focus) | §6.2 "One assertion focus per test." | A rule for every test |
| §6.2 rule 3 (no manual cleanup) | §6.2 "A test cleans up nothing." | A rule for every test, derived from §6.1 and `tmp_path` |
| §6.2 rule 4 (group in `class Test<Topic>`) | §6.2 "Related tests share a class." | A rule for every test |
| §6.2 rule 5 (a plain class, arguments) | §6.2 "A test is a method of a plain class, and it takes what it needs as arguments." | A rule for every test; text unchanged |
| §6.2 rule 6 (`tmp_path`) | §6.2 "A test's directory is `tmp_path`." | A rule for every test. "and the suite leaves nothing behind" is dropped (Decision Log). |
| §6.2 rule 7 (provider routing) | §6.2 recipe "Routing for a real `ProviderManager`" | A recipe for §6's principle |
| §6.2 rule 8 (pin behaviour meant to stay) | §6.2 "A test pins behaviour meant to stay." | A rule for every test; text unchanged |
| §6.2 rule 9 (defect fix seen to fail first) | §6 opening "A defect fix's test is seen to fail first." | Moved (design study Q2); text unchanged |
| §6.2 "Each layer has one kind of test …" (conversion replaces every test of a group) | §6.2 principle, and "A new test takes the form this section states." | A rule for every test; #198's number is dropped, because the rule holds for any conversion |
| §6.2 Service | §6.2 table, Service row | Derived from the principle |
| §6.2 Repository fake | §6.2 table, Fake repository row, and recipe "Writing a fake repository" | What is required goes in the row; how to write the fake is the recipe |
| §6.2 Repository loading | §6.2 table, Repository row, and recipe "Counting a method's statements" | What is required goes in the row; the procedure is the recipe |
| §6.2 Renderer | §6.2 table, Renderer row | Derived; the width is tied to the principle |
| §6.2 Click parameter types | §6.2 table, Click parameter type row | Derived |
| §6.2 Command | §6.2 table, Command row | Derived. "One more for each flag that makes the command call a different service function" becomes one test per path through the command, which covers #279's design study Q5. |
| §6.2 `run_workmain` second entry path | §6.2 table, EOD workflow step row | Derived |

### Step 2 — record tests

For each of the six tests in §2, by DR4:

- Delete the block that opens a `session_scope()` through `get_db()`, writes, and raises, together with its `pytest.raises` wrapper. In `tests/test_clockify_service.py`, delete the `_fail_a_later_scope()` call and the helper `_fail_a_later_scope`.
- Rename the test so its name says what it checks, and reword its docstring where it has one. The new names are below the contract.
- Remove any import the deletion leaves unused.

No other line in the four files changes.

### Step 3 — citations by number

- `.claude/skills/session-start/references/anvil.md:43`: replace `(`docs/standards/6-testing.md` §6.2 rule 9)` with `(`docs/standards/6-testing.md` §6, "A defect fix's test is seen to fail first")`.
- `docs/dev/results/_TEMPLATE_RESULTS.md:63`: replace `` `docs/standards/6-testing.md` §6.2 rule 9 `` with `` `docs/standards/6-testing.md` §6, "A defect fix's test is seen to fail first" ``.
- **The bodies of #287 and #288.** Replace each reference to a §6.2 rule by number with the rule's name. The references are "rule 5" and "Rule 5", whether or not they follow "§6.2", and "Rule 4" in #288. The names are "A test is a method of a plain class, and it takes what it needs as arguments" for rule 5, and "Related tests share a class" for rule 4. A grammatical form such as "rule 5's reason" becomes the same form of the name. Nothing else in either body changes.
  - Each body is read to a file first, checked to be non-empty, edited in that file, and written back with `gh issue edit <N> --body-file`, run from the repository root.
  - It is then read back to show that only those references changed: `diff` of the two files, recorded in the results artifact.

### Step 4 — results artifact

`docs/dev/results/TESTING_STANDARD_RULES_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. It records:

- the table of every `git grep -n 'get_db()' tests/` hit, with the §6.1 statement it complies with, or the open issue that converts its test, or "not a call" (AC2.1)
- the Step 1 table of where each old statement went, each row checked against the delivered file (AC3.1)
- the Step 3 diffs of #287's and #288's bodies (AC6.2)

"Defect shown before the fix" is omitted: #285 is a `gap` (Decision Log). Each criterion whose check names Ray is recorded `Not met`, `Awaiting Ray` (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None.

## 5. Acceptance criteria

The issue's ACs are numbered in its order. AC1.1, AC2.1, AC6.1, AC6.2, AC7.1 and AC7.2 restate the issue's criteria (Decision Log), and the issue body's edit is made at close-out.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §6.1 states how a test of an outside-action record is written, what it can show and why, and that form opens no session through `get_db()` | A stated reading by Ray of `docs/standards/6-testing.md` §6.1, for whether a test author knows from it alone how to write a record test |
| AC2.1 | Every `get_db()` call in `tests/` either complies with §6.1, or is in a test an open issue converts | `git grep -n 'get_db()' tests/`, with each hit matched in the results artifact's table to the §6.1 statement it complies with, the open issue that converts its test, or "not a call" (a docstring, or `def fake_get_db():`). The table is read by Ray. |
| AC3.1 | §6 states one principle for every test, §6.1 and §6.2 each state how their forms meet it, and every old statement is accounted for | A stated reading by Ray of `docs/standards/6-testing.md`'s opening, §6.1 and §6.2, and of the results artifact's table of where each old statement went |
| AC4.1 | §6.2 states how a command branch that skips or changes a service call is tested, as a path through the command | A stated reading by Ray of §6.2's Command row |
| AC5.1 | §6.2's example is a service test on `FakeUnitOfWork` | A stated reading by Ray of the example |
| AC6.1 | No rule in §6 is numbered, and no live document cites a §6 rule by number | `grep -nE '^[0-9]+\. ' docs/standards/6-testing.md` printing nothing, and `grep -rnE '§6(\.[0-9]+)? rule [0-9]\|[Rr]ule [0-9]+ (of\|in) §6' --include=*.md --include=*.py . \| grep -v -e CHANGELOG.md -e docs/archive/ -e DESIGN_TESTING_STANDARD_RULES.md -e TESTING_STANDARD_RULES_SPEC.md -e TESTING_STANDARD_RULES_RESULTS.md` printing nothing |
| AC6.2 | No open issue other than #285 cites a §6 rule by number | `gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --json number,body`, piped to a Python filter that prints each match of `(?<![Dd]esign )\b[Rr]ule [0-9]+\b` in the body of each issue other than #285 that names `6-testing.md` or `§6`, printing nothing. The filter is recorded in the results artifact. |
| AC7.1 | No test changes except the six record tests | `git diff --stat origin/main...HEAD -- tests/` listing exactly `tests/test_ai_costs.py`, `tests/test_clockify_service.py`, `tests/test_gdrive.py` and `tests/test_slack.py` |
| AC7.2 | Each record test still checks what it checked: no assertion or spy changed, and none was added or removed | `git diff -U0 origin/main...HEAD -- tests/ \| grep -E '^[-+]\s*(assert\b\|.*\.assert_\w+\(\|with _record_scope_spy\|with patch\.object\(\s*$\|DatabaseConnection, .record_scope)'` printing nothing |
| AC8.1 | The full suite passes, with no test lost or added | `pytest` reporting `1707 passed, 0 failed, 0 skipped` |

## 6. Test plan

- **Baseline before this work:** `1707 passed, 0 failed, 0 skipped` (`CHANGELOG.md` 1.58.6).
- **Expected after:** `1707 passed, 0 failed, 0 skipped`. Step 2 renames six tests and removes none.
- No test is added. The changes to the standard are checked by reading (AC1.1, AC3.1–AC5.1) and by search (AC2.1, AC6.1, AC6.2).

## 7. Risks and rollback

- **A citation of §6.1 or §6.2 by content no longer finds what it cites.** Step 1 keeps every form that the live citations name (design study F6), and AC3.1's table accounts for every old statement. Rollback: revert Step 1.
- **A record test loses what it checked.** AC7.2 shows that no assertion or spy changed. Rollback: revert Step 2.
- **An issue body is blanked by a failed edit.** Step 3 reads each body to a file and checks it is non-empty before writing, and the results artifact keeps the diff, so the earlier body can be restored from it.

# Testing Standard Rules — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261116
**Originating item:** Issue #285

---

## 1. Purpose

Issue #285 restructures `docs/standards/6-testing.md` §6.1 and §6.2 so that each states the rule its forms follow from, and so that §6.1's rule on `get_db()` and its record-test bullet cannot conflict. The issue leaves two questions to this study: whether the defect-fix rule (§6.2 rule 9) moves to `docs/standards/1-workflow.md`, and whether the record tests change or the rule allows their form. Recon raised two more: whether the record test's later scope proves anything, and what rule the provider-routing recipe meets.

## 2. Scope of the read

All measured on `hotfix/issue-285-testing-standard-rules` at `bd9b0dc`, cut from `origin/main`, 20261116. `git diff --stat origin/main origin/dev` was empty, so the two trees are the same.

- **Read in full:** `docs/standards/6-testing.md`; `docs/standards/4-database.md` §4.2 and §4.3; `tests/conftest.py`; `workmain/database/connection.py` (`session_scope`, `record_scope`, `scope_open`); the four record tests the issue names; the setup of every `unittest.TestCase` class that calls `get_db()`.
- **Searched:**
  - every `get_db()` in `tests/`, and every other way a test opens a session: `DatabaseConnection()`, `SessionLocal(`, `.session_scope(`, `.record_scope(`, `.get_session(`, and an aliased import
  - every live citation of `docs/standards/6-testing.md`, `§6`, `§6.1` and `§6.2` in `*.md`, `*.py` and `*.json`, with `CHANGELOG.md` and `docs/archive/` excluded
  - every open issue body that cites `§6.N`
  - #279's design study on `feature/issue-279-clients-tasks-unit-of-work`, Q5
  - the bodies of #287 and #288
- **Not read:** how capabilities (`workmain/ai/`, `workmain/integrations/`, `workmain/templates_engine/`), the daemon, workflows and the Slack surface are tested today. §6.2 states no form for them, and this study doesn't propose one (Q4).

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The conflict the issue states holds. §6.1 says "Never call `get_db()` or `db.get_session()` in a test", and names only `tests/test_database_isolation.py` and `tests/test_unit_of_work.py` as exceptions. Its record-test bullet says "call it, fail a later scope, and assert the record through `db_session`", and all four record tests open that later scope with `get_db().session_scope()`. | `docs/standards/6-testing.md:28`, `:30`, `:33`; `tests/test_clockify_service.py:109` (in the helper `_fail_a_later_scope`), `tests/test_ai_costs.py:646`, `tests/test_gdrive.py:273`, `tests/test_slack.py:602` | High |
| F2 | **In the test fixture, failing a later scope can't change whether a record test passes.** §6.1's own table says a `rollback()` discards that session's writes "and every commit a session opened after it made in the meantime". A scope opened after the record has closed therefore can't discard the record. A probe (scratch, not committed) ran three record writes through the suite's fixtures and read each through `db_session` before and after failing a later `session_scope()`. Committed in `record_scope()`: 1 before, 1 after. Flushed and closed without a commit: 0 and 0. Flushed and left open: 1 and 1. In every case the read before the later failure gives the same result as the read after it. Two other things carry the evidence: the `record_scope` spy each test already wraps around the call (`patch.object(DatabaseConnection, 'record_scope', autospec=True, side_effect=...)`), and the read through `db_session` after the function returns, which fails for a record that was never committed. Nothing in the fixture detects a record session left open without a commit: every session shares one connection, so `db_session` sees that row's flush. | `docs/standards/6-testing.md:24`; `tests/conftest.py` `_isolated_database` (`join_transaction_mode="create_savepoint"`); the four tests in F1; probe output `committed: before 1 after 1`, `uncommitted+closed: before 0 after 0`, `uncommitted+open: before 1 after 1` | High |
| F3 | `git grep -n 'get_db()' tests/` prints 49 lines in six kinds. **(a)** `tests/conftest.py`: 4 lines, the fixtures that own the transaction. 3 are calls and `:124` is a docstring. §6.1 names no exception for this file. **(b)** `tests/test_database_isolation.py`: 8 lines, 7 calls plus the docstring at `:4`. **(c)** `tests/test_unit_of_work.py`: 14 lines, 13 calls plus the docstring at `:5`. **(d)** The four record tests in F1. **(e)** 18 lines in 17 `unittest.TestCase` classes, which open their seeding session in `setUp` with `get_db().get_session()`: 17 calls plus the docstring at `tests/test_ai_arguments.py:268`. **(f)** `tests/test_ai_costs.py:662`, `def fake_get_db():`, which matches the pattern but is not a call. Kinds (b) and (c) are the named exceptions. Kinds (a), (d) and (e) are covered by none. | `git grep -c 'get_db()' tests/` | High |
| F4 | All 17 classes in F3 (e) are command tests of a group that has an open conversion issue. Each runs `CliRunner().invoke` on a group: `meetings` (#208), `notes` (#209), `reports` (#212, including `tests/test_ai_arguments.py`'s `TestReportTypeFiltersRows`), `slack` (#214) and `time` (#216). They hold 60 tests, the same 60 that #288 says "the command-group issues under #198 convert". A `TestCase` method can't take a pytest fixture, so `db_session` can't reach it. | An AST walk of `tests/test_*.py` for `TestCase` classes whose source holds `get_db()`, with each class's `invoke(<group>` targets; #288 body | Medium |
| F5 | The issue's `get_db()` criterion is checked by `git grep -n 'get_db()' tests/`. It reaches every session-opening call: no test aliases `get_db`, or opens a session through `DatabaseConnection()`, `SessionLocal(` or `connection.db`. The one `DatabaseConnection()` (`tests/test_ai_costs.py:666`) is inside a patched `get_db` and opens nothing. The search also matches docstrings and `def fake_get_db():`, so the results table must say for each hit whether it is a call. | The searches in §2 | Low |
| F6 | Two live documents cite §6.2 rule 9 by number, but the issue names only the first: `.claude/skills/session-start/references/anvil.md:43` and `docs/dev/results/_TEMPLATE_RESULTS.md:63`. Two open issues cite rule 5 by number: #287 three times and #288 once. #288 also says "Rule 4 adds why", a bare number that the issue's search for "§6.2 rule" does not find. No other live text cites a §6 rule by number. The section citations stay correct after the restructure, provided the loading recipe stays in §6.2 and the record-test statement in §6.1: `docs/standards/4-database.md:35` ("tests follow §6.1"), `:64` ("§6.2 states how the loading is tested"), `:68` ("tested at the function that writes it (§6.1)"), and `tests/test_time_tracking.py:7` (§6.1). The open issues that cite §6.2 by section (#205–#216, #251, #256, #265, #279–#282, #73, #45) cite the service, command and renderer forms, and the restructure keeps all three. | The searches in §2 | Medium |
| F7 | §6.2 rule 7 (provider routing) is listed in the issue as a recipe, "how to meet a rule above". No rule in §6.2 is one it meets. Its reason is that a test must not rely on `config/ai_settings.json`, "which `workmain providers set default` changes in ordinary use". The Renderer bullet sets the width so that "`COLUMNS` cannot change the outcome", for the same kind of reason, and states no rule either. | `docs/standards/6-testing.md:64`, `:73` | Medium |
| F8 | No service takes a unit of work on `main` yet. #279 is the first conversion. The new example therefore uses placeholders, as the current one does, and is checked against `tests/mocks/fake_unit_of_work.py`'s `FakeUnitOfWork` interface (`store=`, `committed`, `rolled_back`), which `tests/test_fake_unit_of_work.py` exercises. The recording renderer that the Command bullet names doesn't exist in `tests/` yet either. #279 adds it. | `grep -rn "UnitOfWork\|unit_of_work" workmain/`; `ls tests/mocks/` | Low |
| F9 | §6.2 has a Command bullet, and #279's Q5 cases are code in the command. `clients delete` asks for confirmation through `click.confirm` (`workmain/cli/commands/clients.py:163`), which `CliRunner`'s `input=` answers. A pick goes through `Renderer.pick` (`workmain/cli/output.py:310`), which a recording renderer answers. A command's paths are therefore driven by its arguments and by the answers to its prompts, and the row can state that without patching a service. | `workmain/cli/commands/clients.py:147`, `:163`; `workmain/cli/output.py:310`; #279 design study Q5 | Medium |
| F10 | §6.2 has rows for three of `docs/ARCHITECTURE.md` §1's five layers: application (Service), data (Repository fake, Repository loading) and surfaces (Renderer, Click parameter types, Command). Capabilities and shared code have no row, and among the surfaces, neither the daemon nor the Slack surface does. | `docs/standards/6-testing.md:70-76`; `docs/ARCHITECTURE.md` §1 | Medium |
| F11 | The issue's criterion "No test changes except those the get_db() resolution requires" is checked by `git diff --stat origin/dev -- tests/`. This branch is a `hotfix/*` cut from `origin/main` (`docs/standards/2-git.md` §2.2). The two trees are the same today, but the diff should be against `origin/main`. | `git diff --stat origin/main origin/dev` empty at `bd9b0dc` | Low |
| F12 | #254 says §6.1 and §6.2 carry rules that exist only because the EOD workflow runs commands as child processes: §6.1's child-process bullet and §6.2's `run_workmain` bullet. This restructure keeps both rules. #254 removes them when it removes that entry path. | #254 body; `docs/standards/6-testing.md:34`, `:76` | Low |

## 4. Options

### Record test (Q1)

F2 removes the reason for the later scope, so both options that keep it are defeated.

- **Option A — a conftest fixture that fails a later scope.** It keeps `get_db()` out of the test bodies, but it would add a new mechanism to run a step that proves nothing (F2). Defeated.
- **Option B — §6.1 names the later scope as an exception, with its reason.** It changes no test, but it keeps the step that proves nothing and adds another exception, which is the pattern #285 exists to remove. Defeated.
- **Option C — the record test drops the later scope.** §6.1 states the record test as three steps:
  - call the function
  - assert that it opened `record_scope()` once
  - assert the record through `db_session`

  §6.1 also says why a later failure is not part of the test: under the fixture, a scope opened after the record can't discard it. Each of the four tests deletes its later-scope block, and `tests/test_clockify_service.py` deletes its `_fail_a_later_scope` helper once nothing calls it.
  - **Pros:** it removes the conflict at its cause. It adds no fixture and no exception. Each test keeps its spy and its read, which are the steps that can fail.
  - **Cons:** it changes four tests. The issue's first criterion, "states how a test of an outside-action record fails a later scope", becomes wrong: the spec restates it in its §5, and the issue body is edited at close-out (`docs/standards/1-workflow.md` §1.2).

**Recommendation: C.** It is the only option F2 leaves standing.

### The 17 `TestCase` setups

There is one valid option. §6.1 names the kind as an exception: a `unittest.TestCase` class, which can't take a fixture, opens its seeding session with `get_db().get_session()` until its command group's conversion replaces it. The alternative was to convert the 60 tests to plain classes now. Ray decided otherwise when #288 was split, leaving them to the command-group issues under #198 (F4). Because the exception names a kind and no file, it applies to nothing once the last `TestCase` class is gone.

`tests/conftest.py` is also named, because it holds the fixtures that own the transaction (F3 (a)). That is the reason the rule itself rests on, so it isn't an extra exception.

### Defect-fix rule (Q2)

- **Option A — it stays in §6, and moves from §6.2 into §6's opening, next to the rule on recorded test evidence.** `docs/standards/README.md` gives §6 "writing a test, or recording test evidence". Rule 9 states which two runs a defect fix records, so it is a rule about evidence and not about writing a test. Anvil already reads `docs/standards/6-testing.md` end to end (`.claude/skills/session-start/references/anvil.md` read 6).
- **Option B — it moves to `docs/standards/1-workflow.md`, under §1.1 Implementation.** It is a step in the implementer's order of work. §1 states no other test evidence, though, so the form of the evidence would be in §6 and the duty to record it in §1.

**Recommendation: A.** The rule's subject is test evidence, which is §6's. The two citations in F6 are repointed to the rule's name.

### Provider routing (Q3)

- **Option A — a new rule for every test: "A test's result depends only on what the test sets up".** Provider routing becomes a recipe for this rule, and so does the Renderer's written width. §6.1's database isolation is the case of the rule that the fixture enforces. This adds a rule, so it needs Ray's approval (`docs/standards/1-workflow.md` §1.2).
- **Option B — provider routing stays a rule, scoped to "a test that builds a real `ProviderManager`".** It stays in the rules list, which departs from the issue's list of recipes, and it adds nothing new.

**Recommendation: A.** F7 shows two forms that already follow this unstated rule. Stating it once gives each of them a reason, and gives the next case of the same kind an answer without another bullet. That is the defect the issue describes.

### Table coverage (Q4)

- **Option A — rows only for the forms §6.2 states today.** Each row is labelled with its `docs/ARCHITECTURE.md` layer. A layer with no row is tested by the principle (the issue's "What this issue changes" item 1).
- **Option B — a row for every layer in `docs/ARCHITECTURE.md` §1.** The capability, shared, daemon and Slack-surface rows would be new forms, and §2 records that this study did not look at how those layers are tested.

**Recommendation: A.** B adds forms that no issue asked for and no recon has measured. If they are wanted, they become an issue of their own (`docs/standards/1-workflow.md` §1.2).

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | F2 shows that, under the test fixture, failing a later scope can't change whether a record test passes. Should §6.1's record test drop the later scope, keeping the spy and the read through `db_session`, with each of the four record tests deleting its later-scope block (Option C)? That also makes the issue's first criterion wrong, so the spec restates it. Options A and B keep a step that proves nothing. Recommendation: C. | |
| Q2 | Does the defect-fix rule (§6.2 rule 9) stay in §6, moved into its opening next to the rule on recorded test evidence (Option A)? Or does it move to `docs/standards/1-workflow.md` §1.1 (Option B)? Recommendation: A. | |
| Q3 | §6.2 rule 7 (provider routing) is a recipe in the issue's list, but no rule in §6.2 is one it meets (F7). Should §6.2 add a rule for every test, "A test's result depends only on what the test sets up", with provider routing and the Renderer's width as recipes for it (Option A)? Or should provider routing stay a rule scoped to tests that build a `ProviderManager` (Option B)? A is a new rule and needs your approval. Recommendation: A. | |
| Q4 | Does §6.2's table carry rows only for the forms it states today, each labelled with its layer, leaving any other layer to the principle (Option A)? Or does it carry a row for every layer in `docs/ARCHITECTURE.md` §1 (Option B)? Recommendation: A. | |

## 6. Disposition

- Promoted to:
- Superseded by:

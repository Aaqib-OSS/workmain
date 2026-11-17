# Testing Standard Rules — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261116
**Originating item:** Issue #285

---

## 1. Purpose

Issue #285 restructures `docs/standards/6-testing.md` §6.1 and §6.2 so that each states the rule its forms follow from, and so that §6.1's rule on `get_db()` and its record-test bullet cannot conflict. The issue leaves two questions to this study: whether the defect-fix rule (§6.2 rule 9) moves to `docs/standards/1-workflow.md`, and whether the record tests change or the rule allows their form.

Ray's answers of 20261117 asked for four more things before the spec:

- what the ban on `get_db()` in tests protects today
- §6.1's governing rule, with the `get_db()` guidance derived from it
- a measurement of which tests depend on something they do not set up
- which branch type this work takes

## 2. Scope of the read

The first pass was measured on `hotfix/issue-285-testing-standard-rules` at `bd9b0dc`, cut from `origin/main`, 20261116. `git diff --stat origin/main origin/dev` was empty, so the two trees were the same. The second pass was measured at `659a011`, 20261117. It differs from `bd9b0dc` only by this file.

- **Read in full:**
  - `docs/standards/6-testing.md`; `docs/standards/4-database.md` §4.2 and §4.3
  - `tests/conftest.py`; `tests/test_database_isolation.py`
  - `workmain/database/connection.py` (`session_scope`, `record_scope`, `scope_open`)
  - the four record tests the issue names, and the setup of every `unittest.TestCase` class that calls `get_db()`
  - `.claude/skills/closeout/SKILL.md` P11, and `.claude/skills/closeout/references/hotfix.md`
- **Searched:**
  - every `get_db()` in `tests/`, and every other way a test opens a session: `DatabaseConnection()`, `SessionLocal(`, `.session_scope(`, `.record_scope(`, `.get_session(`, and an aliased import
  - every live citation of `docs/standards/6-testing.md`, `§6`, `§6.1` and `§6.2` in `*.md`, `*.py` and `*.json`, with `CHANGELOG.md` and `docs/archive/` excluded
  - every open issue body that cites `§6.N`
  - #279's design study on `feature/issue-279-clients-tasks-unit-of-work`, Q5, and the bodies of #198, #287 and #288
  - the history of the `get_db()` ban: `git log -S` over `docs/` for the ban's text, "Never call `get_db()`", the diff of `c283f20`, and `docs/archive/specs/TEST_DATABASE_ISOLATION_SPEC.md`
  - the three earlier `hotfix/*` merges that changed only `tests/` and docs (#271, #273, #286)
  - open issues for a §2.2 branch-type gap
- **Measured (F15):** five runs of the full suite through a measuring plugin, plus one targeted run per changed variable. The plugin and its output stay in the session scratchpad and are not committed.
- **Not read:** how capabilities (`workmain/ai/`, `workmain/integrations/`, `workmain/templates_engine/`), the daemon, workflows and the Slack surface are tested today. §6.2 states no form for them, and the answer to Q4 leaves them to the principle.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The conflict the issue states holds. §6.1 says "Never call `get_db()` or `db.get_session()` in a test", and names only `tests/test_database_isolation.py` and `tests/test_unit_of_work.py` as exceptions. Its record-test bullet says "call it, fail a later scope, and assert the record through `db_session`", and all four record tests open that later scope with `get_db().session_scope()`. | `docs/standards/6-testing.md:28`, `:30`, `:33`; `tests/test_clockify_service.py:109` (in the helper `_fail_a_later_scope`), `tests/test_ai_costs.py:646`, `tests/test_gdrive.py:273`, `tests/test_slack.py:602` | High |
| F2 | **In the test fixture, failing a later scope can't change whether a record test passes.** §6.1's own table says a `rollback()` discards that session's writes "and every commit a session opened after it made in the meantime". A scope opened after the record has closed therefore can't discard the record. A probe (scratch, not committed) ran three record writes through the suite's fixtures and read each through `db_session` before and after failing a later `session_scope()`. Committed in `record_scope()`: 1 before, 1 after. Flushed and closed without a commit: 0 and 0. Flushed and left open: 1 and 1. In every case the read before the later failure gives the same result as the read after it. Two other things carry the evidence: the `record_scope` spy each test already wraps around the call (`patch.object(DatabaseConnection, 'record_scope', autospec=True, side_effect=...)`), and the read through `db_session` after the function returns, which fails for a record that was never committed. Nothing in the fixture detects a record session left open without a commit: every session shares one connection, so `db_session` sees that row's flush. | `docs/standards/6-testing.md:24`; `tests/conftest.py` `_isolated_database` (`join_transaction_mode="create_savepoint"`); the four tests in F1; probe output `committed: before 1 after 1`, `uncommitted+closed: before 0 after 0`, `uncommitted+open: before 1 after 1` | High |
| F3 | `git grep -n 'get_db()' tests/` prints 49 lines in six kinds. **(a)** `tests/conftest.py`: 4 lines, the fixtures that own the transaction. 3 are calls and `:124` is a docstring. **(b)** `tests/test_database_isolation.py`: 8 lines, 7 calls plus the docstring at `:4`. **(c)** `tests/test_unit_of_work.py`: 14 lines, 13 calls plus the docstring at `:5`. **(d)** The four record tests in F1. **(e)** 18 lines in 17 `unittest.TestCase` classes, which open their seeding session in `setUp` with `get_db().get_session()`: 17 calls plus the docstring at `tests/test_ai_arguments.py:268`. **(f)** `tests/test_ai_costs.py:662`, `def fake_get_db():`, which matches the pattern but is not a call. | `git grep -c 'get_db()' tests/` | High |
| F4 | All 17 classes in F3 (e) are command tests of a group that has an open conversion issue. Each runs `CliRunner().invoke` on a group: `meetings` (#208), `notes` (#209), `reports` (#212, including `tests/test_ai_arguments.py`'s `TestReportTypeFiltersRows`), `slack` (#214) and `time` (#216). They hold 60 tests, the same 60 that #288 says "the command-group issues under #198 convert". A `TestCase` method can't take a pytest fixture, so `db_session` can't reach it. | An AST walk of `tests/test_*.py` for `TestCase` classes whose source holds `get_db()`, with each class's `invoke(<group>` targets; #288 body | Medium |
| F5 | The issue's `get_db()` criterion is checked by `git grep -n 'get_db()' tests/`. It reaches every session-opening call: no test aliases `get_db`, or opens a session through `DatabaseConnection()`, `SessionLocal(` or `connection.db`. The one `DatabaseConnection()` (`tests/test_ai_costs.py:666`) is inside a patched `get_db` and opens nothing. The search also matches docstrings and `def fake_get_db():`, so the results table must say for each hit whether it is a call. | The searches in §2 | Low |
| F6 | Two live documents cite §6.2 rule 9 by number, but the issue names only the first: `.claude/skills/session-start/references/anvil.md:43` and `docs/dev/results/_TEMPLATE_RESULTS.md:63`. Two open issues cite rule 5 by number: #287 three times and #288 once. #288 also says "Rule 4 adds why", a bare number that the issue's search for "§6.2 rule" does not find. No other live text cites a §6 rule by number. The section citations stay correct after the restructure, provided the loading recipe stays in §6.2 and the record-test statement in §6.1: `docs/standards/4-database.md:35` ("tests follow §6.1"), `:64` ("§6.2 states how the loading is tested"), `:68` ("tested at the function that writes it (§6.1)"), and `tests/test_time_tracking.py:7` (§6.1). The open issues that cite §6.2 by section (#205–#216, #251, #256, #265, #279–#282, #73, #45) cite the service, command and renderer forms, and the restructure keeps all three. | The searches in §2 | Medium |
| F7 | §6.2 rule 7 (provider routing) is listed in the issue as a recipe, "how to meet a rule above". No rule in §6.2 is one it meets. Its reason is that a test must not rely on `config/ai_settings.json`, "which `workmain providers set default` changes in ordinary use". The Renderer bullet sets the width so that "`COLUMNS` cannot change the outcome", for the same kind of reason, and states no rule either. | `docs/standards/6-testing.md:64`, `:73` | Medium |
| F8 | No service takes a unit of work on `main` yet. #279 is the first conversion. The new example therefore uses placeholders, as the current one does, and is checked against `tests/mocks/fake_unit_of_work.py`'s `FakeUnitOfWork` interface (`store=`, `committed`, `rolled_back`), which `tests/test_fake_unit_of_work.py` exercises. The recording renderer that the Command bullet names doesn't exist in `tests/` yet either. #279 adds it. | `grep -rn "UnitOfWork\|unit_of_work" workmain/`; `ls tests/mocks/` | Low |
| F9 | §6.2 has a Command bullet, and #279's Q5 cases are code in the command. `clients delete` asks for confirmation through `click.confirm` (`workmain/cli/commands/clients.py:163`), which `CliRunner`'s `input=` answers. A pick goes through `Renderer.pick` (`workmain/cli/output.py:310`), which a recording renderer answers. A command's paths are therefore driven by its arguments and by the answers to its prompts, and the row can state that without patching a service. | `workmain/cli/commands/clients.py:147`, `:163`; `workmain/cli/output.py:310`; #279 design study Q5 | Medium |
| F10 | §6.2 has rows for three of `docs/ARCHITECTURE.md` §1's five layers: application (Service), data (Repository fake, Repository loading) and surfaces (Renderer, Click parameter types, Command). Capabilities and shared code have no row, and among the surfaces, neither the daemon nor the Slack surface does. | `docs/standards/6-testing.md:70-76`; `docs/ARCHITECTURE.md` §1 | Medium |
| F11 | The issue's criterion "No test changes except those the get_db() resolution requires" is checked by `git diff --stat origin/dev -- tests/`. This branch is a `hotfix/*` cut from `origin/main` (`docs/standards/2-git.md` §2.2). The two trees are the same today, but the diff should be against `origin/main`. | `git diff --stat origin/main origin/dev` empty at `bd9b0dc` | Low |
| F12 | #254 says §6.1 and §6.2 carry rules that exist only because the EOD workflow runs commands as child processes: §6.1's child-process bullet and §6.2's `run_workmain` bullet. This restructure keeps both rules. #254 removes them when it removes that entry path. | #254 body; `docs/standards/6-testing.md:34`, `:76` | Low |
| F13 | **The `get_db()` ban protects nothing today.** Before #136, its stated reason was the fixture of that time: "A CLI command invoked through `CliRunner` opens its *own* session and transaction, so rows flushed-but-uncommitted by `db_session` are never visible to it." #136 replaced that fixture with the transaction fixture, and in doing so deleted the reason and kept the ban (`c283f20`, 20261012). #136's spec says of the `TestCase` sessions: "Under this fixture those sessions join the test's transaction, so they are harmless until then." `db_session` is itself `get_db().get_session()` (`tests/conftest.py:176`), so a session a test opens through `get_db()` is the same kind of object, in the same transaction, with the same last-in, first-out duty. The one thing the ban still gives is a single way for a test to get its seeding session, and rule 5 already gives that: `db_session` is a fixture in `tests/conftest.py`, so a test takes it as an argument. | `git show c283f20 -- docs/DEVELOPMENT_STANDARDS.md`; `docs/archive/specs/TEST_DATABASE_ISOLATION_SPEC.md:25`, `:45`; `tests/conftest.py:170-181` | High |
| F14 | **Every kind in F3 follows from one governing rule and rule 5.** The proposed rule is under § The governing rule for §6.1, below. Taking each kind in F3 in turn: (a) `tests/conftest.py` defines the fixtures, and rule 5 governs tests. (b) and (c) `tests/test_database_isolation.py` and `tests/test_unit_of_work.py` call `get_db()`, `session_scope()`, `record_scope()` and `close()` because those are the code under test, which is what every test does. `TestTestDatabaseBuild` builds its own engine because `build_test_database` runs outside any transaction. It meets the governing rule by undoing its changes before it ends (`DROP TABLE IF EXISTS rebuild_probe` in `finally`, and a rebuild to head). (d) After Q1, the record tests have no `get_db()` call. (e) The 17 `TestCase` setups break rule 5, not isolation: their sessions join the transaction. That is temporary non-compliance, which #208, #209, #212, #214 and #216 remove. (f) is not a call. | F3, F4, F13; `tests/test_database_isolation.py:103-125` | High |
| F15 | **Tests that depend on something they don't set up.** The results are in § Measurement for Q3, below. Of 1707 tests, 24 changed outcome, or were shown by reading to depend on something outside them. 12 of those depend on terminal width, which #198 already tracks. 12 are tracked by no issue. | § Measurement for Q3 | High |
| F16 | **The bare suite makes billed calls.** `tests/test_ai_providers_live.py` calls the Anthropic and Google APIs whenever `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` are set, and `.env` sets both. Its docstring says so, and it skips when a key is absent. Five tests made outside connections on 20261117. | `tests/test_ai_providers_live.py:1-30`; probe network records | Medium |
| F17 | **No branch type in `docs/standards/2-git.md` §2.2 fits a change to `tests/` that alters no application code.** `chore/*` lists `docs/**`, standards, `.claude/` and dev tooling. It admits `tests/**` only when the change is "mechanically proven behaviour-neutral (e.g. AST-equality)", and deleting a later-scope block (Q1) changes what four tests do. `hotfix/*` admits the change. §2.2 says "A merge carrying application code — from `dev` or `hotfix/*` — is a release", and is silent on a `hotfix/*` that carries none. `/closeout` applies the release to every `hotfix/*` regardless: P11 requires the bump, the `CHANGELOG.md` section and the tag on that branch type, `references/hotfix.md` step 1 bumps a patch, and §2.6 requires a service restart. In practice the release happened every time. #271, #273 and #286 changed only `tests/`, docs and `workmain/__version__.py`, and were released as v1.58.1, v1.58.2 and v1.58.5. No open issue covers the gap. | `docs/standards/2-git.md` §2.2, §2.6; `.claude/skills/closeout/SKILL.md` P11; `.claude/skills/closeout/references/hotfix.md` step 1; `git diff --name-only` of merges `f6dbee5`, `2d2f3f5`, `91102e0`; `gh issue list --search` for "branch type tests", "chore tests", "release version bump", "§2.2" | Medium |

### Measurement for Q3

**Method.** A pytest plugin, loaded before `tests/conftest.py`, recorded for each test every read of:

- the clock: `date.today`, `datetime.now`, `datetime.today` and `datetime.utcnow`
- an environment variable whose value came from the shell or `.env`, or was absent and not removed by the test (`DB_*` keys are left out, because the fixture owns them)
- a path under `~/.workmain/` or `config/*.json`, through `open` and `os.stat`
- an outside network connection, other than the test database

It also attributed each read to the code that made it: the test, application code, or a library. Reads are exposure, not dependence. A test depends on an input when changing that input changes its outcome, so the suite was then run with each input changed:

| Input | Changed to | Exposed tests | Outcome changed | Tracked by |
| --- | --- | --- | --- | --- |
| Python clock | Sunday 2027-01-03 00:30, then Thursday 2027-03-11 14:00 | 799 (83 read it in the test body; the rest through application code or an ORM default) | 0 | — |
| `COLUMNS` | 37 | 189 | 12, in `tests/test_ai_arguments.py`, `tests/test_gdrive.py`, `tests/test_notifications_commands.py`, `tests/test_provider_foundation.py`, `tests/test_report_correction.py`, `tests/test_report_history.py` and `tests/test_slack_channel_config.py`. Two of them also depend on test order: the row ID they look for in a table is cut short at narrow widths, and the ID depends on how many rows earlier tests inserted, because a rollback does not reset a sequence. | #198 ("No test depends on terminal width"), through the conversions of `reports`, `gdocs`, `notifications`, `providers` and `slack` |
| Other `.env` values, and `EDITOR`, `VISUAL`, `LINES`, `TERM`, `LANG`, `FORCE_COLOR` | Each changed or removed, one at a time | 478, across all variables | 1: `WORKMAIN_EXPECTED_HOURS`, `tests/test_notification_engine.py::TestCoverageCheck::test_low_hours_flagged` | none |
| API keys | Set empty | 5 | 5 skipped instead of calling the live service (F16) | none |
| `~/.workmain/` | `HOME` set to an empty directory | 6 | 3: `tests/test_gdrive.py::TestGDocsCLI::test_10_upload_all_dry_run` (`integrations/gdrive/token.json`), and `tests/test_slack_channel_config.py::TestSlackSetWorkspace::test_slack_set_workspace_shows_config` and `::test_slack_set_workspace_no_writes` (`integrations/slack/config.json`) | none |
| `config/ai_settings.json` routing | Primary and fallback swapped on all five call types that have a fallback, in a throwaway worktree | 81 | 0 | — |
| The `.env` file | Absent (the same worktree run) | 1 | 1: `tests/test_database_isolation.py::TestTestDatabaseGuard::test_a_run_naming_another_database_stops_before_any_test` reads `DB_NAME` from `.env` with `dotenv_values` | none |
| Network, `127.0.0.1:11434` | Not changed; by reading | 3 | 3 by reading: `tests/test_provider_foundation.py`'s `test_ollama_provider_generate_raises_unavailable`, `test_ollama_provider_test_connection_returns_false` and `test_ollama_provider_check_availability_returns_unavailable` assert that Ollama is unavailable. They pass only while nothing listens on that port. | none |

No test wrote under `~/.workmain/` or `config/`.

**Limits.**

- The clock change moved Python's clock but not the database's. One column (`workmain/database/models.py:558`) takes `server_default=func.now()`, and SQL `CURRENT_DATE` was not changed.
- No run crossed midnight.
- Config files other than routing were read but not changed. Ordinary use writes `config/template_aliases.json`, `config/meeting_templates.json` and `templates/` too (`alias_manager.py:180`, `meeting_templates.py:45`, `templates.py:389`).
- The singletons `get_provider_manager`, `get_alias_manager` and `get_config` read their file once, so a test that reaches a cached instance after the first read shows no read of its own.

**Reading.** Compliance is wide. 1683 of 1707 tests showed no dependence. Of the 24 that did, the 12 width dependences are tracked. The other 12 are in five forms, and none is tracked: an environment value, `~/.workmain/`, the `.env` file, a local port, and the live provider services.

## 4. Options

**Ray, 20261117: #285 adds no exceptions.** A rule's apparent exception either follows from the section's governing rule, or is temporary non-compliance. Temporary non-compliance is tracked by the open issue that removes it and is never written into the standard. This applies to every form the study or the spec touches.

### Record test (Q1)

Answered: Option C. Each of the four record tests drops its later-scope block, and `tests/test_clockify_service.py` drops `_fail_a_later_scope`. §6.1 states that the fixture can't show a record surviving its caller's failure. The `record_scope` spy is therefore the evidence for that property, and the read through `db_session` is the evidence that the record was written.

### The governing rule for §6.1

- **Proposed rule:** *Nothing a test does outlives it, and nothing it sees was left by another test.*
- **How every test meets it:** the fixture's transaction, rolled back at the end of each test. Every session opened through `get_db()` joins that transaction, so such a session meets the rule.
- **What follows from the rule** (F13, F14):
  - **Which session a test uses** is rule 5's question, not isolation's. `db_session` is a fixture in `tests/conftest.py`, so a test that seeds or reads takes it as an argument.
  - **A test whose subject is the session machinery** calls that machinery: `get_db()`, `session_scope()`, `record_scope()`, `close()`. That is a test calling what it tests, so it is no exception.
  - **A test whose subject runs outside any transaction** (the build) meets the rule by undoing its own changes before it ends.
  - **The rule is broken by:** closing the connection, replacing the session factory, building an engine the test does not dispose of with its changes undone, reaching a child process, and doing database work on another thread. Each one leaves the transaction, so each is refused or patched, as §6.1 says today.
  - **A record test** can't show survival in the fixture (Q1).
  - **The 17 `TestCase` setups** keep the rule, and are non-compliance with rule 5 that #208, #209, #212, #214 and #216 remove.
- **Rewritten second criterion** (Ray, 20261117): every `get_db()` call in `tests/` either complies with §6.1, or is in a test that an open issue converts. The results table names that issue for each such hit.

### Defect-fix rule (Q2)

Answered: Option A. The rule moves to §6's opening, next to the rule on recorded test evidence.

### Provider routing (Q3)

Ray, 20261117: Option A in principle, after measurement. The measurement above shows compliance is wide.

- **The rule goes in as stated:** *A test's result depends only on what the test sets up.* Provider routing and the Renderer's written width become recipes for it.
- **Its untracked violations become one new issue,** under Ray's design rule above. The issue's opening is proposed in § The issue for the untracked violations, below.

### Table coverage (Q4)

Answered: Option A.

### Branch type (Q5)

F17: §2.2 has no type that fits this change, and Ray asked for that to be raised as a §2.2 gap rather than resolved here. #285 itself still needs a type before the spec. Two remain:

- **Option A — `hotfix/*`, as cut.** It is the one type whose rules admit a change to `tests/` that is not behaviour-neutral. `/closeout` releases it: a patch bump, a `CHANGELOG.md` section, a tag, a Release, and a service restart for application code that hasn't changed. This is the practice #271, #273 and #286 followed.
- **Option B — `chore/*`.** It needs the spec to argue that deleting a test step is "behaviour-neutral" under the `tests/**` exception. AST-equality, the exception's own example of a proof, can't show that, so the argument would stretch the exception to fit. Defeated.

**Recommendation: A.** It is what §2.2 and `/closeout` give today. The release it produces is the gap, which belongs to the §2.2 issue, not to #285.

### The issue for the §2.2 gap

- **Defect or gap:** gap. §2.2 doesn't say which branch type takes a change to `tests/` that is not behaviour-neutral and changes no application code, or whether its merge is a release. `/closeout` releases every `hotfix/*`. Three such merges were released (F17).
- **Criteria it would need:**
  - §2.2 states the branch type for that change, and whether its merge is a release. Checked by a stated reading by Ray of §2.2.
  - `/closeout`'s preconditions and steps for that type agree with §2.2. Checked by a stated reading by Ray of P11 and the type's reference.
- **An open issue it could join:** none was found.

### The issue for the untracked violations

- **Defect or gap:** defect, once Q3's rule is in, because the standard will say every test depends only on what it sets up. The 12 untracked tests in § Measurement for Q3 each depend on one of five things: an environment value, `~/.workmain/`, the `.env` file, a local port, or the live provider services.
- **Criteria it would need:**
  - No test's outcome changes when `HOME` is an empty directory, when each `.env` value other than `DB_*` is changed, or when `.env` is absent. Checked by `pytest` reporting 0 failed under each change.
  - No test reaches a network address other than the test database. Checked by a run with outside connections refused, reporting 0 failed.
- **For that issue to decide:** whether the live provider tests (F16) leave the application suite for a suite of their own, reached by their own path, as `docs/standards/6-testing.md`'s opening already allows.
- **An open issue it could join:** none was found. #198 covers width only.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | F2 shows that, under the test fixture, failing a later scope can't change whether a record test passes. Should §6.1's record test drop the later scope, keeping the spy and the read through `db_session`, with each of the four record tests deleting its later-scope block (Option C)? That also makes the issue's first criterion wrong, so the spec restates it. Options A and B keep a step that proves nothing. Recommendation: C. | Ray, 20261117: Option C. `tests/test_clockify_service.py` also drops `_fail_a_later_scope`. §6.1 states that the fixture can't show a record surviving its caller's failure, so the spy is the evidence for that property and the `db_session` read is the evidence that the record was written. The spec restates the issue's first criterion, and the issue body is edited at close-out. |
| Q2 | Does the defect-fix rule (§6.2 rule 9) stay in §6, moved into its opening next to the rule on recorded test evidence (Option A)? Or does it move to `docs/standards/1-workflow.md` §1.1 (Option B)? Recommendation: A. | Ray, 20261117: Option A. |
| Q3 | §6.2 rule 7 (provider routing) is a recipe in the issue's list, but no rule in §6.2 is one it meets (F7). Should §6.2 add a rule for every test, "A test's result depends only on what the test sets up", with provider routing and the Renderer's width as recipes for it (Option A)? Or should provider routing stay a rule scoped to tests that build a `ProviderManager` (Option B)? A is a new rule and needs your approval. Recommendation: A. | Ray, 20261117: Option A in principle, after measurement. The measurement is § Measurement for Q3. Compliance is wide: 24 of 1707 tests showed a dependence, 12 of them on width, which #198 tracks. Awaiting Ray's approval of the rule, and his decision on opening the issue for the other 12 (§4 The issue for the untracked violations). |
| Q4 | Does §6.2's table carry rows only for the forms it states today, each labelled with its layer, leaving any other layer to the principle (Option A)? Or does it carry a row for every layer in `docs/ARCHITECTURE.md` §1 (Option B)? Recommendation: A. | Ray, 20261117: Option A. |
| Q5 | No branch type in `docs/standards/2-git.md` §2.2 fits a change to `tests/` that alters no application code (F17). Does #285 stay `hotfix/*` and take the patch release `/closeout` gives every `hotfix/*` (Option A)? `chore/*` (Option B) would stretch its `tests/**` exception. And is the §2.2 gap opened as its own issue (§4 The issue for the §2.2 gap)? Recommendation: A, and open the gap issue. | |
| Q6 | Is §6.1's governing rule "Nothing a test does outlives it, and nothing it sees was left by another test", with the derivations in §4 The governing rule for §6.1? Under it, the `get_db()` ban becomes rule 5's guidance on which session a test takes, and nothing in `tests/` is an exception. Recommendation: yes. | |

## 6. Disposition

- Promoted to:
- Superseded by:

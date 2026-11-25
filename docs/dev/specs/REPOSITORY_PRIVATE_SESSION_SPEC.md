# Repositories hold their session privately — Spec

**Status:** Approved
**Author:** Spanner
**Date:** 20261125
**Read at:** `1f625e5`
**Branch:** `feature/issue-283-repository-private-session` (from `dev`)
**Target release:** v1.62.0
**Originating item:** Issue #283
**Design study:** `../design/DESIGN_REPOSITORY_PRIVATE_SESSION.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261124 | Ray | Branch type `feature/*`: the change edits `workmain/**` and `tests/**`, and a rename is not provable behaviour-neutral by AST equality (`docs/standards/2-git.md` §2.2). | Branch field. |
| 20261125 | Ray | No rule is added to `docs/standards/4-database.md` §4.3. Its first bullet already states that all data access goes through a repository, so only the example changes (design study Q1, withdrawn). | DR5, Step 2. |
| 20261125 | Ray | Criterion 2's search becomes a standing step in `.github/workflows/tests.yml`'s `session-rules` job, on this branch (design study Q2). | DR6, Step 3, AC2.2, AC2.3. |
| 20261125 | Ray | AC1.1's search also becomes a standing `session-rules` step, in DR6's form. The `_session` step alone cannot see a repository written from the old pattern: one that keeps a public `self.session`, such as #161's `ProjectsRepository`, passes it, and DR4's test misses it unless the class is in `UnitOfWork.REPOSITORIES`. AC1.1 runs once, at close-out. | DR6, Step 3, AC1.4, AC1.5, §7. |
| 20261125 | Ray | The criterion that the CI step runs (AC2.2, as first drafted) had no point where it is checked: it needs the pull request's CI run, which exists only from `/closeout` feature step 3, after Step 4 writes the results artifact. Each standing step now has a local criterion, checked at Step 4 (AC1.4, AC2.2), and a run criterion, checked at feature step 3 and recorded at feature step 4 (AC1.5, AC2.3). The run criteria are written `Carried` to #283 at Step 4, because preflight P6 runs before the push and accepts only `Met` or `Carried`. That follows the precedent in `docs/archive/results/CI_WORKFLOW_RESULTS.md` (#297). | §5, Step 4. |
| 20261125 | Spanner | The issue's second criterion's check misses a read by name (`getattr(x, '_session')`) and `scripts/`, which builds repositories (design study F5, F13). It also matches only lowercase names, and its `grep -v` drops a whole line that holds `self._session` and another read. AC2.1 restates it as one PCRE search over every form. The issue body's edit is made at close-out (`docs/standards/1-workflow.md` §1.2). | AC2.1. |
| 20261125 | Caliper | 2, Spec defect, non-blocking: AC3.1's checks can't see the rewrite the design study suggests for `test_repositories_built_on_its_session_while_entered`: a test subclass of a repository that records the session it was built on (F7). A subclass that reads `self._session` passes both AC2.1's search (`self._session` is excluded) and `grep '\.session\b'`, even though DR2 forbids that read. Once Step 1 adds such a subclass, R5's "No class subclasses a repository" also stops being true. Fix: add to AC3.1 that `grep -nE '\bself\._session\b' tests/test_unit_of_work.py` returns no hits. A broader `_session\b` would also match the file's many `db_session` uses. | AC3.1 adds that check. DR2 states that a recording subclass records the argument in its constructor and never reads `self._session`. R5 is dated to the **Read at:** commit and names the subclasses Step 1 may add. |
| 20261125 | Caliper | 2, Spec defect, non-blocking: AC2.2's match case says to add "a `repo._session` line added to a module under `workmain/`". `git grep` searches tracked files only, so if the line goes in a new, untracked module the step prints `none found` and exits 0, and the check looks failed when it isn't. Say "an existing tracked module". This pass appended the line to `workmain/cli/interface.py`, and it was matched (exit 1). | AC2.2: the line is appended to an existing tracked module, with the reason. |
| 20261125 | Caliper | 1, Spec defect, non-blocking: R10 says no file in `docs/dev` names the attribute. Its own command, run at `9e6f28d`, returns lines from the design study and from the spec itself. The claim should exclude the artifact set. | R10 excludes this spec and its design study. |
| 20261125 | Caliper | 2, Spec defect, non-blocking: §6 says "The results artifact re-measures at `1f625e5`", but implementation runs on the branch tip. It should say "at the branch tip before Step 1". `workmain/`, `tests/`, `docs/standards/` and `.github/` are unchanged from `287db27` through `9e6f28d`, so the two give the same count. Collection at `9e6f28d` gives 1854 items, which matches R14 (1850 passed + 1 xfailed + 3 xpassed). | §6: re-measured at the branch tip before Step 1. |
| 20261125 | Caliper | 4, Standards gap, non-blocking: §1.2 requires a call-site search of the whole repository. #188 forbids any document citing `scripts/baseline/`, and the spec leaves that directory out of R4 and R5 without saying the rename leaves it working. No rule says how a spec covers a call site in restricted code. | Recorded. It becomes an issue only when Ray says so. The pass's sentence describing what the restricted scripts do is left out of this row, because #188 bars any document from citing them. |
| 20261125 | Caliper | n/a, Existing defect, non-blocking: the two existing `session-rules` steps use `if grep ...; then exit 1; fi`, so a `grep` error (exit 2) prints `none found`. The spec's §7 already records this. | Recorded in §7. It becomes an issue only when Ray says so. |
| 20261125 | Caliper | Pass at 9e6f28d, full: 34 items checked, 0 blocking, 6 non-blocking. | n/a |
| 20261125 | Ray | Spec approved. | **Status:** Approved. |
| 20261125 | Anvil | R5's list of `'session'` string literals omits `automation/session_param_check.py:40`, which its own command returns at `1f625e5` and at the branch tip. The line compares a syntax-tree parameter name, so R5's conclusion holds and no step changes. Spanner's recon search had excluded that file; the command written into R5 does not. | R5 lists the third literal. **Status:** back to `Draft` in the same commit (`docs/standards/1-workflow.md` §1.1 Approval), for Ray's approval again. |
| 20261125 | Ray | Spec approved again, with R5's correction. | **Status:** Approved. |
| 20261125 | Caliper (post-implementation) | No findings. | n/a |

---

## 1. Scope

**In scope:**

- The 12 repository modules in `workmain/database/repositories/`: each repository holds its session as `self._session` instead of `self.session`.
- `tests/test_unit_of_work.py`: the four tests that read a repository's `session` (R4) get the session another way, and one new test shows no repository has a `session` attribute.
- `docs/standards/4-database.md` §4.3: the repository example's code block.
- `.github/workflows/tests.yml`: two new steps in the `session-rules` job.
- The results artifact, `docs/dev/results/REPOSITORY_PRIVATE_SESSION_RESULTS.md`.

**Out of scope:**

- The seven classes outside the repositories that hold `self.session` (R7). They are not repositories, and #198's conversion issues own them.
- `workmain/services/unit_of_work.py`. It builds each repository with a positional session (`repository_class(session)`), which the rename leaves working, and it holds no session attribute of its own.
- `tests/mocks/fake_unit_of_work.py`. Its fakes hold no `session` (design study F8).
- Any repository method, signature, docstring or constructor parameter. The constructor parameter stays `session`.
- §4.3's rule text. No rule is added (Decision Log, 20261125).
- The two existing `session-rules` steps, including how they treat a `grep` error (§7).
- `scripts/baseline/`, restricted by #188.

## 2. Verified current state

Verified at `1f625e5`. `workmain/`, `tests/`, `docs/standards/` and `.github/` are unchanged from `287db27`, where the design study read them.

| # | Claim | Evidence (file:line, symbol) |
| --- | --- | --- |
| R1 | 12 repository classes, each setting `self.session = session` in `__init__`: `AiCostRepository`, `ClientRepository`, `EmailRepository`, `GDriveRepository`, `MeetingsRepository`, `NotesRepository`, `NotificationConfigRepository`, `ReportsRepository`, `ScheduleExceptionRepository`, `SystemStateRepository`, `TaskStatusRepository`, `TimeEntriesRepository`. `NotificationConfigData` in the same directory is a data holder with no session. | `grep -rnE 'self\.session *=' workmain/database/repositories/`; `grep -nE '^class ' workmain/database/repositories/*.py` |
| R2 | `self.session` occurs 202 times across those 12 files, assignments included. | `grep -rnE 'self\.session\b' workmain/database/repositories/ \| wc -l` |
| R3 | `UnitOfWork.REPOSITORIES` maps 12 names to exactly the 12 classes in R1, and `__enter__` builds each as `repository_class(session)`. | `workmain/services/unit_of_work.py` `UnitOfWork.REPOSITORIES`, `UnitOfWork.__enter__` |
| R4 | Call sites of a repository's `session` attribute outside its own class, found by ``git grep -nE '\b[A-Za-z_][A-Za-z0-9_]*(\(\))?\.session\b' -- workmain tests automation scripts ':!scripts/baseline' ':!workmain/database/repositories' \| grep -vE '\bself\.session\b'``. Each was read and is a read through a repository: `tests/test_unit_of_work.py:107` `TestUnitOfWork::test_repositories_built_on_its_session_while_entered` (`repository.session is opened[0]`); `:142` `TestUnitOfWork::test_repositories_absent_after_commit_raises` (`mp.setattr(uow.system_state.session, 'commit', ...)`); `:262` `TestRecordUnitOfWork::test_record_runs_on_record_scope` and `:268` `TestRecordUnitOfWork::test_default_runs_on_session_scope` (`uow.system_state.session.execute(text('SHOW lock_timeout'))`). | the search; `tests/test_unit_of_work.py` |
| R5 | No read by name: no `getattr`, `vars` or `__dict__` read of `'session'`, and the only `'session'` string literals are a pytest fixture scope (`tests/conftest.py:115`), the hidden-name tuple of `TestUnitOfWork::test_exposes_no_session_or_transaction_control` (`tests/test_unit_of_work.py:148`), which checks the unit of work, not a repository, and the parameter-name test in `automation/session_param_check.py` `_takes_session` (`:40`), which compares a syntax-tree argument's name. No class subclasses a repository at the **Read at:** commit; Step 1 may add test subclasses for DR3, which DR2 bars from reading `_session`. | ``git grep -nE "getattr\([^)]*['\"]session['\"]\|vars\(\|__dict__\[['\"]session" -- workmain tests automation scripts ':!scripts/baseline'``; ``git grep -nE "['\"]session['\"]" -- workmain tests automation``; ``git grep -nE 'class \w+\(\w*Repository\)' -- workmain tests`` |
| R6 | Inside the repositories, the reads that cross to another repository are `ClientRepository`'s `SystemStateRepository(self.session)` in `set_active`, `clear_active` and `get_active`. They read the class's own attribute, so they rename with it. | `workmain/database/repositories/client_repository.py:172`, `:185`, `:194` |
| R7 | Seven modules outside the repositories hold `self.session` on classes of their own: `workmain/ai/note_condenser.py`, `workmain/ai/prompt_builder.py`, `workmain/ai/report_generator.py`, `workmain/daemon/inspection_engine.py`, `workmain/services/schedule_service.py`, `workmain/templates_engine/field_manager.py`, `workmain/templates_engine/renderer.py`. R4's search shows nothing reads them from outside. | `git grep -lE '\bself\.session\b' -- workmain ':!workmain/database/repositories'` |
| R8 | `tests/test_unit_of_work.py` has `_sessions_opened()`, a context manager that records every session `DatabaseConnection.get_session` returns inside its block. `test_repository_that_fails_to_build_closes_the_scope` already monkeypatches an entry of `UnitOfWork.REPOSITORIES`. | `tests/test_unit_of_work.py` `_sessions_opened`, `TestUnitOfWork::test_repository_that_fails_to_build_closes_the_scope` |
| R9 | `session_scope()` and `record_scope()` each open one session through `get_session()`, and `record_scope()` sets `lock_timeout` to `RECORD_LOCK_TIMEOUT`. | `workmain/database/connection.py` `DatabaseConnection.session_scope`, `DatabaseConnection.record_scope`, `RECORD_LOCK_TIMEOUT` |
| R10 | The only document statement of the attribute is §4.3's example, lines 59–68 of `docs/standards/4-database.md`, inside the fence at 58–69. No other file in `CLAUDE.md`, `docs/standards/`, `docs/ARCHITECTURE.md`, `.claude/` or `docs/dev/` names it, apart from this spec and its design study. | ``git grep -nE 'self\.session\|\.session\b' -- CLAUDE.md docs/standards docs/ARCHITECTURE.md .claude docs/dev`` |
| R11 | `.github/workflows/tests.yml`'s `session-rules` job has two steps, each a `grep` that exits 1 on a match and prints `none found` otherwise. It runs on every push and pull request to `dev` and `main`, and checks out without `fetch-depth`, so `git grep` runs on the checked-out tree. GitHub runs a `run` block with `bash -e`. | `.github/workflows/tests.yml` job `session-rules` |
| R12 | The search AC2.1 states returns nothing at `1f625e5`. On a probe file it matches `repo._session`, `myself._session`, `uow.clients._session` and `getattr(r, "_session")`, and not `self._session`, `x.db_session` or `self._session_factory`. | AC2.1's command; the probe run in the scratchpad, 20261125 |
| R13 | The rename and Step 2's edit, simulated in a scratch worktree, pass `python3 automation/style_check.py --base origin/dev`: 0 violations. | design study F17; re-run with Step 2's edit, 20261125 |
| R14 | Baseline at `287db27`, a bare `pytest`: 1850 passed, 0 failed, 0 skipped (1 xfailed, 3 xpassed). | design study F14 |

## 3. Design rules

- **DR1 — Each repository holds its session as `self._session`.** Each of the 12 classes in R1 assigns `self._session = session` in `__init__`, and every `self.session` in its module becomes `self._session`. Nothing else in a repository module changes. No repository keeps a `session` attribute, property or alias.
- **DR2 — No code outside the repositories reads a repository's session.** The four tests in R4 get the session they need from the scope, not from a repository: from `_sessions_opened()` (R8), or from the argument a repository class was constructed with. A test subclass of a repository that records that argument does so in its constructor, and never reads `self._session`.
- **DR3 — Each test in R4 keeps the property it checks today:**
  - `test_repositories_built_on_its_session_while_entered`: while entered, each name in `UnitOfWork.REPOSITORIES` holds an instance of its class, every one of them was built on the one session the scope opened, and exactly one session was opened.
  - `test_repositories_absent_after_commit_raises`: when the scope's commit raises, the exception propagates and no repository is left set.
  - `TestRecordUnitOfWork::test_record_runs_on_record_scope`: the session a `UnitOfWork(record=True)` runs on has `lock_timeout` equal to `RECORD_LOCK_TIMEOUT`.
  - `TestRecordUnitOfWork::test_default_runs_on_session_scope`: the session a `UnitOfWork()` runs on has the server's default `lock_timeout`, which differs from `RECORD_LOCK_TIMEOUT`.
- **DR4 — One new test shows no repository exposes a session.** In `tests/test_unit_of_work.py` `TestUnitOfWork`, it builds each class in `UnitOfWork.REPOSITORIES` on `db_session` and asserts the instance has no `session` attribute. It does not read `_session`.
- **DR5 — §4.3's example shows `self._session`.** Only its code block changes (Step 2).
- **DR6 — The `session-rules` job runs AC1.1's search and AC2.1's search on every run, one step each.** Each step fails when its search matches, and fails when the search errors (exit above 1), so an error cannot read as `none found`. It prints `none found` otherwise. Their text is Step 3's.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | DR1, DR2, DR3, DR4. One step, because the rename breaks the four tests in R4 (`docs/standards/1-workflow.md` §1.2). The suite is green at its commit. | the 12 repository modules in R1; `tests/test_unit_of_work.py` |
| 2 | DR5: §4.3's example, as quoted below. | `docs/standards/4-database.md` |
| 3 | DR6: the two new `session-rules` steps, as quoted below. It follows Step 1, before which AC1.1's search matches the 202 lines in R2. | `.github/workflows/tests.yml` |
| 4 | The results artifact. Rows AC1.1–AC1.4, AC2.1, AC2.2, AC3.1 and AC4.1 are checked against the delivered code and written `Met` with their evidence. Rows AC1.5 and AC2.3 need the pull request's run, so they are written `Carried`, citing #283, with the run to read and the local evidence AC1.4 and AC2.2 recorded (Decision Log, 20261125). | `docs/dev/results/REPOSITORY_PRIVATE_SESSION_RESULTS.md` |

**Step 2.** In `docs/standards/4-database.md` §4.3, replace:

```python
  class SomethingRepository:
      def __init__(self, session: Session) -> None:
          self.session = session

      def create(self, name: str) -> Something:
          obj = Something(name=name)
          self.session.add(obj)
          self.session.flush()
          self.session.refresh(obj)
          return obj
```

with:

```python
  class SomethingRepository:
      def __init__(self, session: Session) -> None:
          self._session = session

      def create(self, name: str) -> Something:
          obj = Something(name=name)
          self._session.add(obj)
          self._session.flush()
          self._session.refresh(obj)
          return obj
```

The fence and its indentation stay as they are in the file.

**Step 3.** In `.github/workflows/tests.yml`, append to the `session-rules` job's `steps`, after the `No get_session() outside connection.py` step, in this order:

```yaml
      # docs/standards/4-database.md §4.3: data access goes through a
      # repository's methods, and a repository holds its session as
      # `_session`, as §4.3's example does. A public `self.session` hands the
      # session to any code holding the repository. grep exits 1 when nothing
      # matches; above 1 is an error, which fails the step.
      - name: No public session attribute in a repository
        run: |
          status=0
          grep -rnE 'self\.session\b' workmain/database/repositories/ || status=$?
          if [ "$status" -eq 0 ]; then exit 1; fi
          if [ "$status" -ne 1 ]; then echo "grep exit $status"; exit "$status"; fi
          echo "none found"

      # docs/standards/4-database.md §4.3: data access goes through a
      # repository's methods, so nothing outside the repositories reads a
      # repository's session: no `<name>._session` other than `self._session`,
      # and no '_session' string, the form getattr takes. git grep exits 1
      # when nothing matches; above 1 is an error, which fails the step.
      - name: No read of a repository's session outside the repositories
        run: |
          status=0
          git grep -nP "(?<!\bself)\._session\b|['\"]_session['\"]" -- workmain tests automation scripts ':!workmain/database/repositories' ':!scripts/baseline' || status=$?
          if [ "$status" -eq 0 ]; then exit 1; fi
          if [ "$status" -ne 1 ]; then echo "git grep exit $status"; exit "$status"; fi
          echo "none found"
```

### Authorization points

None.

## 5. Acceptance criteria

The change renames an attribute. Every entry path that reaches a repository, whether surface, service, workflow or daemon, reaches it through the same methods, so the full suite (AC4.1) is the evidence that the paths still work. No single path is named.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No repository module refers to a public `session` attribute | `grep -rnE 'self\.session\b' workmain/database/repositories/` returns no hits |
| AC1.2 | No repository built on a session has a `session` attribute | `pytest tests/test_unit_of_work.py` passes, with DR4's test iterating every class in `UnitOfWork.REPOSITORIES` |
| AC1.3 | §4.3's example shows a repository holding its session as `_session` | `grep -nE 'self\.session\b' docs/standards/4-database.md` returns no hits, and `grep -cE 'self\._session\b' docs/standards/4-database.md` prints `4` |
| AC1.4 | The step `No public session attribute in a repository` passes on a clean tree, fails on a match, and fails on a search error | Its `run:` block, run in `bash -e` from the repository root at the branch tip, prints `none found` and exits 0. In a scratch worktree with a `self.session` line added to one repository module, it prints that line and exits 1. Run from a directory with no `workmain/database/repositories/`, it prints `grep exit 2` and exits 2 |
| AC1.5 | Every push and pull request to `dev` or `main` runs AC1.1's search | `/closeout` feature step 3: the `session-rules` job of the run on the pull request that merges this branch to `dev` shows `none found` under `No public session attribute in a repository`. Recorded at feature step 4 |
| AC2.1 | No code outside the repositories reads another object's `_session`, by attribute or by name | ``git grep -nP "(?<!\bself)\._session\b\|['\"]_session['\"]" -- workmain tests automation scripts ':!workmain/database/repositories' ':!scripts/baseline'`` prints nothing and exits 1 |
| AC2.2 | The step `No read of a repository's session outside the repositories` passes on a clean tree, fails on a match, and fails on a search error | Its `run:` block, run in `bash -e` from the repository root at the branch tip, prints `none found` and exits 0. In a scratch worktree with a `repo._session` line appended to an existing tracked module under `workmain/` outside the repositories (`git grep` reads tracked files only), it prints that line and exits 1. Run from a directory outside any git repository, it prints `git grep exit 128` and exits 128 |
| AC2.3 | Every push and pull request to `dev` or `main` runs AC2.1's search | `/closeout` feature step 3: the `session-rules` job of the run on the pull request that merges this branch to `dev` shows `none found` under `No read of a repository's session outside the repositories`. Recorded at feature step 4 |
| AC3.1 | The four tests in R4 check what DR3 states without reading a repository's session | `pytest tests/test_unit_of_work.py::TestUnitOfWork::test_repositories_built_on_its_session_while_entered tests/test_unit_of_work.py::TestUnitOfWork::test_repositories_absent_after_commit_raises tests/test_unit_of_work.py::TestRecordUnitOfWork` passes; AC2.1's search, run over `tests/`, prints nothing; `grep -nE '\.session\b' tests/test_unit_of_work.py` returns no hits; and `grep -nE '\bself\._session\b' tests/test_unit_of_work.py` returns no hits |
| AC4.1 | The full suite passes | A bare `pytest` reports 0 failed |

AC1.1 is the issue's first check, unchanged. AC2.1 restates the issue's second (Decision Log, 20261125). AC3.1 widens the issue's third from `TestRecordUnitOfWork` to all four tests in R4. AC1.4, AC1.5, AC2.2 and AC2.3 keep AC1.1's and AC2.1's searches running after close-out.

**Where each criterion is checked.** Step 4 checks every criterion except AC1.5 and AC2.3 and records it `Met`. AC1.5 and AC2.3 need the pull request's run, which first exists at `/closeout` feature step 3 (`.claude/skills/closeout/references/feature.md`). Close-out preflight P6 runs before that push and accepts only `Met` or `Carried` rows (`.claude/skills/closeout/SKILL.md` P6). So Step 4 writes them `Carried`, citing #283, with the run to read. Feature step 4, which records "the criteria step 3's run checked", sets each to `Met` with the run's evidence.

## 6. Test plan

- **Baseline before this work:** 1850 passed, 0 failed, 0 skipped (1 xfailed, 3 xpassed), from a bare `pytest` at `287db27` (R14). The results artifact re-measures at the branch tip before Step 1.
- **Expected after:** 1850 + *n* passed, 0 failed, 0 skipped, where *n* is the number of test items DR4's test collects (1 unparametrized, 12 if parametrized over `UnitOfWork.REPOSITORIES`). xfailed and xpassed unchanged.
- **Test files:** `tests/test_unit_of_work.py`: the four tests in R4 rewritten to DR3, and DR4's test added to `TestUnitOfWork`. No other test file changes.

## 7. Risks and rollback

- **A repository written from the old pattern.** A later branch can add a repository, such as #161's `ProjectsRepository`, that keeps a public `self.session`, or a method on an existing one that uses `self.session`. The method raises `AttributeError` on an existing repository, and the suite catches it wherever the method is tested. A new repository's `self.session` raises nothing, and DR4's test misses it unless the class is in `UnitOfWork.REPOSITORIES`. The `No public session attribute in a repository` step (DR6) finds either one on the branch's pull request. No other branch touches these files today (design study F11).
- **The new CI steps are report-only**, like the rest of `tests.yml`, so a match shows on the run but does not block a merge.
- **`git grep -P` needs git built with PCRE.** Ubuntu's git is. If a runner's git is not, `git grep` errors, and DR6 makes the step fail rather than pass.
- **Existing defect, outside scope:** the two existing `session-rules` steps treat a `grep` error (exit 2) as `none found`, because `if grep ...; then exit 1; fi` reads any non-zero exit as no match.
- **Rollback:** each step is one commit. Reverting Step 1 restores `self.session` and the four tests together. Steps 2 and 3 revert on their own.

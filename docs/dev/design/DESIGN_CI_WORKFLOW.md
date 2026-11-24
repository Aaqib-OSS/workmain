# A GitHub Actions run of the suite, the style check and the commit-message check — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner
**Date:** 20261123
**Read at:** 010803befceeaee19c8cdb661f12023c0a50b402
**Originating item:** Issue #297

---

## 1. Purpose

Nothing outside the working session runs the application suite, `automation/style_check.py` or `.githooks/commit-msg`, so a push to `dev` or a `dev → main` pull request carries no independent result. This study checks the issue's claims against current source and GitHub's live settings. It then sets out the design of a GitHub Actions workflow that runs all three, and the questions Ray must answer before the spec can be written. The issue's "Fix in mind" bullets are each treated as a question here (`docs/standards/1-workflow.md` §1.3).

## 2. Scope of the read

- **Files read:** `automation/style_check.py`; `.githooks/commit-msg` and `.githooks/pre-push`; `tests/conftest.py`; `workmain/database/connection.py` (configuration block); `pyproject.toml`; `requirements.txt` and `requirements-dev.txt`; `.env.example`; `.gitignore`; `workmain/database/migrations/versions/0001_baseline.sql` (extensions); and `docs/standards/2-git.md`, `docs/standards/4-database.md` §4.1, `docs/standards/6-testing.md` §6 and `docs/standards/7-file-placement.md` §7.
- **GitHub, read live:** the repository's `security_and_analysis` settings, CodeQL default setup, the two rulesets, Actions permissions, and the list of Actions secrets.
- **Test database, read only:** the role, owner, server version, extensions and time zone of `workmain_test`.
- **History:** `.githooks/commit-msg`, run over the last 300 commits on `origin/main`.
- **Search by file (§1.3).** `gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --search "\"<path>\" in:body"` was run once for each of these paths. Every non-noise result is listed:
  - `automation/style_check.py`: #264, #277, #240
  - `automation/style_check_test.py`: #277
  - `.githooks/commit-msg`: #298, #89
  - `docs/standards/2-git.md`: #299, #298, #291, #247, #89
  - `tests/conftest.py`: #287, #278
  - `docs/standards/6-testing.md` and `docs/standards/1-workflow.md`: these return most open issues, because nearly every issue cites them. None of the results is about CI, test execution environment or commit checks, apart from those already listed.
  - `.github/`: matches every body that contains "github". Of the results, only #247 and #298 concern this work.
  - **No `parked` issue** was returned for any of these files.
- **Search by term:** "GitHub Actions", "workflow file", "CI", "secret scanning", "push protection", "required check". Beyond #297 itself, these returned only #298 and #111, which is unrelated.
- **Left out:** the bodies of the tests that will fail on a clean runner. They are owned by #292, #198, #207 and #214, and this issue makes the suite run, not pass. `automation/*_test.py` is also left out, because the issue's criteria name the application suite only.

## 3. Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F1 | No workflow exists. `.github/` holds only `ISSUE_TEMPLATE/`. CodeQL runs through GitHub's default setup, not a workflow file: `state: configured`, Python, weekly, standard runner. | `ls .github/`; `gh api repos/lockdwn20/workmain/code-scanning/default-setup` |
| F2 | Actions is enabled, allows all actions, and does not require pinning to a SHA. The repository holds no Actions secrets. | `gh api repos/lockdwn20/workmain/actions/permissions`; `gh api .../actions/secrets` returned none |
| F3 | **Secret scanning push protection is already enabled**, along with secret scanning. The issue's bullet "Enable GitHub secret scanning push protection" is therefore already done, and nothing remains for this issue. | `gh api repos/lockdwn20/workmain --jq .security_and_analysis`: `secret_scanning_push_protection.status: enabled` |
| F4 | Two rulesets exist. `main-pr-required` applies a `pull_request` rule to `refs/heads/main`. `protection` applies `deletion` and `non_fast_forward` rules to every ref. Both carry an admin-role bypass set to `always`. Neither requires a status check. Making the new check required therefore means editing a ruleset on GitHub, outside the working tree. | `gh api repos/lockdwn20/workmain/rulesets/<id>` for 25770102 and 25759747 |
| F5 | **`automation/style_check.py` cannot run on a runner as written.** On a runner it hits three problems: <br>(a) It reads real values only from `.env` in the main working tree (`real_values(_main_worktree() / ".env")` in `main`), and with no values listed it fails (`failed = ... or not values`). <br>(b) It names its base from the checked-out branch (`base_branch`). A pull request checkout is a detached HEAD, so the branch name is `HEAD` and the base is `main`. A runner has only `origin/main`, so `git merge-base HEAD main` fails. `--base origin/main` avoids this. <br>(c) It needs the history back to the merge base, which a shallow checkout (the `actions/checkout` default of depth 1) does not have. | `automation/style_check.py` `main`, `base_branch`, `changed_lines`, `commit_violations` |
| F6 | `.env` is gitignored, so a `.env` written into a runner's checkout does not count as an untracked changed file. `workmain.egg-info/` and `.pytest_cache/` are also gitignored. Any other file a workflow step writes inside the checkout would count as changed, and `changed_lines` would check it. | `git check-ignore -v`: `.gitignore:37`, `:19`, `:76`; `changed_lines` reads `git ls-files --others --exclude-standard` |
| F7 | A `.env` in the checkout is also read by the suite. `workmain/database/connection.py` calls `load_dotenv()` at import, and `tests/test_database_isolation.py` reads `.env` (#292). Any `.env` that a style-check step writes must therefore not exist while `pytest` runs. | `workmain/database/connection.py` module level; #292 body |
| F8 | **The production database role is not a superuser, as the issue says.** `workmain_user` has `rolsuper`, `rolcreatedb` and `rolcreaterole` all false. It owns `workmain_test`, and it owns the two extensions the baseline creates, `pg_trgm` and `uuid-ossp`. Both are trusted extensions on PostgreSQL 16, so a database owner that is not a superuser can create them. The server is PostgreSQL 16.15. The `postgres` container image makes its `POSTGRES_USER` a superuser, so a runner that tests as that user tests with more privilege than production has. | Read-only query on `workmain_test`, 20261123; `0001_baseline.sql` lines 14, 28 |
| F9 | `tests/conftest.py` states how the test database is set up: "workmain_test is created once by the database server's administrator, owned by the application's user". Each run then drops everything that user owns and rebuilds the schema with `alembic upgrade head`. The connection is set from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` and `DB_PASSWORD`, and `DB_NAME` is forced to `workmain_test`. | `tests/conftest.py` `_test_database`, `build_test_database`, `pytest_configure`; `workmain/database/connection.py` configuration block |
| F10 | **The application's time zone is `America/Los_Angeles` in two places.** `workmain/daemon/scheduler.py` (`BlockingScheduler(timezone='America/Los_Angeles')`) and `workmain/utils/ics_parser.py` (`LOCAL_TZ`) set it, and the live database session's `timezone` is `America/Los_Angeles`. A runner defaults to UTC for both the process and the `postgres` container. Matching the application therefore needs both the process `TZ` and the database session's time zone set, for example with `PGTZ`. The time-zone dependence itself is #292's, and its fourth criterion. | `workmain/daemon/scheduler.py:176`; `workmain/utils/ics_parser.py:75`; `show timezone` on `workmain_test` |
| F11 | `.githooks/commit-msg` takes a message file path, checks its subject, and exempts merge, revert, fixup, squash and amend subjects. Run over the last 300 commits on `origin/main`, it rejected none, so a check over existing history starts green. It finds the git directory through `git rev-parse --git-dir`, which works in a runner's checkout. | `.githooks/commit-msg`; loop over `git rev-list origin/main -n 300`, 20261123 |
| F12 | Two places state the commit type list, and they must stay in step: `docs/standards/2-git.md` §2.4 (`Types: feat, fix, refactor, chore, docs, test`) and the `grep -qE` pattern and help text in `.githooks/commit-msg`. No skill or `automation/` script parses commit types. §2.2 already lists "editor/CI config" and `.github/` under `chore/*`, so `chore(ci): ...` is a valid subject today. No commit in history uses it. | `docs/standards/2-git.md` §2.2, §2.4; `.githooks/commit-msg`; `grep` over `.claude` and `automation` |
| F13 | **A `hotfix/*` or `chore/*` merge reaches `main` by a direct push with no pull request** (§2.2, through the admin bypass). The issue's criteria cover a push to `dev` and a pull request to `main` only. A hotfix's code is therefore first tested by the run on the `dev` push that follows it. By then its lines are on `origin/main`, so a `dev` run with base `origin/main` does not style-check them. | `docs/standards/2-git.md` §2.2 `main`; F5 |
| F14 | **The last "Fix in mind" bullet asks for two checks the criteria never mention:** no `.commit()` or `.rollback()` under `workmain/database/repositories/`, and no `get_session(` outside `workmain/database/connection.py`. Both rules come from `docs/standards/4-database.md` §4.1 and §4.3. <br>No repository holds `.commit()` or `.rollback()` today. <br>A text search for `get_session(` finds six test files, which call `DatabaseConnection.get_session()` from `tests/` (§6.1 governs tests). It also finds `ConversationState.get_session` in `workmain/daemon/conversation_state.py:242` and its caller in `workmain/integrations/slack/slack_eod.py:119`, which is a different method. So a bare `grep` fails today on code that breaks no rule. A correct check has to resolve the call target, scoped to `workmain/`. | `grep -rnE '\.(commit\|rollback)\(\)' workmain/database/repositories`; `grep -rn 'get_session(' workmain tests automation scripts` |
| F15 | **A run that finds a real value comes after the value is already published.** A push to a public repository publishes the value when the push lands, before any run starts. A real-value check in a run can therefore only report the publication. Prevention stays with the local `automation/style_check.py` run that Anvil's step check and `/closeout` P7 already make. | `CLAUDE.md` § Client Reference; `.claude/skills/session-start/references/anvil.md`; `.claude/skills/closeout/SKILL.md` P7 |
| F16 | GitHub masks a secret's whole value in logs, not each part of it. If `DEV_REAL_VALUES` were stored as one comma-separated secret, a single entry printed on its own would not be masked unless the workflow masks each entry (`::add-mask::`). `automation/style_check.py` prints positions, never values (`real_value_violations`, `main`). | `automation/style_check.py`; GitHub Actions log masking (unverified against GitHub's current documentation) |
| F17 | Related open issues. <br>#298 says its commit-message check on the `dev → main` pull request belongs to #297. That check is this issue's fifth criterion. <br>#89 adds an `Issue: #N` trailer check to `.githooks/commit-msg`, which a run that calls the hook picks up with no change. <br>#277 (rename blind spot) applies to the run as well. It is #277's to fix. <br>#247 (sessions act as admin) means a required check could still be bypassed by a session. | Issue bodies, read 20261123 |

## 4. Governing rules and options

**Governing rules.**

- **Owner.** `docs/ARCHITECTURE.md` §2 maps application code and the files the application reads. A workflow file is development tooling, not something the application reads, so its placement is `docs/standards/7-file-placement.md` §7 and its branch type is `docs/standards/2-git.md` §2.2. §7 has no row for `.github/` because GitHub fixes that path. A spec that adds `.github/workflows/<file>.yml` should state that §7 gains no row for it, or else add one, as Ray chooses (Q8).
- **The suite** is a bare `pytest` from the repository root, and its evidence takes the three-count form (`docs/standards/6-testing.md` §6).
- **The test database** is set up as F9 describes: created by the server's administrator and owned by the application's user.
- **Real values** stay out of everything the repository publishes (`CLAUDE.md` § Client Reference), and only development tooling reads `DEV_REAL_VALUES`.
- **A new rule or commit type needs Ray's approval** (`docs/standards/1-workflow.md` §1.5).
- **A ruleset edit happens on GitHub**, outside the working tree, and belongs to Ray (F4).

**Settled by rule, which Ray can reverse:**

- **The runner's database role matches production.** The issue asks this as a question, and F8 and F9 decide it. The `postgres` service container (16) runs as its superuser only to create a `workmain_user` role with no superuser, createdb or createrole privilege, and a `workmain_test` database owned by that role. The suite then connects as `workmain_user`. Testing as the container's superuser would pass a migration that production refuses.
- **Push protection needs no work** (F3).

### Option A — one workflow, the real values written to `.env` for the style step

- **Approach:** add `.github/workflows/<name>.yml`, triggered on a push to `dev` and on a pull request to `main`. It checks out with full history and sets `TZ` and `PGTZ` to `America/Los_Angeles`. It prints `date`, builds the database as settled above, and installs `requirements.txt` and `requirements-dev.txt` and the package. It then runs three checks, each reporting its own exit status:
  - **Commit messages:** `.githooks/commit-msg`, once per commit in the range, each message written to a file under `$RUNNER_TEMP` (F6). The range is the push's before..after, or the pull request's base..head.
  - **Style:** a step writes `DEV_REAL_VALUES` from a repository secret into `.env`, runs `automation/style_check.py --base origin/main`, and deletes `.env`.
  - **Suite:** a bare `pytest`.
- **Pros:** `automation/style_check.py` does not change.
- **Cons:**
  - A file holding the real values sits in the checkout for the length of one step, and the suite's correctness depends on that step deleting it before `pytest` runs (F7).
  - A failure between writing and deleting `.env` leaves it behind for any later step that runs regardless of failure.

### Option B — one workflow, `automation/style_check.py` also reads `DEV_REAL_VALUES` from the environment

- **Approach:** the same workflow as A, except that the secret goes into the style step's `env:` only. `automation/style_check.py` reads `DEV_REAL_VALUES` from the process environment when it is set, and from `.env` otherwise. Its docstring and `automation/style_check_test.py` change to match. The step masks each entry before the check runs (F16).
- **Pros:**
  - The values never exist as a file on the runner and never reach the `pytest` process.
  - The check still fails closed when the secret is missing.
- **Cons:** it changes `automation/style_check.py` and its tests, which #277 also changes. The two must not land in conflicting order.

### Option C — no real values on the runner

- **Approach:** the same workflow, with a flag added to `automation/style_check.py` that skips the real-value check and states it was skipped. The run checks ruff, history citations and Markdown wrapping only.
- **Pros:** the real values are never copied to GitHub.
- **Cons:**
  - The run cannot report a published real value. F15 shows it could only report it after the fact anyway.
  - It adds a way to switch the check off, which a local run could also use.

**Recommendation: B, if Ray answers Q3 yes; C, if he answers no.**

- **Against A:** A's correctness rests on a cleanup step. B gets the same result by scoping the secret to one step, which the runner enforces.
- **What B buys:** the real-value check in a run only reports, never prevents (F15). B keeps that report. The local check still does the preventing.
- **When C is right:** the reason for C is entirely whether a copy of the values on GitHub fits `CLAUDE.md` § Client Reference. That is Q3, and it is Ray's.

**Common to every option:**

- **Each check runs and reports on its own,** so a failing suite does not hide a style or commit-message result. That means separate jobs, or steps that run after a failure.
- **The workflow sets `permissions: contents: read`.**

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | **Should the check start as report-only, with making it required on `main` left for later?** The problem is real: #292, #198, #207 and #214 own tests that will fail on a clean runner, so a required check would block every `dev → main` pull request until they ship. Making it required is a ruleset edit on GitHub (F4). #247 means an admin session could bypass it even then. **Recommended:** report-only. A later, separate change makes it required, once the suite is green on the runner. That change is outside this issue. | |
| Q2 | **How should the runner get `DEV_REAL_VALUES`?** Option A writes `.env` from a secret. Option B scopes the secret to the step's environment and has `automation/style_check.py` read it there. Option C skips the real-value check in the run. **Recommended:** B, subject to Q3. | |
| Q3 | **Does a GitHub Actions secret holding the real values fit `CLAUDE.md` § Client Reference?** The rule forbids real values in what the repository *publishes*: a tracked file, a commit message, issue or pull request text. A secret is none of those. It is encrypted and masked in logs. But it puts a copy of the values on GitHub, where today they exist only in `.env` and the database. The check it enables only reports a value already published (F15). If yes, Option B. If no, Option C. | |
| Q4 | **Should a commit type `ci` be added?** It would change `docs/standards/2-git.md` §2.4 and the pattern and help text in `.githooks/commit-msg` (F12). The issue's "Fix in mind" adds it. §2.2 already files CI config under `chore`, so `chore(ci): ...` works today with no change to the rule. **Recommended:** no. Use `chore(ci)`, which adds no rule. If Ray wants the type, both places change in one step. | |
| Q5 | **When a run fails, who fixes it?** The issue's answer: the branch that caused the failure fixes it, unless an open issue already owns the failing test, and a failing run never becomes a new issue by itself. That would be a new rule. It needs Ray's approval and a home. **Recommended:** a short rule in `docs/standards/6-testing.md` §6, beside the statement of what the suite is, citing `docs/standards/1-workflow.md` §1.3 for the search that finds the owning issue. | |
| Q6 | **Are the session checks in this issue or their own?** These are the two checks from the last "Fix in mind" bullet: no `.commit()` or `.rollback()` in repositories, and no `get_session(` outside `connection.py`. No criterion names them. A bare `grep` fails today on `ConversationState.get_session`, which breaks no rule (F14). A correct check resolves call targets, which is a design of its own. **Recommended:** carry them to their own issue, since the work does not need them. | |
| Q7 | **Should the workflow also run on a push to `main`?** That push is the route a `hotfix/*` or `chore/*` merge takes, with no pull request (F13). The problem is real: a hotfix reaches `main`, and its lines are never style-checked by a run. It is not in the issue's criteria. Adding it is one trigger, plus a base for the style check on that event. **Recommended:** yes. The issue's Problem is a change reaching `main` unseen, and this is the one route to `main` that its criteria leave open. | |
| Q8 | **How are actions pinned, and does §7 gain a row?** No rule covers action pinning (F2: pinning is not required). Pinning to a full commit SHA closes the case where a moved tag runs new code with this repository's token. §7 has no row for `.github/workflows/`. **Recommended:** pin every action to a full SHA with its version in a comment, and give §7 no row, because GitHub fixes the path. | |

## 6. Disposition

- Promoted to:
- Superseded by:

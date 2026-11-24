# A GitHub Actions run of the suite, the style check and the commit-message check — Spec

**Status:** Shipped
**Author:** Spanner
**Date:** 20261124
**Read at:** 59f73429b3c5ccfdc5b2d313cd2104090b8c8126
**Branch:** `chore/issue-297-ci-workflow` (base: `main`, `docs/standards/2-git.md` §2.1)
**Target release:** none. A `chore/*` merge is not a release (`docs/standards/2-git.md` §2.2).
**Originating item:** Issue #297
**Design study:** `../design/DESIGN_CI_WORKFLOW.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261124 | Ray | Design study Q1–Q11 answered. The answers are in the study's §5. | Accepted. |
| 20261124 | Ray | Markers are not strict: `@pytest.mark.xfail(reason="#<owning issue>")` (Q11). A marked test that passes reports as xpassed. | Accepted. Step 2. |
| 20261124 | Ray | Spec approved, with Step 2's worktree created by `git worktree add --detach "$(mktemp -d)" HEAD`. | Accepted. |
| 20261124 | Ray | Deviation approved: `tests/test_slack_channel_config.py::TestSlackSetWorkspace::test_slack_set_workspace_shows_config` asserted on a value listed in `DEV_REAL_VALUES`. Its assertion now uses an invented value (`CLAUDE.md` § Client Reference). History stays as it is, as with #276. AC1.5's check allows the one line. | Accepted. Ray approved the amendment to AC1.5 with the deviation, so **Status** stays `Approved`. |
| 20261124 | Ray | No Caliper review. | Review is `n/a` (`docs/standards/1-workflow.md` §1.1). |
| 20261124 | Spanner | The draft workflow in the issue's comment is the basis for Step 3, with four changes. <br>(a) A range or base that cannot be read fails the run and says why (design study F19). <br>(b) The `python-dotenv` pin is read from `requirements.txt` (F20). <br>(c) The style step prints its exit status (F21). <br>(d) The comments do not cite the study (`docs/standards/3-code.md` §3, opening). | Accepted by Ray, 20261124. |

---

## 1. Scope

**In scope:**

- `.github/workflows/tests.yml`, new.
- `automation/style_check.py` and `automation/style_check_test.py`: `DEV_REAL_VALUES` read from the environment.
- The test files under `tests/` that hold a test failing in Step 2's run. Each gains an `xfail` marker and nothing else.
- The results artifact.

**Ray, outside the working tree:** creating the repository secret `DEV_REAL_VALUES` before this branch's merge is pushed to `main`.

**Out of scope:**

- Making the check required.
- Fixing any baseline failure. #292, #198, #207 and #214 own those failures.
- A `ci` commit type.
- Any change to `docs/standards/6-testing.md`, its templates, or §7.
- Push protection, which is already on.
- A session check that resolves call targets.
- #277, #89 and #298.
- Running `automation/*_test.py` in the workflow.

## 2. Verified current state

Direct path: each step quotes the text it replaces. Claims about the runner, GitHub and the draft workflow are the design study's findings F1–F26.

`real_values` call sites, from `grep -rn 'real_values' --include='*.py' .` outside `.venv/`. No `getattr` reference or uncalled reference exists:

- `automation/style_check.py:393` (`main`)
- `automation/style_check_test.py:270` and `:274`

## 3. Design rules

- **DR1 — The real values never exist as a file on the runner, and no log prints one.** The secret reaches the style step's `env:` only. Each entry is masked from an environment variable before the check runs (design study F16).
- **DR2 — Each check is a job of its own.**
- **DR3 — A range or base that cannot be read fails the run and names the reason.**
- **DR4 — The suite connects as a role that is not a superuser, cannot create databases or roles, and owns `workmain_test`.**
- **DR5 — A marker is the only change to a test.**

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `automation/style_check.py` reads `DEV_REAL_VALUES` from the environment | `automation/style_check.py`, `automation/style_check_test.py` |
| 2 | Baseline failures marked `xfail` | the test files Step 2's run names |
| 3 | The workflow | `.github/workflows/tests.yml` |
| 4 | Results artifact | `docs/dev/results/CI_WORKFLOW_RESULTS.md` |

### Step 1 — `DEV_REAL_VALUES` from the environment

**Contract:** `real_values(env: Path, environ: Mapping[str, str] | None = None) -> list[str]`. `environ` defaults to `os.environ`. The function returns the entries of `environ["DEV_REAL_VALUES"]`, split as now, when that yields at least one entry, and otherwise the entries from `env`. A missing secret expands to `""` and falls through to a `.env` that does not exist, so the check still fails closed. The call in `main` is unchanged.

**Replace** in the module docstring:

```text
DEV_REAL_VALUES, read from .env in the main working tree, so a linked
worktree reads the same file. The report names where a value is,
```

**with:**

```text
DEV_REAL_VALUES, read from the environment when it lists any, and
otherwise from .env in the main working tree, so a linked worktree
reads the same file. The report names where a value is,
```

**Replace** the function `real_values`, from `def real_values(env: Path) -> list[str]:` through its `return`, with the contract above. Its docstring documents `environ`.

**Replace** in `main`:

```python
            f"  real-value check not run: {REAL_VALUES_KEY} is not set in .env in the main working tree"
```

**with:**

```python
            f"  real-value check not run: {REAL_VALUES_KEY} is not set in the environment or in .env in the main working tree"
```

**Tests** in `automation/style_check_test.py`:

- An environment value is used over the file.
- An empty or comma-only environment value falls through to the file.
- `main`, with `DEV_REAL_VALUES` set by `monkeypatch.setenv` and no `.env`, reports a value on a changed line without printing it.
- The `repo` fixture calls `monkeypatch.delenv("DEV_REAL_VALUES", raising=False)`.

### Step 2 — Mark the baseline failures

Run the suite once locally, without `.env` or `~/.workmain/`, with its output piped. Create the worktree with `git worktree add --detach "$(mktemp -d)" HEAD`, as Caliper does, so no directory above it holds a `.env`. `HOME` set to an empty directory, and `DB_*` exported with `DB_NAME=workmain_test`, as `python -m pytest`, so the worktree's `workmain` is imported. Mark each test that fails with `@pytest.mark.xfail(reason="#<owning issue>")`, adding `import pytest` where it is missing. A failure no open issue owns is reported to Ray in one line.

**Proof that the change is behaviour-neutral** (`docs/standards/2-git.md` §2.2): `git diff main -- tests/` adds only those decorator lines and `import pytest` lines, and removes nothing.

### Step 3 — The workflow

**Create** `.github/workflows/tests.yml`:

```yaml
# Runs the application suite, the style check on changed lines, the
# commit-message check and the session-rule searches. Report-only: no
# check here blocks a merge. Making one required is a ruleset change on
# GitHub.
#
# Actions are pinned to a full commit SHA, with the release in a comment.

name: tests

on:
  push:
    branches: [dev, main]   # main: hotfix/* and chore/* merges arrive by push, with no pull request
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  suite:
    name: Application suite
    runs-on: ubuntu-latest
    timeout-minutes: 30

    # A throwaway PostgreSQL 16, created for this run and deleted after it.
    # The image makes POSTGRES_USER a superuser, so that account only creates
    # the application's role and database; the suite never connects as it.
    # Both passwords exist only inside this run.
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: ci_admin_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10

    # What workmain/database/connection.py reads. tests/conftest.py builds the
    # schema itself with `alembic upgrade head`. No .env file exists here.
    # TZ sets the process's time zone, PGTZ the database session's.
    env:
      DB_HOST: localhost
      DB_PORT: "5432"
      DB_NAME: workmain_test
      DB_USER: workmain_user
      DB_PASSWORD: ci_only_password
      TZ: America/Los_Angeles
      PGTZ: America/Los_Angeles

    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
        with:
          python-version: "3.12"
          cache: pip

      # As production: a role that is not a superuser and cannot create
      # databases or roles, owning workmain_test. pg_trgm and uuid-ossp are
      # trusted extensions, so that owner can create them.
      - name: Create the application's role and test database
        run: |
          docker exec "${{ job.services.postgres.id }}" psql -v ON_ERROR_STOP=1 -U postgres \
            -c "CREATE ROLE workmain_user LOGIN PASSWORD 'ci_only_password' NOSUPERUSER NOCREATEDB NOCREATEROLE" \
            -c "CREATE DATABASE workmain_test OWNER workmain_user" \
            -c "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname = 'workmain_user'"

      - name: Install requirements and the package
        run: |
          pip install -r requirements.txt -r requirements-dev.txt
          pip install --no-deps -e .

      - name: Show the run's time zone
        run: date

      - name: Run the application suite
        run: pytest

  style:
    name: Style check on changed lines
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      # Full history, so style_check.py can find where the change left its base.
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0

      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
        with:
          python-version: "3.12"
          cache: pip

      # ruff from requirements-dev.txt; python-dotenv at the version requirements.txt pins.
      - name: Install ruff and python-dotenv
        run: pip install -r requirements-dev.txt "$(grep -oE '^python-dotenv==[^ #]+' requirements.txt)"

      # The secret reaches this step's environment only, and style_check.py
      # reads DEV_REAL_VALUES from the environment. No file holds the values.
      #
      # GitHub masks the secret's whole value, not each entry in it, so each
      # entry is masked before anything runs. The script reads the entries
      # from the environment, so the log never shows them.
      #
      # A pull request from a fork gets no secrets, so its run fails closed here.
      #
      # Base: origin/main on a push to dev or a pull request to main; on a push
      # to main, the commit main pointed at before the push.
      - name: Check the changed lines
        env:
          DEV_REAL_VALUES: ${{ secrets.DEV_REAL_VALUES }}
          BASE: ${{ (github.event_name == 'push' && github.ref_name == 'main') && github.event.before || 'origin/main' }}
        run: |
          IFS=',' read -ra entries <<< "$DEV_REAL_VALUES"
          for entry in "${entries[@]}"; do
            entry="${entry#"${entry%%[![:space:]]*}"}"
            entry="${entry%"${entry##*[![:space:]]}"}"
            if [ -n "$entry" ]; then echo "::add-mask::$entry"; fi
          done
          if ! git cat-file -e "$BASE^{commit}" 2>/dev/null; then
            echo "Base $BASE is not in this clone, so the changed lines cannot be found. A forced push to main replaces the commit main pointed at."
            exit 1
          fi
          status=0
          python3 automation/style_check.py --base "$BASE" || status=$?
          echo "automation/style_check.py exit $status"
          exit "$status"

  commit-messages:
    name: Commit messages
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0

      # Every commit the push or pull request adds, each through
      # .githooks/commit-msg, which exempts merge, revert and fixup subjects
      # itself. A branch's first push has an all-zero "before", so its range
      # starts at origin/main. A range that cannot be read fails the job.
      # Message files go under $RUNNER_TEMP, outside the checkout.
      - name: Check each commit message in the range
        env:
          EVENT: ${{ github.event_name }}
          BEFORE: ${{ github.event.before }}
          AFTER: ${{ github.sha }}
          PR_BASE: ${{ github.event.pull_request.base.sha }}
          PR_HEAD: ${{ github.event.pull_request.head.sha }}
        run: |
          if [ "$EVENT" = "pull_request" ]; then
            range="$PR_BASE..$PR_HEAD"
          elif [ "$BEFORE" = "0000000000000000000000000000000000000000" ]; then
            range="origin/main..$AFTER"
          else
            range="$BEFORE..$AFTER"
          fi
          echo "Range: $range"
          if ! commits="$(git rev-list --reverse "$range")"; then
            echo "Range $range cannot be read from this clone. A forced push replaces the commit the branch pointed at before it."
            exit 1
          fi
          failed=0
          for commit in $commits; do
            git log -1 --format=%B "$commit" > "$RUNNER_TEMP/commit-msg.txt"
            if bash .githooks/commit-msg "$RUNNER_TEMP/commit-msg.txt"; then status=0; else status=$?; failed=1; fi
            echo "$(git log -1 --format='%h %s' "$commit") -> exit $status"
          done
          exit "$failed"

  session-rules:
    name: Session rules
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      # docs/standards/4-database.md §4.1 and §4.3: committing and rolling back
      # are the scope owner's, never a repository's.
      - name: No commit or rollback in a repository
        run: |
          if grep -rnE '\.(commit|rollback)\(\)' workmain/database/repositories/; then exit 1; fi
          echo "none found"

      # docs/standards/4-database.md §4.1: sessions open through session_scope().
      # `get_session()` with no argument, so ConversationState.get_session(user_id)
      # does not match.
      - name: No get_session() outside connection.py
        run: |
          if grep -rn 'get_session()' workmain/ --include='*.py' | grep -v connection.py; then exit 1; fi
          echo "none found"
```

Before the commit, run each job's `run:` block locally in `bash -e` with its `env:` set by hand, including a `BASE` and a `BEFORE` that are not in the clone.

### Step 4 — Results artifact

`docs/dev/results/CI_WORKFLOW_RESULTS.md`, from its template. Criteria checked on GitHub are recorded `Not met`, `Awaiting Ray`, because the workflow first runs at close-out.

### Authorization points

None. Close-out's pushes to `main` and `dev` each trigger a run.

## 5. Acceptance criteria

Issue edits at close-out:

- Criterion 1's check is restated as AC1.1 below.
- Criterion 1 is extended to a push to `main` (AC1.2).
- Criterion 6 is added (AC6.1).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A push to `dev` runs the application suite on a GitHub-hosted runner against a fresh `workmain_test`, and its result shows on the commit | The run on the push that merges this branch to `dev` shows a bare `pytest` and its summary line in its log. The results artifact writes the counts in `docs/standards/6-testing.md` §6's form, with xfailed and xpassed as a note. |
| AC1.2 | A push to `main` runs the same suite, and its result shows on the commit | The run on the push that merges this branch to `main` shows a bare `pytest` and its summary line in its log |
| AC1.3 | The suite connects as a role that is not a superuser | That run's role step shows `rolsuper`, `rolcreatedb` and `rolcreaterole` all `f` for `workmain_user` |
| AC1.4 | The known failures are marked, so the run starts green | That run's summary shows 0 failed |
| AC1.5 | A marker is the only change to any test, apart from the approved replacement of a real value | `git diff main -- tests/` adds only `@pytest.mark.xfail(reason="#<N>")` lines and `import pytest` lines, plus the one assertion line in `test_slack_set_workspace_shows_config` that replaces a real value with an invented one |
| AC2.1 | A pull request to `main` runs the same suite and shows its result on the pull request | `gh pr checks <N>` on the next `dev → main` pull request lists this workflow's jobs beside CodeQL's |
| AC3.1 | The run checks the changed lines with `automation/style_check.py` and shows its exit status | The style job's log holds `automation/style_check.py exit <n>` |
| AC3.2 | The workflow holds no real value | Ray reads `.github/workflows/tests.yml` for any real value |
| AC3.3 | `automation/style_check.py` reads the real values from the environment when it lists any, and from `.env` otherwise | `pytest automation/style_check_test.py` passes, including Step 1's tests |
| AC4.1 | The run uses the application's time zone | The run's time-zone step prints a date in `PST` or `PDT` |
| AC5.1 | Every commit a push or pull request adds is checked with `.githooks/commit-msg` | The commit-message job prints one `-> exit <n>` line per commit in the range |
| AC5.2 | A range that cannot be read fails the run and says why | The commit-message `run:` block, run locally with `BEFORE` set to a SHA absent from the clone, exits 1 and prints the reason |
| AC6.1 | A push or pull request checks that no repository commits or rolls back, and that no `get_session()` call exists outside `workmain/database/connection.py` | The session-rules job shows `none found` under both steps |

## 6. Test plan

- **Baseline:** 1800 passed, 0 failed, 0 skipped, from a bare `pytest` at `94d5c63`, whose code is the same as at **Read at:**. `pytest automation/`: 134 passed, 0 failed, 0 skipped.
- **Expected after, locally:** 0 failed. Passed plus xpassed is 1800. `pytest automation/`: 137 passed, 0 failed, 0 skipped.
- **On the runner:** 0 failed, with xfailed and xpassed as a note.

## 7. Risks and rollback

- **The runner may fail a test the local run passed.** That run is then red, and it is marked the same way on a new branch.
- **One style violation keeps `dev` red until the next release.** A run on `dev` checks everything `dev` holds beyond `main`, because its base is `origin/main`.
- **A pull request from a fork fails closed.** It gets no secrets, and Ray is the only contributor.
- **A forced push fails the run, which says why** (DR3).
- **A marked test that an owning issue fixes reports as xpassed and stays green.** The owning issue removes its marker.
- **Rollback:** revert each step's commit. Step 3's revert deletes the workflow.

# A GitHub Actions run of the suite, the style check and the commit-message check — Spec

**Status:** Draft
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
| 20261124 | Ray | Report-only. Known baseline failures are marked `xfail(strict=True)` with the owning issue, and the markers are in scope. Making the check required is a separate change. Design study Q1. | Accepted. Steps 2 and 3. |
| 20261124 | Ray | `automation/style_check.py` reads `DEV_REAL_VALUES` from the environment, and the secret reaches the style step only. Design study Q2 (Option B). | Accepted. Step 1. |
| 20261124 | Ray | A GitHub Actions secret fits `CLAUDE.md` § Client Reference, because a secret is not published. Design study Q3. | Accepted. |
| 20261124 | Ray | No `ci` commit type. CI files use `chore(ci): …`. Design study Q4. | Accepted. §1 Out of scope. |
| 20261124 | Ray | No new rule for who fixes a failed run. Design study Q5. | Accepted. §1 Out of scope. |
| 20261124 | Ray | Both session-rule searches stay in this issue (design study Q6, F14). | Accepted. Step 3, AC6.1. The issue gains AC6 at close-out (§5). |
| 20261124 | Ray | The workflow also runs on a push to `main`. Design study Q7. | Accepted. Step 3, AC1.2. |
| 20261124 | Ray | Every action is pinned to a full commit SHA, with its release in a comment, and §7 gains no row. Design study Q8. | Accepted. Step 3. |
| 20261124 | Spanner | The draft workflow in the issue's comment is the basis for Step 3. It changes in four places. <br>(a) A range or base the run cannot read fails the run and says why, where the draft's loop passed silently (design study F19). <br>(b) The `python-dotenv` pin is read from `requirements.txt`, not restated (F20). <br>(c) The style step prints `automation/style_check.py`'s exit status (F21). <br>(d) Comments state what each step does and why, without citing the design study's F and Q numbers, because comments describe the code as it is and git and the issue hold how it came to be (`docs/standards/3-code.md` §3, opening). | Within Ray's answers to Q1–Q8. Shown to Ray with this spec. |
| 20261124 | Spanner | The baseline failures are found by a local run in a clean environment, the only way that survives (design study F22). | Applied rule. Step 2. |
| 20261124 | Spanner | Design study Q9: how evidence counts `xfailed`. | **Open — Ray.** Step 4 is written for the recommended option (a) and is withdrawn if Ray chooses (b). |
| 20261124 | Spanner | Design study Q10: how criterion 1's count check reads. | **Open — Ray.** AC1.1 is written for the recommended reading. |
| 20261124 | Spanner | Design study Q11: whether the marker applies on the runner only. | **Open — Ray.** Step 2 is written for the recommended option (a). |

---

## 1. Scope

**In scope:**

- `.github/workflows/tests.yml`, new.
- `automation/style_check.py` and `automation/style_check_test.py`: `DEV_REAL_VALUES` read from the environment.
- The test files under `tests/` that hold a test failing in Step 2's clean run. Each gains an `xfail` marker and nothing else.
- Pending Q9 (a): `docs/standards/6-testing.md` §6, `docs/dev/specs/_TEMPLATE_SPEC.md` §6 and `docs/dev/results/_TEMPLATE_RESULTS.md`, for the fourth count.
- The results artifact `docs/dev/results/CI_WORKFLOW_RESULTS.md`.
- **Ray's action, outside the working tree:** creating the repository secret `DEV_REAL_VALUES` before this branch's merge is pushed to `main`. Only Ray holds the values, and no session reads them. If the secret is missing, the style job fails closed.

**Out of scope:**

- **Making the check required on `main`.** That is a ruleset edit, decided separately (Q1).
- **Fixing any baseline failure.** #292, #198, #207 and #214 own those failures. Each issue removes its marker when it fixes its test.
- **A `ci` commit type** (Q4), **a §6 rule for who fixes a failed run** (Q5), and **a §7 row** (Q8).
- **Secret-scanning push protection,** which is already enabled (design study F3).
- **A session check that resolves call targets** rather than matching text (design study F14).
- **#277**, the blind spot in `automation/style_check.py` for files that were renamed. **#89**, the commit trailer. **#298**, the `-a` and `--no-verify` guard.
- **Running `automation/*_test.py` in the workflow.** The issue names the application suite only (`docs/standards/6-testing.md` §6).

## 2. Verified current state

Direct path: each step quotes the text it replaces. The claims about the runner, GitHub's settings and the draft workflow are the design study's findings F1–F26, verified at the **Read at:** commit and on GitHub on 20261124.

`real_values` call sites, found by `grep -rn 'real_values' --include='*.py' .` outside `.venv/`. No reference passes it by name uncalled or through `getattr`:

- `automation/style_check.py:393` in `main`
- `automation/style_check_test.py:270` and `:274`

## 3. Design rules

- **DR1 — The real values never exist as a file on the runner, and no log prints one.** The secret reaches the style step's `env:` only. Each entry is registered with `::add-mask::` from an environment variable before the check runs (design study F16).
- **DR2 — Each check is a job of its own.** A failure in one never hides another's result.
- **DR3 — A range or base the run cannot read fails the run and names the reason.** It never passes as an empty range.
- **DR4 — The suite's database role matches production's.** It is not a superuser, cannot create databases or roles, and owns `workmain_test`. The container's superuser only creates that role and database.
- **DR5 — A marker marks a failure; it never changes a test.** Each marked test's body, fixtures and parameters are unchanged. The proof method is stated in Step 2.
- **DR6 — A failure no open issue owns, or a test whose result differs between two clean runs, gets no marker.** Either one stops Step 2 and goes to Ray.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `automation/style_check.py` reads `DEV_REAL_VALUES` from the environment | `automation/style_check.py`, `automation/style_check_test.py` |
| 2 | Baseline failures on a clean runner marked `xfail` | the test files Step 2's run names |
| 3 | The workflow | `.github/workflows/tests.yml` |
| 4 | Pending Q9 (a): §6 counts `xfailed` | `docs/standards/6-testing.md`, `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/results/_TEMPLATE_RESULTS.md` |
| 5 | Results artifact | `docs/dev/results/CI_WORKFLOW_RESULTS.md` |

### Step 1 — `DEV_REAL_VALUES` from the environment

`real_values` gains a second parameter, and every caller is updated in this step (`docs/standards/1-workflow.md` §1.2).

**Contract:** `real_values(env: Path, environ: Mapping[str, str] | None = None) -> list[str]`, where `environ` defaults to `os.environ`.

- It returns the entries of `environ["DEV_REAL_VALUES"]`, split the same way as now, when that value yields at least one entry. Otherwise it returns the entries from the file `env`.
- On a runner whose secret is missing, `${{ secrets.DEV_REAL_VALUES }}` expands to an empty string. That empty value falls through to `.env`, which does not exist there, so the check still fails closed.

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

**Replace** the function `real_values`, from `def real_values(env: Path) -> list[str]:` through `return [entry.strip() for entry in raw.split(",") if entry.strip()]`. The new function has the contract above, and its docstring documents `environ` and the precedence between the environment and the file.

**Replace** in `main`:

```python
    values = real_values(_main_worktree() / ".env")
```

**with:**

```python
    values = real_values(_main_worktree() / ".env")  # the environment first, then .env
```

The comment is the implementer's to word or to drop. The call itself is unchanged because `environ` defaults.

**Replace** in `main`:

```python
            f"  real-value check not run: {REAL_VALUES_KEY} is not set in .env in the main working tree"
```

**with:**

```python
            f"  real-value check not run: {REAL_VALUES_KEY} is not set in the environment or in .env in the main working tree"
```

**Tests**, in `automation/style_check_test.py`:

- **An environment value is used, and the file is ignored:** the environment lists entries and the file lists different ones, and `real_values` returns the environment's.
- **An empty environment value falls through to the file:** the environment holds `""` or only commas and spaces, and `real_values` returns the file's entries.
- **`main` reads the environment:** `main` run with `DEV_REAL_VALUES` set by `monkeypatch.setenv` and no `.env` reports a listed value it finds on a changed line, without printing the value.
- The `repo` fixture calls `monkeypatch.delenv("DEV_REAL_VALUES", raising=False)`, so a value exported in the developer's shell never reaches a test that reads the fixture's `.env`.

### Step 2 — Mark the baseline failures

**1. The clean run.** Run the suite in an environment that holds what a runner holds and nothing else (design study F22):

- a detached worktree of this branch at its tip, in the session scratchpad, so no `.env` exists
- `HOME` set to an empty temporary directory, so `~/.workmain/` is absent
- `env -i`, with only these variables: `PATH` (the virtualenv's `bin` first), `HOME`, `TZ=America/Los_Angeles`, `PGTZ=America/Los_Angeles`, `GITHUB_ACTIONS=true`, and `DB_HOST`, `DB_PORT`, `DB_USER` and `DB_PASSWORD` from the main tree's `.env`, read by a script that never prints them, with `DB_NAME=workmain_test`
- output to a pipe, not a terminal
- run as `python -m pytest -p no:cacheprovider -rfE` from the worktree's root

That command is not the bare `pytest`. `python -m` puts the worktree first on `sys.path`, ahead of the editable install's main tree (`docs/standards/6-testing.md` §6). Before running it, `python -c "import workmain; print(workmain.__file__)"`, in the same environment, must print a path inside the worktree. The run is made twice.

**2. Owners.** For each test that fails, find its owning open issue with the §1.3 search by file and by test node ID. DR6 applies to a failure with no owner, and to a test that fails in one run and not the other.

**3. The marker.** Each failing test gains exactly one decorator. Pending Q11 (a), the form is:

```python
@pytest.mark.xfail("os.environ.get('GITHUB_ACTIONS') == 'true'", reason="#<owning issue>", strict=True)
```

- It goes on the test method, or on the module-level test function.
- `import pytest` is added where the module lacks it.
- If a failure is one case of a parametrized test, or comes from a fixture shared with tests that pass, the marker would cover tests that do not fail. That stops the step under DR6.

**4. Proof that the change is behaviour-neutral (`docs/standards/2-git.md` §2.2).** For each changed test file, parse the base version and the new version with `ast`. Remove from the new version every decorator that is a call to `pytest.mark.xfail`, and the `import pytest` line where this step added it. Then compare `ast.dump` of the two. Every file must compare equal. The script lives in the session scratchpad, and its output goes in the results artifact.

**5. The checks after marking:**

- The clean run, repeated, reports 0 failed, and its `xfailed` count equals the number of markers added.
- A bare `pytest` in the main tree reports 0 failed, with the same passed count as the §6 baseline.

### Step 3 — The workflow

**Create** `.github/workflows/tests.yml` with this content:

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

**Check before the commit:** each job's `run:` block, run locally in `bash -e` with its `env:` values set by hand, behaves as its comment states. That includes the two failure paths, a `BASE` and a `BEFORE` that are not in the clone (AC3.4, AC5.2), and both session-rule searches printing `none found` (AC6.1). `automation/style_check.py` passes on the file.

### Step 4 — §6 counts `xfailed` (pending Q9 (a))

**Replace** in `docs/standards/6-testing.md` §6:

```text
  - Skipped means a precondition declared with `@pytest.mark.skipif` was absent, decided before the test exercises anything.
- **Recorded test evidence states all three counts, in the form `<passed> passed, <failed> failed, <skipped> skipped`, and writes each one even when it is zero**, so the record shows whether the whole suite ran.
```

**with:**

```text
  - Skipped means a precondition declared with `@pytest.mark.skipif` was absent, decided before the test exercises anything.
  - Xfailed means a test marked `@pytest.mark.xfail(..., strict=True)`, with the open issue that owns its failure as the reason, failed as that issue records. A marked test that passes counts as failed, until its issue removes the marker.
- **Recorded test evidence states all four counts, in the form `<passed> passed, <failed> failed, <skipped> skipped, <xfailed> xfailed`, and writes each one even when it is zero**, so the record shows whether the whole suite ran.
```

**Replace** in `docs/dev/specs/_TEMPLATE_SPEC.md` §6:

```text
- **Baseline before this work:** <passed> passed, <failed> failed, <skipped> skipped, from a bare `pytest` at the **Read at:** commit.
- **Expected after:** <passed> passed, <failed> failed, <skipped> skipped.
```

**with:**

```text
- **Baseline before this work:** <passed> passed, <failed> failed, <skipped> skipped, <xfailed> xfailed, from a bare `pytest` at the **Read at:** commit.
- **Expected after:** <passed> passed, <failed> failed, <skipped> skipped, <xfailed> xfailed.
```

**Replace** in `docs/dev/results/_TEMPLATE_RESULTS.md`:

```text
- **Test suite:** <passed> passed, <failed> failed, <skipped> skipped (baseline: the spec's §6 baseline).
```

**with:**

```text
- **Test suite:** <passed> passed, <failed> failed, <skipped> skipped, <xfailed> xfailed (baseline: the spec's §6 baseline).
```

Before the commit, search the whole document set (`CLAUDE.md`, `docs/standards/`, `.claude/`, the templates) for every other statement of the three-count form, and change each one (`docs/standards/1-workflow.md` §1.5).

### Step 5 — Results artifact

`docs/dev/results/CI_WORKFLOW_RESULTS.md`, from its template. It records:

- both clean runs, with the list of failures and each one's owning issue
- the AST proof's output
- the suite counts
- each criterion's evidence

The criteria checked on GitHub (AC1.1–AC1.4, AC2.1, AC3.1, AC3.3, AC4.1, AC5.1, AC6.1) are recorded `Not met` with `Awaiting Ray` as their evidence, because the workflow first runs at close-out (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None in the steps. Close-out pushes this branch's merge to `main` and then to `dev`, each of which triggers a run (`docs/standards/2-git.md` §2.2). Ray creates the `DEV_REAL_VALUES` secret before that push (§1).

## 5. Acceptance criteria

The issue's criteria stand. Q7 and Q6 each add a property no issue criterion holds: AC1.2 extends criterion 1 to a push to `main`, and AC6.1 needs a criterion 6. The issue body gains both at close-out (`docs/standards/1-workflow.md` §1.2).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A push to `dev` runs the application suite on a GitHub-hosted runner against a fresh `workmain_test`, and its result shows on the commit | The run triggered by the push that merges this branch to `dev` shows a bare `pytest` and its summary line in its log. The results artifact writes those counts in `docs/standards/6-testing.md` §6's form, zeros included. This reading is pending Q10. |
| AC1.2 | A push to `main` runs the same suite, and its result shows on the commit | The run triggered by the push that merges this branch to `main` shows a bare `pytest` and its summary line in its log |
| AC1.3 | The suite connects as a role that is not a superuser and cannot create databases or roles | That run's log, at the step "Create the application's role and test database", shows `workmain_user` with `rolsuper`, `rolcreatedb` and `rolcreaterole` all `f` |
| AC1.4 | On the runner, only the failures that open issues own are expected, and nothing else fails | That run's summary shows 0 failed, and an `xfailed` count equal to `grep -rn 'pytest.mark.xfail(' tests/ \| wc -l` |
| AC1.5 | The markers leave a local run unchanged | A bare `pytest` in the main tree reports 0 failed, 0 xfailed, and the §6 baseline's passed count. This is pending Q11. |
| AC1.6 | No marked test's body, fixtures or parameters changed | Step 2's AST comparison reports every changed test file equal |
| AC2.1 | A pull request to `main` runs the same suite and shows its result on the pull request | `gh pr checks <N>` on the next `dev → main` pull request lists this workflow's four jobs beside CodeQL's check |
| AC3.1 | The run checks the lines the change made against the style rules with `automation/style_check.py`, and shows its exit status | The style job's log of the AC1.2 run holds `automation/style_check.py exit <n>` |
| AC3.2 | The repository holds no real value in the workflow | Ray reads `.github/workflows/tests.yml` for any real value. It holds role names, two throwaway passwords and no real value |
| AC3.3 | No run log shows a real value | Ray reads the style job's log of the AC1.2 run for any real value |
| AC3.4 | A base the style job cannot read fails it and says why | The style step's `run:` block, run locally with `BASE` set to a SHA absent from the clone, exits 1 and prints the reason |
| AC3.5 | `automation/style_check.py` takes the real values from the environment when it lists any, and from `.env` otherwise | `pytest automation/style_check_test.py` passes, including the three Step 1 tests |
| AC4.1 | The run uses the time zone the application runs in | The AC1.2 run's step "Show the run's time zone" prints a date in `PST` or `PDT` |
| AC5.1 | A push to `dev` or `main`, or a pull request to `main`, checks the message of every commit it adds with `.githooks/commit-msg` | The commit-message job's log of the AC1.1 and AC1.2 runs prints one `-> exit <n>` line for each commit in the range |
| AC5.2 | A range the commit-message job cannot read fails it and says why | The job's `run:` block, run locally with `EVENT=push` and `BEFORE` set to a SHA absent from the clone, exits 1 and prints the reason |
| AC6.1 | A push or pull request checks that no repository commits or rolls back and that no `get_session()` call exists outside `workmain/database/connection.py` | The session-rules job's log of the AC1.2 run shows `none found` under both steps |
| AC6.2 | Pending Q9 (a): the evidence form counts `xfailed` | Ray reads `docs/standards/6-testing.md` §6 and both templates for the four-count form, and §6 for the definition of xfailed |

## 6. Test plan

- **Baseline before this work:** 1800 passed, 0 failed, 0 skipped, from a bare `pytest` at `94d5c63`, whose code is the same as at the **Read at:** commit. `pytest automation/`: 134 passed, 0 failed, 0 skipped.
- **Expected after:**
  - The application suite, locally: 1800 passed, 0 failed, 0 skipped, 0 xfailed (pending Q11 (a)).
  - The application suite, in the clean run and on the runner: 0 failed, with `xfailed` equal to the markers added. Passed and skipped are set by Step 2's run.
  - `pytest automation/`: 137 passed, 0 failed, 0 skipped.
- **Test files:**
  - `automation/style_check_test.py`: three tests for Step 1, and the `repo` fixture's `delenv`.
  - Under `tests/`: markers only (DR5).

## 7. Risks and rollback

- **The runner fails a test the clean run passed,** for example from a package difference. The first run on `main` is then red. The role that caused the failure fixes it, on a new branch (Q5).
- **A style violation stays red on `dev`.** A run on `dev` checks everything `dev` holds that `main` does not, because its base is `origin/main`. So one violation pushed to `dev` keeps every later `dev` run red until the next release. Read a red `dev` result with that in mind.
- **A pull request from a fork gets no secrets,** so its style job fails closed. Ray is the only contributor.
- **A forced push fails the run.** The `protection` ruleset blocks non-fast-forward pushes except through the admin bypass (design study F4). A forced push to `dev` or `main` fails the commit-message job, and on `main` the style job too, each saying why (DR3).
- **When an owning issue fixes its test,** the strict marker turns the run red until that issue removes the marker. That is intended (Q1).
- **Rollback:**
  - Step 3: delete `.github/workflows/tests.yml`.
  - Step 2: revert its commit. The markers are inert locally.
  - Step 1: revert its commit. `.env` is still read.
  - Step 4: revert its commit, together with any results already written in four-count form.

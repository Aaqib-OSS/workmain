# A GitHub Actions run of the suite, the style check and the commit-message check — Implementation Results

**Status:** Active
**Author:** Spanner
**Date:** 20261124
**Spec:** `../specs/CI_WORKFLOW_SPEC.md`
**Released as:** `n/a`

---

## 1. Summary

Complete on the branch. The workflow `.github/workflows/tests.yml` has four report-only jobs: the application suite, the style check on changed lines, the commit-message check, and the two session-rule searches. `automation/style_check.py` now reads `DEV_REAL_VALUES` from the environment. The four tests that fail on a clean runner are marked `xfail` with their owning issues. Every `run:` block was run locally. The criteria checked on GitHub wait for close-out, because the workflow first runs on the push of this branch's merge to `main`.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `real_values` reads the environment first, then `.env` (`288b55c`) | `automation/style_check.py`, `automation/style_check_test.py` | +4 (automation) |
| 2 | Four baseline failures marked `xfail` (`8cda7aa`) | `tests/test_database_isolation.py`, `tests/test_gdrive.py`, `tests/test_slack_channel_config.py` | 0 |
| 3 | The workflow (`8391732`) | `.github/workflows/tests.yml` | 0 |
| 4 | This artifact | `docs/dev/results/CI_WORKFLOW_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Carried | Carried to #297. Ray, 20261124: the run on the push that merges this branch to `dev`, its `pytest` summary line, and the counts written in §6 form in §5 |
| AC1.2 | Carried | Carried to #297. Ray, 20261124: the run on the push that merges this branch to `main` |
| AC1.3 | Carried | Carried to #297. Ray, 20261124: that run's role step shows `f`, `f`, `f` for `workmain_user` |
| AC1.4 | Carried | Carried to #297. Ray, 20261124: that run's summary shows 0 failed. The local clean run (§5) showed 0 failed, 4 xfailed |
| AC1.5 | Met | `git diff main -- tests/` adds four `@pytest.mark.xfail(reason="#<N>")` lines and two `import pytest` lines. Its only other change replaces the asserted value in `test_slack_set_workspace_shows_config` with an invented one |
| AC2.1 | Carried | Carried to #297. Ray, 20261124: `gh pr checks <N>` on the next `dev → main` pull request |
| AC3.1 | Carried | Carried to #297. Ray, 20261124: the style job's log holds `automation/style_check.py exit <n>`. A local run of the step printed `automation/style_check.py exit 0` |
| AC3.2 | Carried | Carried to #297. Ray, 20261124: a reading of `.github/workflows/tests.yml` for any real value |
| AC3.3 | Met | `pytest automation/style_check_test.py` passes, including `test_values_in_the_environment_are_used_over_the_file`, `test_an_environment_value_with_no_entries_falls_through_to_the_file` (two cases) and `test_main_reads_the_values_from_the_environment_without_printing_them` |
| AC4.1 | Carried | Carried to #297. Ray, 20261124: the run's time-zone step prints `PST` or `PDT` |
| AC5.1 | Carried | Carried to #297. Ray, 20261124: the commit-message job prints one `-> exit <n>` line per commit. A local run over `origin/main..8cda7aa` printed seven lines, each `-> exit 0` |
| AC5.2 | Met | The commit-message `run:` block, run locally in `bash -e` with `EVENT=push` and an absent `BEFORE`, printed "Range … cannot be read from this clone…" and exited 1. The style step with an absent `BASE` did the same |
| AC6.1 | Carried | Carried to #297. Ray, 20261124: the session-rules job shows `none found` twice. A local run of both steps printed `none found` and exited 0 |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | The spec changes the "real-value check not run" message, and an existing assertion in `automation/style_check_test.py` checked the old wording | within approved meaning | The assertion now checks the new wording | Spanner, 20261124 |
| 2 | `test_values_are_split_on_commas_with_whitespace_and_empty_entries_dropped` read `os.environ` once `environ` had a default | within approved meaning | It passes `{}`, so a value exported in the shell cannot change its result | Spanner, 20261124 |
| 3 | The spec expected 137 automation tests. The empty-value test is parametrized over `""` and `" , ,"`, so 138 | within approved meaning | Recorded here | Spanner, 20261124 |
| 4 | `test_slack_set_workspace_shows_config` asserted on a value listed in `DEV_REAL_VALUES` | none | Its assertion now uses an invented value, which Ray approved as a deviation. Locally the test now reports xfailed, because it reads the live `~/.workmain/` config until #214 makes it set up its own | Ray, 20261124 |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | A private `_entries` helper splits a raw value for both sources | Repeating the split expression | One home for the split rule |
| 2 | 1 | The tests use invented values `Vrell` and `wopsy-dune` | Reusing `Qzx` | A distinct value shows which source won |
| 3 | 3 | The workflow file is extracted from the spec's code block byte for byte | Retyping it | The spec's quote is the verification |

## 5. Verification

- **Application suite, local bare `pytest`:** 1796 passed, 0 failed, 0 skipped. Note: 3 xpassed, 1 xfailed. Baseline: 1800 passed, 0 failed, 0 skipped.
- **Application suite, clean run** (Step 2: a detached worktree under `mktemp -d`, an empty `HOME`, `env -i`, output piped, `python -m pytest`):
  - Before the markers: 1791 passed, 4 failed, 5 skipped.
  - After: 1791 passed, 0 failed, 5 skipped. Note: 4 xfailed.
  - The four failures and their owners:
    - `tests/test_database_isolation.py::TestTestDatabaseGuard::test_a_run_naming_another_database_stops_before_any_test`: #292
    - `tests/test_gdrive.py::TestGDocsCLI::test_10_upload_all_dry_run`: #207
    - `tests/test_slack_channel_config.py::TestSlackSetWorkspace::test_slack_set_workspace_shows_config`: #214
    - `tests/test_slack_channel_config.py::TestSlackSetWorkspace::test_slack_set_workspace_no_writes`: #214
- **`pytest automation/`:** 138 passed, 0 failed, 0 skipped. Baseline: 134 passed, 0 failed, 0 skipped.
- **Workflow `run:` blocks, run locally** in `bash -e`, extracted from the committed file:
  - The style step exits 0 against `origin/main` with an invented value.
  - The style step exits 1, giving the reason, for an absent base.
  - The commit-message step exits 0 over seven commits.
  - The commit-message step exits 1, giving the reason, for an absent `before`.
  - Both session-rule steps print `none found` and exit 0.
- **`automation/style_check.py` and `automation/architecture_check.py`:** both exit 0.
- **Live verification:** at close-out, on the runs this branch's merge pushes trigger.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Real value in a test | Fixed on this branch by Ray's deviation (§4 row 4). Earlier commits still hold the value, as with #276 | History is not rewritten |

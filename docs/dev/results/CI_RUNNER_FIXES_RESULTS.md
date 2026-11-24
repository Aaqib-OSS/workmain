# Two defects in the tests workflow's first runs — Implementation Results

**Status:** Active
**Author:** Spanner
**Date:** 20261124
**Spec:** `../specs/CI_RUNNER_FIXES_SPEC.md`
**Released as:** `n/a`

---

## 1. Summary

Complete on the branch. `.github/workflows/tests.yml` has two fixes:

- The style job's install step is a block scalar, so YAML no longer cuts it at ` #`.
- The runner creates `workmain_test` with the `C.UTF-8` locale, as production has, and prints the collation beside the role.

Both criteria are checked on the run that this branch's merge push to `main` triggers.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Both fixes (`dac9e98`) | `.github/workflows/tests.yml` | 0 |
| 2 | This artifact | `docs/dev/results/CI_RUNNER_FIXES_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | **Not met** | `Awaiting Ray`: the run on this branch's merge push to `main` shows `C.UTF-8` for `datcollate` and `datctype`, and 0 failed |
| AC3.1 | **Not met** | `Awaiting Ray`: the same run's style job log holds `automation/style_check.py exit 0` |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |

## 5. Verification

- **Every `run:` value**, loaded with `yaml.safe_load`, has balanced quotes. The install step's value holds the whole command through `requirements.txt`, and runs locally in `bash -e` with exit 0.
- **`CREATE DATABASE … LOCALE 'C.UTF-8'`** was not run locally, because the local role cannot create databases. The run checks it.
- **Suites:** unchanged from #297's close-out. No test or application file changed.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |

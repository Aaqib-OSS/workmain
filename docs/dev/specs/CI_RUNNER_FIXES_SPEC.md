# Two defects in the tests workflow's first runs — Spec

**Status:** Approved
**Author:** Spanner
**Date:** 20261124
**Read at:** 1367734de27a4020aeaa105b7ac14f637a450484
**Branch:** `chore/issue-297-ci-runner-fixes` (base: `main`, `docs/standards/2-git.md` §2.1)
**Target release:** none. A `chore/*` merge is not a release (`docs/standards/2-git.md` §2.2).
**Originating item:** Issue #297
**Design study:** `n/a`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261124 | Ray | Spec approved. | Accepted. |
| 20261124 | Spanner | Runs `45446215786` (`main`) and `45446219024` (`dev`) both failed in two jobs. The role that caused a failure fixes it (`../archive/design/DESIGN_CI_WORKFLOW.md` Q5). | This spec. |

---

## 1. Scope

**In scope:** `.github/workflows/tests.yml`, and this spec's results artifact.

**Out of scope:** everything else. #297's artifact set in `docs/archive/` is history (`docs/standards/1-workflow.md` §1.5).

**The two defects:**

- **The style job never reached the check.** In its install step, `run:` is a plain YAML scalar, and YAML reads ` #` inside a plain scalar as the start of a comment. The command was cut at `[^`, and bash failed with "unexpected EOF while looking for matching `''". The pre-merge check ran each extracted `run:` block, but not this one.
- **The suite had 2 failures on both runs:** 1789 passed, 2 failed, 5 skipped, 4 xfailed. The tests were `tests/test_fake_unit_of_work.py::TestClientContract::test_find_by_name_fuzzy_matches_substrings_in_name_order[real]` and `::test_list_all_returns_every_client_in_name_order[real]`. They expect byte-order sorting (`ZqvC` before `Zqvb`). The container's `CREATE DATABASE` took the image's default locale, `en_US.utf8`. Production and the local `workmain_test` both use `C.UTF-8`, with the libc provider, read from `pg_database` on 20261124. So the runner did not match production, which DR4 of the archived spec intends for the role.

## 2. Verified current state

Direct path: each step quotes the text it replaces.

## 3. Design rules

- **DR1 — The runner's `workmain_test` matches production's collation and character type, as its role already does.**

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Both fixes | `.github/workflows/tests.yml` |
| 2 | Results artifact | `docs/dev/results/CI_RUNNER_FIXES_RESULTS.md` |

### Step 1

**Replace:**

```yaml
        run: pip install -r requirements-dev.txt "$(grep -oE '^python-dotenv==[^ #]+' requirements.txt)"
```

**with:**

```yaml
        run: |
          pip install -r requirements-dev.txt "$(grep -oE '^python-dotenv==[^ #]+' requirements.txt)"
```

**Replace:**

```yaml
            -c "CREATE DATABASE workmain_test OWNER workmain_user" \
            -c "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname = 'workmain_user'"
```

**with:**

```yaml
            -c "CREATE DATABASE workmain_test OWNER workmain_user TEMPLATE template0 LOCALE_PROVIDER libc LOCALE 'C.UTF-8'" \
            -c "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname = 'workmain_user'" \
            -c "SELECT datname, datcollate, datctype FROM pg_database WHERE datname = 'workmain_test'"
```

Change the comment above that step so it says the database matches production's locale as well.

**Before the commit:**

- Load every `run:` value with `yaml.safe_load`, and check that none is cut short. Every quote is balanced, and the install step's value holds `requirements.txt`.
- Run the install step's value in `bash -e`.

### Step 2

`docs/dev/results/CI_RUNNER_FIXES_RESULTS.md`, from its template.

### Authorization points

None in the steps. Close-out merges to `main`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The runner's suite runs against a `workmain_test` with production's collation, and passes | The run on this branch's merge push to `main`: its role step shows `C.UTF-8` for both `datcollate` and `datctype`, and its summary shows 0 failed |
| AC3.1 | The style job reaches `automation/style_check.py` and prints its exit status | The same run's style job log holds `automation/style_check.py exit 0` |

## 6. Test plan

No test files change. The application suite and `pytest automation/` are unchanged from #297's close-out: 1796 passed, 0 failed, 0 skipped, and 138 passed, 0 failed, 0 skipped.

## 7. Risks and rollback

- **The `C.UTF-8` locale might not exist in the `postgres:16` image.** The run's role step would then fail and say so. The Debian-based image ships with `C.UTF-8`.
- **Rollback:** revert Step 1's commit.

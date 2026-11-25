# markdownlint Check on Changed Lines — Spec

**Status:** Draft
**Author:** Spanner
**Date:** 20261125
**Read at:** 7c564eec943cb4817b6d99001e2d29d8673f3877
**Branch:** `chore/issue-308-markdownlint-check` (base: `docs/standards/2-git.md` §2.1)
**Target release:** none: a `chore/*` merge carries no version bump, `CHANGELOG.md` entry, tag or Release (§2.2)
**Originating item:** Issue #308
**Design study:** `../design/DESIGN_MARKDOWNLINT_CHECK.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261125 | Spanner | The engine is markdownlint-cli2, the one the editor runs, and the only one that reads `.markdownlint.json` as written (design study §4, F3) | DR1 |
| 20261125 | Spanner | The check runs inside `automation/style_check.py`, which gives it the changed-line filter, `SKIPPED` and every existing caller (design study §4, F7) | DR3, DR4 |
| 20261125 | Ray | markdownlint-cli2 is pinned in `automation/package.json` with its lockfile and installed with `npm ci --prefix automation` (design study Q1, Option A) | DR1, DR2, Step 1, Step 2 |
| 20261125 | Ray | `.markdownlint.json` is not trimmed (design study Q2) | §1 Out of scope |
| 20261125 | Ray | A markdownlint finding is also reported when the line before or after it is a changed line (design study Q3, option (b)) | DR4 |
| 20261125 | Ray | The new tests follow the inline `repo` harness; AC1 is restated (design study Q4) | §5 note on AC1 |

---

## 1. Scope

**In scope:**

- `automation/style_check.py` runs markdownlint-cli2, configured by `.markdownlint.json`, over the Markdown files a branch changed, and reports each finding on a changed line or next to one.
- `automation/package.json` and `automation/package-lock.json` pin markdownlint-cli2. `.gitignore` ignores `automation/node_modules/`.
- `automation/style_check_test.py` covers the check.
- `.github/workflows/tests.yml` job `style` installs Node and markdownlint-cli2 before it runs the check.
- `docs/standards/1-workflow.md` §1.5 names the check as where its Markdown rule is enforced.

**Out of scope:**

- Changing `.markdownlint.json` (design study Q2).
- Fixing the 96 findings already in live Markdown (design study F5) or those in `docs/archive/` (F6). They are fixed when a branch touches them, as #297's design brings code up to the rules.
- The hard-wrap check, `markdown_violations`, which stays as it is.
- Renamed files: a file the branch renamed and edited is not checked, by this check or any other in the module. That is #277.
- Running the `automation/` suite in CI (design study F12).
- `README.md`'s install steps. The check's stop message names the install command (DR2), as ruff's does.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `check(changes, values)` keeps a violation only where its span `(first, last)` includes a changed line, or where its file maps to `None` (new or untracked). `main` prints each kept violation as `<path>:<line> — <message>`, indented two spaces | `automation/style_check.py:342` `check`, `:416` `main` |
| `check` runs `markdown_violations` on every changed path ending `.md` that exists | `automation/style_check.py:364-368` |
| `python_violations` finds ruff with `shutil.which`, stops with `SystemExit` when ruff is missing or exits other than 0 or 1, and runs only when there are Python paths | `automation/style_check.py:222-257` |
| `changed_lines` drops `SKIPPED` paths: `CHANGELOG.md`, `docs/archive/`, `scripts-deprecated/`, `staging/` | `automation/style_check.py:38`, `:112` |
| `_main_worktree()` returns the main working tree's root from any linked worktree; `main` reads `.env` from it | `automation/style_check.py:65`, `:408` |
| The module docstring states what is checked and `Requires git, ruff and python-dotenv.` | `automation/style_check.py:1-21` |
| markdownlint-cli2 0.24.2 (markdownlint 0.42.2) is what the editor runs. It needs Node 22 or later. It reads `.markdownlint.json` from its working directory | design study F3, F4; `markdownlint-cli2 --help` |
| markdownlint-cli2 prints each finding to stderr as `<path>:<line>[:<column>] error <MDnnn>/<name> <description>[ [<detail>]]`. It prints progress to stdout. It exits 0 with no findings, 1 with findings, and 2 on an error such as a missing file. A path prefixed with `:` is read literally, not as a glob | run 20261125 in the scratchpad |
| A paragraph added directly under an existing heading is reported as `MD022` on the heading's line, the line before the added one | design study F8 |
| The `repo` test fixture builds a temporary repository at `tmp_path` and points `sc.ROOT` at it. `test_a_wrapped_line_added_to_an_existing_document_is_reported` asserts the whole violation list, and `test_main_exits_1_on_a_violation_and_0_without` asserts exit 0 on a Markdown change | `automation/style_check_test.py:69`, `:242`, `:253` |
| pytest's default `norecursedirs` includes `node_modules`, and ruff's default exclusions include `node_modules`, so an installed `automation/node_modules/` adds nothing to `pytest automation/` or ruff | pytest and ruff defaults; `pyproject.toml:1-8` sets neither |
| `.github/workflows/tests.yml` job `style` sets up Python and installs ruff and python-dotenv; it sets up no Node | `.github/workflows/tests.yml:86-137` |
| `actions/setup-node` v7.1.0 is commit `949feb2413d6458794dcd2491c4babbbce0c15c1` | `gh api repos/actions/setup-node/git/ref/tags/v7.1.0`, 20261125 |
| Callers of `style_check.py`: `.claude/skills/closeout/SKILL.md:35` (P7), `.claude/skills/session-start/references/anvil.md:46` (step 5), `.claude/skills/session-start/references/caliper.md:52` (I6, `--base`, detached worktree), `.github/workflows/tests.yml:135`. No caller's command line changes | `git grep -n style_check -- . ':!docs/archive' ':!automation/style_check*.py'` |
| `pytest automation/`: 138 passed, 0 failed, 0 skipped | run 20261125 at the **Read at:** commit |

## 3. Design rules

- **DR1 — The tool and its version.** markdownlint-cli2 at exactly `0.24.2`, named in `automation/package.json` `devDependencies`, with the whole tree pinned by `automation/package-lock.json`. `automation/package.json` is `"private": true` and declares no scripts.
- **DR2 — Where the tool is found.** `<main working tree>/automation/node_modules/.bin/markdownlint-cli2`, where the main working tree is `_main_worktree()`, so a linked worktree such as Caliper's I6 uses the main tree's install, as it uses the main tree's `.env`. When there are Markdown paths to check and that file does not exist, the check stops with `SystemExit("markdownlint-cli2 was not found (npm ci --prefix automation)")`. When markdownlint-cli2 exits other than 0 or 1, the check stops with `SystemExit` naming its stderr.
- **DR3 — Which files and which rules.** The same paths `markdown_violations` gets: every changed path ending `.md` that exists, after `SKIPPED`. They are passed in one run, each prefixed with `:`, with `ROOT` as the working directory, so markdownlint-cli2 finds `ROOT/.markdownlint.json` as the editor does. No `--config` is passed.
- **DR4 — Which findings are reported.** A finding is reported when its line, the line before it or the line after it is a changed line, or when its file is wholly changed. It is printed at the line markdownlint reports. Every other violation keeps the existing changed-line filter.
- **DR5 — The report.** Each finding is printed in the existing form, `<path>:<line> — <message>`, where `<message>` is markdownlint's text after `error` and the space that follows it: `<MDnnn>/<name> <description>` and any detail. It counts in the summary line's violation total and in the exit code, as every other violation does.
- **DR6 — The docstring states the dependency.** The module docstring says Markdown lines are also checked with markdownlint-cli2 against `.markdownlint.json`, and that the check requires Node 22 or later and markdownlint-cli2 installed with `npm ci --prefix automation`.

## 4. Steps

| Step | Deliverable | Files | ACs |
| --- | --- | --- | --- |
| 1 | The pinned tool, the check and its tests: DR1–DR6 | `automation/package.json`, `automation/package-lock.json`, `.gitignore`, `automation/style_check.py`, `automation/style_check_test.py` | AC1.1–AC1.6, AC1.8 |
| 2 | CI installs Node and the tool | `.github/workflows/tests.yml` | AC2.1 |
| 3 | §1.5 cites the check | `docs/standards/1-workflow.md` | AC3.1 |
| 4 | The results artifact | `docs/dev/results/MARKDOWNLINT_CHECK_RESULTS.md` | AC1.7, all |

Every addition lives in `automation/`, which `docs/standards/7-file-placement.md` §7 assigns to dev tooling and `docs/ARCHITECTURE.md` does not map. `automation/style_check.py` owns checking a branch's changed lines (design study §4).

**Step 1.**

- `automation/package.json`, per DR1:

  ```json
  {
    "private": true,
    "devDependencies": {
      "markdownlint-cli2": "0.24.2"
    }
  }
  ```

- `automation/package-lock.json` is the file `npm install --prefix automation` writes from that `package.json`, committed unedited.
- `.gitignore` gains a section after its last line, `test_notes-*.md`:

  ```text

  # Node, for automation/ tooling
  automation/node_modules/
  ```

- `automation/style_check.py` gains `markdownlint_violations(paths: list[str]) -> list[Violation]`, which runs the tool per DR2 and DR3 and returns one `(path, line, line, message)` entry per finding with DR5's message. `check` runs it on the DR3 paths and applies DR4 to its entries. `check`'s and `main`'s signatures are unchanged. The module docstring is updated per DR6.
- `automation/style_check_test.py`:
  - The `repo` fixture writes a copy of the repository's `.markdownlint.json` into the temporary repository, and links the repository's `automation/node_modules` into the temporary repository's `automation/`, ignored there. Every test then runs the real tool against the real rule set. Existing tests whose Markdown now draws a markdownlint finding are updated so each one still tests only what its name says.
  - Tests that run markdownlint are skipped when it is not installed in the repository, as the ruff tests are skipped without ruff.
  - The new tests are those §5 names.

**Step 2.** In `.github/workflows/tests.yml` job `style`, replace:

```yaml
      # ruff from requirements-dev.txt; python-dotenv at the version requirements.txt pins.
      - name: Install ruff and python-dotenv
        run: |
          pip install -r requirements-dev.txt "$(grep -oE '^python-dotenv==[^ #]+' requirements.txt)"
```

with:

```yaml
      # ruff from requirements-dev.txt; python-dotenv at the version requirements.txt pins.
      - name: Install ruff and python-dotenv
        run: |
          pip install -r requirements-dev.txt "$(grep -oE '^python-dotenv==[^ #]+' requirements.txt)"

      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version: "24"

      # markdownlint-cli2 at the version automation/package-lock.json pins.
      - name: Install markdownlint-cli2
        run: npm ci --prefix automation
```

**Step 3.** In `docs/standards/1-workflow.md` §1.5 **Writing.**, replace:

```text
- **Markdown is written one line per paragraph**, per list item and per table row, and the editor wraps it. `.markdownlint.json` is set to match, and governs all formatting.
```

with:

```text
- **Markdown is written one line per paragraph**, per list item and per table row, and the editor wraps it. `.markdownlint.json` governs all other formatting, and turns its line-length rule off to match. `automation/style_check.py` checks both on every line a branch changes.
```

**Step 4.** The results artifact, per `docs/standards/1-workflow.md` §1.1.

### Authorization points

None.

## 5. Acceptance criteria

Each test named below is in `automation/style_check_test.py`.

AC1 is restated (§1.2; design study Q4). The issue's check reads "tests in `automation/` with fixture files", and these tests write their Markdown inline in the `repo` fixture's temporary repository, as the existing tests do. The issue body needs that edit at close-out.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A changed Markdown line that breaks a rule `.markdownlint.json` enables fails the style check, and the output names the file, line and rule | `pytest automation/style_check_test.py` passes, including `test_a_markdownlint_finding_on_a_changed_line_is_reported`, which runs `main` on a branch adding a fenced block with no language and asserts exit 1 and `<path>:<line> — MD040/` in the output |
| AC1.2 | A markdownlint finding on a line the branch did not change, and not next to one, is not reported, so the existing findings do not fail a branch | `test_a_markdownlint_finding_on_an_untouched_line_is_not_reported` passes, with the finding in the base commit and the branch changing a line at least two lines away |
| AC1.3 | A finding reported on the line next to a changed line is reported, so a paragraph added under an existing heading fails | `test_a_markdownlint_finding_next_to_a_changed_line_is_reported` passes, with a paragraph added directly under a heading from the base commit, asserting an `MD022` violation at the heading's line |
| AC1.4 | The rules are those `.markdownlint.json` sets, not markdownlint's defaults | `test_the_rules_are_read_from_markdownlint_json` passes, with a changed line over 80 characters drawing no violation, which the default `MD013` would report |
| AC1.5 | With Markdown to check and markdownlint-cli2 not installed, the check stops and names the install command | `test_the_check_stops_when_markdownlint_cli2_is_not_installed` passes, asserting `SystemExit` with `npm ci --prefix automation` in its message |
| AC1.6 | Run in a linked worktree, as Caliper's I6 runs it, the check uses the main working tree's install | `test_markdownlint_is_found_from_a_linked_worktree` passes, running `main` with `--base` from a linked worktree that has no `automation/node_modules`, and asserting a markdownlint violation is reported |
| AC1.7 | On this repository the check runs markdownlint on this branch's Markdown | `npm ci --prefix automation`, then `python3 automation/style_check.py` on this branch, prints `PASS`, with this spec, the design study and the results artifact among its changed files |
| AC1.8 | Every existing style-check test still passes, testing what it did before | `pytest automation/` reports 144 passed, 0 failed, 0 skipped |
| AC2.1 | The CI `style` job runs markdownlint as part of the check | The `style` job's log on this branch's pull request shows the `npm ci --prefix automation` step and `automation/style_check.py exit 0` |
| AC3.1 | §1.5 cites the check as where its Markdown rule is enforced | Ray reads `docs/standards/1-workflow.md` §1.5 **Writing.**, first item, for the check named as what enforces both `.markdownlint.json` and one line per paragraph |

The command line is the only entry path to the check (§2 callers). AC1.1 and AC1.6 run it through `main`, without and with `--base`; AC2.1 runs it in CI.

## 6. Test plan

- **Baseline before this work:** `automation/`: 138 passed, 0 failed, 0 skipped (§2). `tests/`: unchanged by this work, which touches nothing under `workmain/` or `tests/`; close-out runs it.
- **Expected after:** `automation/`: 144 passed, 0 failed, 0 skipped, with ruff and markdownlint-cli2 installed. Step 1 adds the six tests AC1.1–AC1.6 name.
- **Test files:** `automation/style_check_test.py` only, extended as Step 1 states.

## 7. Risks and rollback

- **A branch editing a file with existing findings fails on one next to its edit** (DR4). That is the rule working; the line is fixed on the branch. The 7 live files in design study F5 are where this is likeliest.
- **The tool is missing on a machine or worktree.** DR2's stop names the install command. A session's first run after this merges needs `npm ci --prefix automation` once in the main working tree.
- **The editor and the check drift apart** when the extension updates its bundled markdownlint-cli2. The check then follows `automation/package.json`, and moving it to the editor's new version is a one-line change plus `npm install --prefix automation`.
- **Known limitation: a renamed file is not checked** (§1 Out of scope, #277).
- **Rollback:** revert the step commits. Nothing outside `automation/`, `.gitignore`, `.github/workflows/tests.yml` and §1.5 changes, and no caller's command line changes.

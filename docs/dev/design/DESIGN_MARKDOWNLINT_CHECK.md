# markdownlint check on changed lines — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner
**Date:** 20261125
**Read at:** 49dd1662047c591655be5ecad72db15d98f99406
**Originating item:** Issue #308

---

## 1. Purpose

`docs/standards/1-workflow.md` §1.5 says `.markdownlint.json` governs all Markdown formatting, but nothing runs it: the editor flags only the file open in it, so Markdown an agent writes reaches commit unlinted. This study decides how the rule set becomes a check that runs locally and in CI, and whether the rule set changes first. The read was read-only; the only things run were markdownlint-cli2, installed outside the repository in the session scratchpad, and `git status`, which showed the tree unchanged.

## 2. Scope of the read

- **Source the work changes:** `automation/style_check.py`, `automation/style_check_test.py`, `.markdownlint.json`, `.github/workflows/tests.yml` job `style`, `docs/standards/1-workflow.md` §1.5, `.gitignore`.
- **Checks that enforce a rule the work touches** (§7 locations): `automation/style_check.py` (§1.5 hard wrapping), `.github/workflows/tests.yml` (runs it). No other file in `automation/`, `.github/workflows/` or `.githooks/` reads Markdown formatting.
- **Every statement of the rule:** `git grep -n -i markdownlint -- . ':!docs/archive'` returns `docs/standards/1-workflow.md:127` only. Every caller of the check: `git grep -n style_check -- . ':!docs/archive' ':!automation/style_check*.py'` returns `.claude/skills/closeout/SKILL.md` P7, `.claude/skills/session-start/references/anvil.md` step 5, `.claude/skills/session-start/references/caliper.md` I6, `.github/workflows/tests.yml` and `docs/standards/3-code.md` §3.
- **Issues by file** (§1.3): `automation/style_check.py` → #264, #297, #277, #308, #240; `automation/style_check_test.py` → #277; `.markdownlint.json` → #308; `.github/workflows/tests.yml` → #308; `docs/standards/1-workflow.md` → 24 issues, none about Markdown formatting (#284 is about how a check command displays); `requirements-dev.txt` → #107. No `parked` issue names a file this work changes. Term searches `markdownlint`, `Markdown lint`, `hard wrap`, `style_check` add nothing beyond these.
- **Measurement:** markdownlint-cli2 0.24.2 (markdownlint 0.42.2) run with the repository's `.markdownlint.json` over the tracked Markdown `style_check.py` does not skip, and separately over `docs/archive/{design,specs,results}/`.
- **Left out:** the markdownlint rules' own documentation, beyond the findings they produced here; Node availability on GitHub's `ubuntu-latest` image, which was not read (F9).

## 3. Findings

| # | Finding | Evidence (file:line, symbol) |
| --- | --- | --- |
| F1 | The issue's claim holds: no check reads `.markdownlint.json`. `style_check.py` checks Markdown only for hard wrapping, its own rule, which `.markdownlint.json` turns off as `MD013`. | `automation/style_check.py:289` `markdown_violations`; `.markdownlint.json:3` `"MD013": false`; F2 search |
| F2 | §1.5 is the rule's only statement: "`.markdownlint.json` is set to match, and governs all formatting." | `docs/standards/1-workflow.md:127` |
| F3 | The editor runs markdownlint-cli2 0.24.2, markdownlint 0.42.2, from the VS Code extension `davidanson.vscode-markdownlint` 0.63.0. These are the current npm releases, and the versions measured here. `.markdownlint.json` is that engine's config format. | extension `package.json` `"markdownlint-cli2": "0.24.2"`; `npm view markdownlint-cli2 version` → `0.24.2` |
| F4 | markdownlint-cli2 0.24.2 needs Node 22 or later. This machine has Node v25.2.1. The repository has no `package.json`, and `.gitignore` has no `node_modules` entry. | `npm view markdownlint-cli2@0.24.2 engines` → `{ node: '>=22' }`; `node --version` |
| F5 | Live Markdown fails today: 96 findings in 7 of 42 files. 72 are `MD060` (table pipe spacing) in `docs/AI_SETTINGS_GUIDE.md`, `docs/OAUTH_SETUP.md` and `docs/SLACK_SETUP.md`. The rest: `MD031` 12, `MD040` 6, `MD001` 2 (both in `automation/fixtures/standards_*.md`), `MD034`, `MD032`, `MD022`, `MD012` 1 each. A whole-file check would fail on a branch that touches any of these files. | measurement, §2 |
| F6 | Archived artifacts confirm the problem the issue names: 114 of 300 files have findings. The largest counts are `MD060` 1612, `MD050` 712, `MD031` 612, `MD032` 390, `MD040` 379. Artifacts archived this month carry them, among them `docs/archive/design/DESIGN_CI_WORKFLOW.md` with 33. `MD050` fires on dunder names written outside backticks (`__repr__` at `docs/archive/design/DESIGN_DATABASE_SCHEMA_HYGIENE_20260608_v1.2.md:21`), which render as bold, so it is a real defect, not a style clash. | measurement, §2 |
| F7 | `style_check.py` filters every finding to a changed line in `check`, and limits ruff, which it runs on PATH, the same way. A tool added there inherits the changed-line filter, the `SKIPPED` paths (`CHANGELOG.md`, `docs/archive/`, …), and every caller in §2: P7, Anvil step 5, Caliper I6 and CI. | `automation/style_check.py:342` `check`; `:222` `python_violations`; `:38` `SKIPPED` |
| F8 | markdownlint reports some findings on a line next to the one the branch changed. A paragraph added directly under an existing heading is reported as `MD022` on the heading's line, which the branch did not change, so a filter that keeps only changed lines drops it. `MD031` (fence after a paragraph), `MD032` (list after a paragraph) and `MD012` (an added blank line) are reported on the added line. | scratch files, §2: heading at line 3, added line 4 → `a.md:3 MD022` |
| F9 | Unverified: which Node version `ubuntu-latest` provides. The `style` job installs Python only, and no step sets up Node. | `.github/workflows/tests.yml:86-137` |
| F10 | markdownlint-cli2 prints each finding as `<path>:<line>[:<column>] error <MDnnn>/<name> <description> [<detail>]`, and exits 1 when it finds any, as ruff does. It has no built-in JSON output; JSON needs the separate `markdownlint-cli2-formatter-json` package, set in a `.markdownlint-cli2.*` file. | `markdownlint-cli2 --help`; output, §2 |
| F11 | The existing tests write their Markdown inline into a temporary git repository; none reads a fixture file. Issue AC1's check names "tests in `automation/` with fixture files". | `automation/style_check_test.py:45` `BASE`, `:69` `repo` |
| F12 | Existing defect, outside scope: CI's bare `pytest` collects `tests/` only, so `automation/` tests, `style_check_test.py` among them, run in no CI job. | `pyproject.toml:2` `testpaths = ["tests"]`; `docs/standards/6-testing.md:5` |

## 4. Governing rules and options

**Governing rules.**

- `docs/ARCHITECTURE.md` § 2 names no owner for process tooling. §7 places it in `automation/`, and `automation/style_check.py` owns checking a branch's changed lines (F7).
- §1.5: `.markdownlint.json` governs all Markdown formatting.
- §1.5 "A change to a rule searches the whole document set": F2 has the rule's one statement, and the §2 search names every caller of the check.
- Issue #297's design, archived in `docs/archive/design/DESIGN_CI_WORKFLOW.md`: code is brought up to the rules as it is touched, not all at once (F5 shows why).

**Engine.** markdownlint-cli2 is the only valid option. It is the engine the editor runs (F3) and reads `.markdownlint.json` as written. A Python port such as `pymarkdownlnt` has a config format and rule set of its own, so it would disagree with the editor and break §1.5.

**Where the check runs.** Inside `style_check.py` is the only valid option. It gets the changed-line filter, the skipped paths and all four callers without a new call site (F7). A separate CI step that lints whole files would fail on 96 existing findings (F5), and would leave out P7, Anvil and Caliper, which run locally.

The decision left is how the tool is pinned and installed. Q1 holds it; the options are below.

### Option A — `automation/package.json` and its lockfile

- **Approach:** `automation/package.json` names `markdownlint-cli2` at `0.24.2`, `automation/package-lock.json` pins its whole dependency tree, and `npm ci --prefix automation` installs it. `style_check.py` runs `automation/node_modules/.bin/markdownlint-cli2` and stops with a `SystemExit` naming the install command when it is missing, as it does for ruff. `.gitignore` gains `automation/node_modules/`. CI adds `actions/setup-node`, pinned by SHA, and `npm ci --prefix automation` to the `style` job.
- **Pros:** the lockfile pins every transitive version, as `requirements-dev.txt` pins ruff. It sits where §7 puts dev tooling. The version is read from one file.
- **Cons:** it adds two tracked files and a Node toolchain to development setup.

### Option B — `npx` with the version in `style_check.py`

- **Approach:** `style_check.py` runs `npx --yes markdownlint-cli2@0.24.2`, with the version in a constant.
- **Pros:** no new tracked files.
- **Cons:** markdownlint itself is pinned exactly by cli2, but its other dependencies are not, so two runs can resolve different trees. The first run downloads from the network, and every run after it depends on npx's cache. The version lives in code rather than in a dependency file.

**Recommendation:** Option A. It is the same model ruff follows: an exact, reproducible version in a dependency file, a clear failure when the tool is missing, and nothing fetched at check time.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | How is markdownlint-cli2 pinned and installed (§4 Options A and B)? The problem is real: the check needs Node 22 or later (F4), CI sets up no Node (F9), and the version must match the editor's (F3). Recommendation: Option A. | |
| Q2 | Is the rule set trimmed before the check is turned on, as the issue asks? The live findings (F5) and the archive's (F6) are all formatting defects the editor already flags, including `MD050` on unbackticked dunders. None clashes with a house rule, and the changed-line filter keeps existing findings from blocking. Recommendation: no trim; `.markdownlint.json` stays as it is. | |
| Q3 | Does the check also report a finding on a line next to a changed line? The problem is real: a paragraph added under an existing heading is reported on the heading's line and would pass (F8). Options: (a) keep only changed lines and document the miss; (b) also keep a markdownlint finding on the line directly before or after a changed line, at the cost of sometimes reporting an existing finding next to an edit; (c) check the whole of every touched file, which fails a branch that edits any of the 7 files in F5. Recommendation: (b). The finding it adds is one line, fixed in the file the branch is already editing. | |
| Q4 | Issue AC1's check names "fixture files", and the existing tests write Markdown inline (F11). Do the new tests follow the existing inline form, with the spec restating AC1 in its §5 under §1.2? Recommendation: yes, follow the harness and restate AC1. | |

## 6. Disposition

- Promoted to:
- Superseded by:

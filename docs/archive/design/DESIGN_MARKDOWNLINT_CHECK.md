# markdownlint check on changed lines — Design Study

**Status:** Shipped

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
| F1 | The issue's claim holds: no check reads `.markdownlint.json`. `style_check.py` checks Markdown only for hard wrapping, its own rule. markdownlint has no rule for it: `MD013`, which `.markdownlint.json` turns off, is the maximum line length, so turning it off is what lets a paragraph sit on one long line. | `automation/style_check.py:289` `markdown_violations`; `.markdownlint.json:3` `"MD013": false`; F2 search |
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
| F13 | `.markdownlint.json` does not show what it checks. `"default": true` turns on every rule of the installed markdownlint, 53 in 0.42.2, and the file names only the 4 it changes; a version bump adds rules with no change to the file. The one-line-per-paragraph rule is Python in `style_check.py`, which no config file shows and the editor does not flag. | `.markdownlint.json:2`; `node_modules/markdownlint/lib/md*.mjs` `names`, 0.42.2 |
| F14 | `markdownlint-rule-single-line-paragraphs` 0.2.0 is a markdownlint custom rule, `single-line-paragraphs`, that reports a prose paragraph spread over more than one source line: on its first line and on every continuation line. It applies to paragraphs at the root and in lists and quotes; it allows an explicit break (trailing `\`, two trailing spaces, `<br>`); it skips headings, code, tables, HTML, front matter and definitions. MIT, no dependencies, peer `markdownlint >=0.41.1`, one maintainer, published 20261007. Over the live Markdown it finds the same two real wraps `markdown_violations` finds: `automation/fixtures/standards_missing_label_pair.md:5-6` and `config/providers/_template/models/README.md:3-4`. | `npm view markdownlint-rule-single-line-paragraphs`; its `README.md`; measurement, §2 |
| F15 | It also reports every artifact header block, 47 of its 51 live findings: the three `docs/dev/*/_TEMPLATE_*.md` and the 14 `automation/fixtures/closeout_*` files. Consecutive `**Field:** value` lines are one Markdown paragraph, and GitHub renders them as one run-on line; `markdown_violations` exempts them by pattern (`_BLOCK_START`), and the package has no exemption setting. The same headers with a blank line between fields report nothing. | measurement, §2; `automation/style_check.py:48` `_BLOCK_START` |
| F16 | Every reader of a header field reads one line: `automation/closeout_acs.py:42` `_SPEC_BRANCH_FIELD_RE` (`^\*\*Branch:\*\*\s*` + backtick, `re.MULTILINE`), and the `^\*\*Originating item:\*\*`, `^\*\*Spec:\*\*` and `**Status:**` reads in `.claude/skills/session-start/references/spanner.md` read 4, `caliper.md` and `.claude/skills/closeout/`. A blank line between fields changes none of them. A trailing `\` would end every field value with `\`. | `git grep` of the field names over `automation/*.py`, `.claude/`, `.githooks/` |
| F17 | A custom rule needs a `.markdownlint-cli2.jsonc` (`customRules`); `.markdownlint.json` cannot load one. Named by package, the rule is found next to the markdownlint-cli2 that runs it, so the CLI finds it from a worktree with no `node_modules` of its own. The editor bundles its own markdownlint-cli2, so it needs `"modulePaths": ["automation/node_modules"]`; a missing path there is not an error. That the editor loads the rule this way is from the extension's documentation, not run. | scratch runs, §2; extension `readme.md` § Configure, `modulePaths` |
| F18 | A `.markdownlint-cli2.jsonc` with `"default": false` and 48 rules named, the 53 less `MD013`, `MD033`, `MD041` (off today) and `MD043`, `MD044` (each checks nothing without settings the repository does not give), reproduces exactly the 96 findings of F5, line for line. | measurement, §2: `diff` of the two outputs is empty |
| F12 | `automation/` tests are a separate suite, reached by `pytest automation/`; CI's bare `pytest` collects `tests/` only, by design. AC1's check is therefore a local `pytest automation/style_check_test.py` run, not a CI log. | `pyproject.toml:2` `testpaths = ["tests"]`; `docs/standards/6-testing.md:5` |

## 4. Governing rules and options

**Governing rules.**

- `docs/ARCHITECTURE.md` § 2 names no owner for process tooling. §7 places it in `automation/`, and `automation/style_check.py` owns checking a branch's changed lines (F7).
- §1.5: `.markdownlint.json` governs all Markdown formatting.
- §1.5 "A change to a rule searches the whole document set": F2 has the rule's one statement, and the §2 search names every caller of the check.
- Issue #297's design, archived in `docs/archive/design/DESIGN_CI_WORKFLOW.md`: code is brought up to the rules as it is touched, not all at once (F5 shows why).

**Engine.** markdownlint-cli2 is the only valid option. It is the engine the editor runs (F3) and reads `.markdownlint.json` as written. A Python port such as `pymarkdownlnt` has a config format and rule set of its own, so it would disagree with the editor and break §1.5.

**The one-line-per-paragraph rule.** `markdownlint-rule-single-line-paragraphs` (F14), pinned beside markdownlint-cli2, in place of `markdown_violations`. Ray ruled out writing a custom rule while a package exists. The header form it requires is Q6.

**The config file.** `.markdownlint-cli2.jsonc` replaces `.markdownlint.json`, the only valid option: it is the file that can load the rule (F17), and it names every rule it enforces (Q5).

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
| Q1 | How is markdownlint-cli2 pinned and installed (§4 Options A and B)? The problem is real: the check needs Node 22 or later (F4), CI sets up no Node (F9), and the version must match the editor's (F3). Recommendation: Option A. | Q1 answered 20261125: Option A. |
| Q2 | Is the rule set trimmed before the check is turned on, as the issue asks? The live findings (F5) and the archive's (F6) are all formatting defects the editor already flags, including `MD050` on unbackticked dunders. None clashes with a house rule, and the changed-line filter keeps existing findings from blocking. Recommendation: no trim; `.markdownlint.json` stays as it is. | Q2 answered 20261125: no trim. Q5 then made the rule set explicit without dropping a rule. |
| Q3 | Does the check also report a finding on a line next to a changed line? The problem is real: a paragraph added under an existing heading is reported on the heading's line and would pass (F8). Options: (a) keep only changed lines and document the miss; (b) also keep a markdownlint finding on the line directly before or after a changed line, at the cost of sometimes reporting an existing finding next to an edit; (c) check the whole of every touched file, which fails a branch that edits any of the 7 files in F5. Recommendation: (b). The finding it adds is one line, fixed in the file the branch is already editing. | Q3 answered 20261125: (b). |
| Q4 | Issue AC1's check names "fixture files", and the existing tests write Markdown inline (F11). Do the new tests follow the existing inline form, with the spec restating AC1 in its §5 under §1.2? Recommendation: yes, follow the harness and restate AC1. | Q4 answered 20261125: yes. |
| Q5 | Does the config file show every rule the check enforces? The problem is real (F13): `.markdownlint.json` names 4 of the 53 rules it applies, and the hard-wrap rule is in none. Recommendation: `"default": false` with every enforced rule named, and the hard-wrap rule loaded as a rule of the same file (F14, F17). | Q5 answered 20261125: yes, an explicit rule list, and the package rather than a rule of our own. |
| Q6 | How are header fields written, now that the package reports consecutive field lines (F15)? Options: a blank line between fields, or a trailing `\` on each. Recommendation: blank lines; no reader of a field changes (F16), where `\` would end every value. | Q6 answered 20261125: blank lines. |

## 6. Disposition

- Promoted to: `../specs/MARKDOWNLINT_CHECK_SPEC.md`
- Superseded by: n/a

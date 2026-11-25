# markdownlint Check on Changed Lines — Implementation Results

**Status:** Active

**Author:** Spanner

**Date:** 20261125

**Spec:** `../specs/MARKDOWNLINT_CHECK_SPEC.md`

**Released as:** `n/a`

---

## 1. Summary

Complete. `automation/style_check.py` now runs markdownlint-cli2 0.24.2 against `.markdownlint-cli2.jsonc` on every Markdown line a branch changes, and on the line next to one. The config names every rule it enforces, with nothing on by default, and loads `markdownlint-rule-single-line-paragraphs` 0.2.0 in place of the module's own hard-wrap check, which is removed. The tools are pinned in `automation/package.json` and its lockfile. The CI `style` job installs Node and the tools. The templates and closeout fixtures use blank-line headers, and §1.5 names the config and the check. Three criteria wait on Ray or on the pull request: AC1.12, AC2.1 and AC3.1.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Blank-line header form, DR9: 30 blank lines inserted, no field text changed (`5a178c7`) | `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/design/_TEMPLATE_DESIGN.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, 14 `automation/fixtures/closeout_*` files | +0 |
| 2 | Pinned tools, config, check and tests, DR1–DR8 (`b36786b`) | `automation/package.json`, `automation/package-lock.json`, `.gitignore`, `.markdownlint-cli2.jsonc`, `.markdownlint.json` (deleted), `automation/style_check.py`, `automation/style_check_test.py` | −5, +9 |
| 3 | CI `style` job sets up Node 24 and runs `npm ci --prefix automation` (`463142e`) | `.github/workflows/tests.yml` | +0 |
| 4 | §1.5 names `.markdownlint-cli2.jsonc` and `automation/style_check.py` (`1cadaaf`) | `docs/standards/1-workflow.md` | +0 |
| 5 | This artifact | `docs/dev/results/MARKDOWNLINT_CHECK_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest automation/style_check_test.py`: `test_a_markdownlint_finding_on_a_changed_line_is_reported` passed |
| AC1.2 | Met | `test_a_markdownlint_finding_on_an_untouched_line_is_not_reported` passed |
| AC1.3 | Met | `test_a_markdownlint_finding_next_to_a_changed_line_is_reported` passed |
| AC1.4 | Met | `test_a_rule_the_config_does_not_name_is_not_reported` passed |
| AC1.5 | Met | `test_the_check_stops_when_markdownlint_cli2_is_not_installed` passed |
| AC1.6 | Met | `test_markdownlint_is_found_from_a_linked_worktree` passed; also §5, the after run, made from a linked worktree |
| AC1.7 | Met | `test_a_wrapped_line_added_to_an_existing_document_is_reported` and `test_a_wrapped_line_that_predates_the_branch_is_not_reported` passed |
| AC1.8 | Met | §5 AC1.8 run |
| AC1.9 | Met | §5 AC1.9 run: 44 files, every reported rule a key of `.markdownlint-cli2.jsonc` |
| AC1.10 | Met | `pytest automation/`: 142 passed, 0 failed, 0 skipped |
| AC1.11 | Met | §5 AC1.11 run: 17 files, `Summary: 0 issues in 0 files`; `pytest automation/` passed after Step 1, 138 passed |
| AC1.12 | **Not met** | `Awaiting Ray`: in VS Code, a paragraph wrapped across two lines and a fenced block with no language each show a warning, `single-line-paragraphs` and `MD040` |
| AC1.13 | Met | `test_a_markdownlint_cli2_that_fails_to_load_stops_the_check`: all three cases passed |
| AC2.1 | **Not met** | Awaiting the `style` job log on this branch's pull request, which `/closeout` opens |
| AC3.1 | **Not met** | `Awaiting Ray`: reads `docs/standards/1-workflow.md` §1.5 **Writing.**, first item, for `.markdownlint-cli2.jsonc` and `automation/style_check.py` |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | Step 2's replacement for `check`'s `Returns:` line ends "on or next to one (DR4), sorted by path and line". A spec ID in code is a process citation (§3) and is used only in the file that defines it (§1.5) | within approved meaning | "(DR4)" left out, and the line wrapped to the docstring's width. Meaning unchanged | Spanner, 20261125 |
| 2 | Step 2's replacement `Requires` line is longer than the module docstring's width | within approved meaning | Wrapped over two lines, text unchanged | Spanner, 20261125 |
| 3 | Step 2's quoted `touched` block follows the values loop with no blank line between them | within approved meaning | A blank line added before `def touched` | Spanner, 20261125 |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 2 | Findings parsed from stderr with one regular expression, `_LINT_FINDING`; the counts from stdout with `_LINT_FILES` and `_LINT_SUMMARY` | `markdownlint-cli2-formatter-json` | The spec's text form, with no second package or `outputFormatters` entry the editor would ignore (Decision Log, Caliper, first pass, option (c)) |
| 2 | 2 | The test repository's `.gitignore` names `automation/node_modules` without a trailing `/` | The trailing `/` the repository's own `.gitignore` uses | In a test repository the path is a symlink, which git does not treat as a directory, so a pattern ending `/` would leave it untracked rather than ignored, and `changed_lines` would collect it |
| 3 | 2 | `BASE["docs/guide.md"]` gains a last paragraph on one line, and the assertions on `docs/guide.md:6` move to `:8` | Keeping the base text and asserting the earlier wrap too | Without it, the blank line every test appends sits next to the base's wrapped paragraph, so DR4 reports that paragraph in tests about something else |
| 4 | 2 | `needs_markdownlint` also marks six real-value tests whose branches change a `.md` file | Giving those tests non-Markdown files | They now run markdownlint through `check`; changing their files would change what they test. Without the tool, the suite runs 126 passed and 16 skipped, none failed |
| 5 | 2 | AC1.13's stubs are bash scripts written to a `tmp_path` folder that stands in for the main working tree through a patched `_main_worktree` | A patched `subprocess.run` | A stub runs the real `subprocess` call and the real parsing, so the test reaches the code DR2 states |
| 6 | 2 | `MAIN` in the test module is found from the test file's own repository with `git rev-parse --path-format=absolute --git-common-dir` | `ROOT / "automation" / "node_modules"` | Caliper, first pass: from a linked worktree, `ROOT` has no `node_modules`, and the suite would skip |

## 5. Verification

- **Test suite:** `pytest automation/`: 142 passed, 0 failed, 0 skipped (baseline 138 passed, 0 failed, 0 skipped). Without the tools installed: 126 passed, 0 failed, 16 skipped. `tests/` is untouched by this work and is run at close-out.
- **Defect shown before the fix:** a fenced block with no language in a new `demo.md`, on a branch cut in a linked worktree:
  - at `origin/main` (`49dd166`), `python3 automation/style_check.py` printed `PASS`;
  - at this branch's `1cadaaf`, `python3 automation/style_check.py --base main` printed `demo.md:3 — MD040/fenced-code-language Fenced code blocks should have a language specified`, followed by its context, and `FAIL`.
- **AC1.8 run:** with this file written, `python3 automation/style_check.py` printed `chore/issue-308-markdownlint-check against main: 28 changed file(s), 0 violation(s)` and `PASS`. `git diff --name-only $(git merge-base HEAD main)` with `git ls-files --others --exclude-standard` listed the spec, the design study, the three templates and this file.
- **AC1.9 run:** `automation/node_modules/.bin/markdownlint-cli2` over the 44 tracked `.md` files outside `SKIPPED`. It reported `MD001` 2, `MD012` 1, `MD022` 1, `MD031` 12, `MD032` 1, `MD034` 1, `MD040` 6, `MD060` 72 and `single-line-paragraphs` 4, which is design study F5's 96 plus F14's two wraps. Every reported rule is a key of `.markdownlint-cli2.jsonc`.
- **AC1.11 run:** the same tool over the 17 files Step 1 changed printed `Linting: 17 files` and `Summary: 0 issues in 0 files`.
- **Live verification:** at close-out.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| `npm audit` | 5 low-severity advisories, all one transitive KaTeX advisory (GHSA-238p-pmpm-9mq7) under `markdownlint` 0.42.2, the same version the editor bundles. The only fix npm offers is markdownlint-cli2 0.16.0, a downgrade. KaTeX is installed but never loaded: `markdownlint/lib/micromark-parse.mjs:7` imports only the syntax extension `math`, and KaTeX is imported only by the extension's HTML renderer, `micromark-extension-math/lib/html.js:6`, which nothing loads | No issue, Ray 20261125 |
| Caliper findings | Three standards gaps and one existing defect, in the spec's Decision Log | Each is an issue only on Ray's word (§1.3) |
| Existing findings | The 96 findings of design study F5 and the two wraps of F14, in files this work did not touch | Fixed when a branch touches them (spec §1) |
| Editor reload | The editor reads `.markdownlint-cli2.jsonc` and loads the rule through `modulePaths` once `npm ci --prefix automation` has run in the main working tree | AC1.12 |

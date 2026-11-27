# Module-level tests into plain classes — Design Study

**Status:** Active

**Kind:** Design study

**Author:** Spanner

**Date:** 20261127

**Read at:** `5d9bed2`

**Originating item:** Issue #288

---

## 1. Purpose

Issue #288 asks for every test in `tests/` to be a method of a plain `Test<Topic>` class, as `docs/standards/6-testing.md` §6.2 requires. An outside contributor has already opened pull request #290 for it, without a spec. Ray ruled on 20261127 that the work runs on the full path: this study and a spec come first, the contributor's commit is the base of a new branch, and #290 is closed with a reference to the new pull request, which gives the contributor full credit. This study measures again, checks #290 against the issue and against `dev`, and settles the two questions the work depends on.

## 2. Scope of the read

- The 86 module-level tests the issue names, at `5d9bed2`, found by the issue's own AST command.
- Pull request #290: its one commit `402ec1a`, parented on `3fff87a`, and the five files it changes. It was compared against its parent and against `dev`, test by test, by AST.
- `workmain/ai/providers/ollama.py` `OllamaProvider.check_availability`, `generate`, and `workmain/ai/base_provider.py` `BaseProvider.test_connection`, for the three Ollama tests.
- `tests/test_ollama_provider.py`, which tests the same three paths.
- The checks that apply to the changed files: `automation/style_check.py` (ruff with `pyproject.toml` `[tool.ruff.lint]`, and its process-citation search), `.github/workflows/tests.yml`, and `.claude/skills/closeout/SKILL.md` P7.
- The §1.3 search by file for each of the nine files and `tests/test_ollama_provider.py`.
- Not read: the bodies of tests that stay where they are. Moving a test does not change what it does (F2).

## 3. Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F1 | Measured again at `5d9bed2`: 86 module-level tests, the same names in the same nine files as the issue lists (66, 6, 4, 4, 2, 1, 1, 1, 1). | The issue's AST command, run on `origin/dev` |
| F2 | #290 moves the 82 tests in the five non-command files into plain classes with no base class. An AST comparison of each test against its original at `3fff87a` shows names, arguments, decorators and bodies unchanged, apart from the added `self` and docstring re-indentation that nesting forces (equal after `inspect.cleandoc`). The module-level statements that are not tests are unchanged. | `402ec1a` against `3fff87a` |
| F3 | #290's classes: `TestProviderRegistry` (3), `TestBaseProvider` (4), `TestOllamaProvider` (7), `TestProviderConfiguration` (4), `TestProviderManager` (11), `TestProviderCli` (18), `TestProviderRouting` (19) in `tests/test_provider_foundation.py`, placed after the file's existing classes. `TestAIFoundation`, `TestLiveProviders`, `TestCliLogging` and `TestCompareProvidersOutput` are in the other four files. | `402ec1a` |
| F4 | At its parent, #290 collects the same count as the parent: 1707 and 1707. Its five files pass at its head: 133 passed, 0 failed, 5 skipped. The full suite was not run on it. | `pytest --collect-only -q`, in worktrees of `3fff87a` and `402ec1a` |
| F5 | #290 conflicts with `dev` in `tests/test_provider_foundation.py`, in two hunks (51 and 145 lines). `f6667a2` (#155) changed the bodies of 5 of the moved tests on `dev`: `test_claude_provider_reads_model_from_config`, `test_claude_provider_requires_model_in_config`, `test_gemini_provider_reads_model_from_config`, `test_gemini_provider_requires_model_in_config` and `test_provider_disabled_by_construction_failure_reports_reason`. Each adds `**_TEST_RATES` to a config. The conflict is in the deleted originals. The moved copies don't conflict, so a resolution that keeps #290's side silently keeps the old bodies. | `git merge-tree origin/dev 402ec1a`. AST comparison of `3fff87a` and `origin/dev` |
| F6 | The other four files have no change on `dev` since `3fff87a` to any test #290 moves. | AST comparison of `3fff87a` and `origin/dev` |
| F7 | `automation/style_check.py --base 3fff87a` on `402ec1a` exits 1 with 128 violations, all on moved lines: ANN201 (82), ANN001 (29), ANN202 (11), D205 (3) and D213 (3). Re-indenting a line makes it a changed line, and the check reads every changed line. The ANN202 findings are nested helper functions inside moved tests. `references/anvil.md` requires a style violation to be fixed before each commit, and `/closeout` P7 requires the check to exit 0. | `python3 automation/style_check.py --base 3fff87a` in a detached worktree of `402ec1a`; `automation/style_check.py` module docstring |
| F8 | The three Ollama tests are unchanged in #290. `test_ollama_provider_generate_raises_unavailable`, `test_ollama_provider_test_connection_returns_false` and `test_ollama_provider_check_availability_returns_unavailable` each build `OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})` and call the real `urllib.request.urlopen` through `check_availability`. They pass only while nothing on `localhost:11434` lists `mistral-7b:latest`. The issue's Problem section requires each one to set up the unavailability itself. No criterion checks it, and Ray's comment of 20261116 to the contributor said "move tests without changing what they do". | `tests/test_provider_foundation.py:124`, `:137`, `:156`; `workmain/ai/providers/ollama.py` `check_availability` |
| F9 | `tests/test_ollama_provider.py` already covers two of those paths with the unavailability set up: `TestCheckAvailability::test_check_availability_connection_refused` patches `urllib.request.urlopen` to raise `URLError`, and `TestGenerate::test_generate_provider_unavailable` patches it to list no models. No test there covers `test_connection`. The three tests stay. Deleting them would break the issue's second criterion, and `test_connection` has no other test. | `tests/test_ollama_provider.py` |
| F10 | #290 leaves the 4 tests in command test files and gives #208 and #209 as the reason. That is true of 3. `tests/test_cost_display.py::test_costs_usage_error_exits_2_on_stderr` is parametrized over the `meetings`, `notes`, `providers` and `reports` groups, so #208, #209, #211 and #212 each replace part of it. | `tests/test_cost_display.py:133` |
| F11 | #290 moves 11 command tests, in `tests/test_provider_foundation.py`, that #211 (the providers commands) will replace. They run `providers test`, `costs`, `set default` and `list` through `CliRunner`: `test_providers_test_known_provider_no_bad_parameter`, `test_providers_test_unknown_provider_bad_parameter`, `test_providers_costs_unknown_provider_bad_parameter`, the six `test_set_default_*` tests at `:690`–`:789`, `test_providers_list_prints_every_configured_report_type` and `test_set_default_repairs_entry_the_manager_would_refuse`. They are the same kind of test #290 leaves in the meetings and notes files. No other module-level test in the file reaches `workmain.cli`. | `tests/test_provider_foundation.py`; #211 body, "tests/test_provider_foundation.py runs providers list (1), test (7) and set default (7)" |
| F12 | No branch exists for #208, #209, #211, #287 or #292, so no work in progress edits these files. | `git branch -a` |
| F13 | The §1.3 search by file returns no `parked` issue. #292 states the three Ollama tests are #288's. It also owns `tests/test_ai_providers_live.py` and may move that file's tests out of the application suite. A class around them doesn't change that. #287 names `TestCompareProviders` in `tests/test_compare_providers.py`, a class this work doesn't touch. #124 and #173 name files here for other reasons. #211 and #280 name `tests/test_provider_foundation.py` and `tests/test_cost_display.py` as files their conversions replace tests in. | §1.3 search, run for all ten files |

## 4. Governing rules and options

**Governing rules.**

- `docs/standards/6-testing.md` §6.2: "A test is a method of a plain class, and it takes what it needs as arguments. Related tests share a `Test<Topic>` class." The same section: "Converting code to a new form replaces every test of it, in whichever file it is." And: "A test's result depends only on what it sets up… Anything it needs from … the network, it sets up itself."
- `docs/standards/3-code.md` §3.5, as `automation/style_check.py` checks it on every changed line (F7).
- `docs/standards/1-workflow.md` §1.2: each step leaves the suite green, and a criterion names a property with the command as its evidence.
- `docs/ARCHITECTURE.md` names no owner for test layout. The work adds no module, class or function to `workmain/`.

The Ollama tests need no option. The issue states the fix, and F9 rules out deleting them: each one patches `urllib.request.urlopen` to fail, as `tests/test_ollama_provider.py` already does. The annotations need no option either: F7's rules require them in the commit that moves the lines.

### Q1 — tests a command-group issue under #198 will replace

There are 15: the 4 in command test files (F10) and the 11 providers command tests (F11). #290's split, moving the 11 and leaving the 4, is ruled out. It treats one kind of test two ways, and no rule separates them.

### Option A — move all 15

- **Approach:** every module-level test becomes a method of a plain class. The 4 tests in command files join a `Test<Topic>` class in their own file.
- **Pros:** §6.2's rule holds for the whole suite now. The issue's first criterion has no exception list, so its command prints nothing. The move is proven by AST, so it costs the command-group issues nothing: each replaces its tests wherever they sit. No branch edits those files (F12).
- **Cons:** it touches four more files that #208, #209, #211 and #212 will rewrite.

### Option B — leave all 15

- **Approach:** the 11 providers command tests move back to module level from #290's commit. The spec names all 15 as exceptions to the first criterion.
- **Pros:** the files the command-group issues will rewrite are left alone.
- **Cons:** it undoes part of the contributor's commit. The exception list stays true only until each issue ships, and for `test_costs_usage_error_exits_2_on_stderr` that means the last of four issues (F10). Until then, the suite breaks §6.2 in 15 places that no criterion checks.

**Recommendation:** Option A. §6.2's rule applies to every test now. Moving a test is proven not to change it, so leaving one for later buys nothing, and the exceptions would need tracking across four issues.

### Q2 — how the contributor's commit enters the branch

The commit for that step has to carry three things: #290's move, `f6667a2`'s 5 test bodies (F5), and the annotations F7 requires. Any of them missing means the suite or the style check fails at that commit.

### Option A — cherry-pick `402ec1a`, author kept

- **Approach:** `git cherry-pick 402ec1a` onto the branch. Resolve both hunks by taking #290's deletion, copy `f6667a2`'s 5 bodies into the moved methods, and add the annotations, all before the commit. The author stays the contributor. The commit body says what the resolution and the annotations added.
- **Pros:** git records the contributor as the author of the move.
- **Cons:** the commit authored under their name also holds lines they didn't write. The body is the only record of which lines those are.

### Option B — our commit, contributor as co-author

- **Approach:** the same tree as Option A, committed by the implementing role with a `Co-Authored-By:` trailer naming the contributor as `402ec1a` records them.
- **Pros:** the author field is accurate, and GitHub shows the contributor as co-author on the commit and the pull request.
- **Cons:** git doesn't record the contributor as the commit's author.

**Recommendation:** Option A. The move and its grouping are the contributor's work, and the conflict resolution is what a rebase of their branch would have done. The body records the rest.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Fifteen module-level tests are command tests that #208, #209, #211 or #212 will replace (F10, F11). #290 moves 11 of them and leaves 4. Does #288 move all 15 (Option A) or leave all 15 for those issues (Option B)? | |
| Q2 | The commit that brings #290's move onto the branch also carries `f6667a2`'s 5 test bodies and 128 annotation fixes the contributor didn't write (F5, F7). Is the contributor its author (Option A) or its co-author (Option B)? | |

## 6. Disposition

- Promoted to:
- Superseded by:

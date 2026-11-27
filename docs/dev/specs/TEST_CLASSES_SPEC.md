# Module-level tests into plain classes — Spec

**Status:** Approved

**Author:** Spanner

**Date:** 20261127

**Read at:** `043e8c5`

**Branch:** `feature/issue-288-test-classes` (base: `dev`, `docs/standards/2-git.md` §2.1)

**Target release:** set by `/closeout`

**Originating item:** Issue #288

**Design study:** `../design/DESIGN_TEST_CLASSES.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261127 | Ray | Branch type `feature/*`, on the full path. Pull request #290 was opened by an outside contributor without a spec. Its commit `402ec1a` is the first commit of this branch's work, cherry-picked onto `dev`, and the contributor gets full credit. #290 is closed with a reference to this branch's pull request. | Adopted; header, Step 1, Close-out. |
| 20261127 | Ray | Design study Q1: Option A. All 15 module-level command tests move, including the 11 providers command tests #290 already moved and the 4 in command test files it left. | Adopted; DR1, Step 2, AC1.1. |
| 20261127 | Ray | Design study Q2: Option A. `402ec1a` is cherry-picked with its author kept. The same commit carries `f6667a2`'s five test bodies and the annotations the style check requires, and its body says which lines those are. | Adopted; Step 1. |
| 20261127 | Ray | The issue gains a criterion: the three Ollama unavailability tests pass whatever listens on `localhost:11434`. | Adopted; DR4, Step 3, AC4.1. The issue has no criterion for it, so per `docs/standards/1-workflow.md` §1.2, §5 states it as AC4.1 and the issue body gains it as a fourth criterion at close-out. |
| 20261127 | Ray | Every line a step changes, re-indented lines included, passes `automation/style_check.py` in that step's commit. No violation is left for a later issue. | Adopted; §4 opening. |
| 20261127 | Caliper | 2, Spec defect, blocking: DR4 says how the three Ollama tests set up the failure is "below the contract". DR2 lets these three tests change what they check, and AC2.2 leaves them out of its comparison. That makes the easiest route to green a valid build: patch `OllamaProvider.check_availability`, or `BaseProvider.test_connection`, to return `UNAVAILABLE`. Nothing reaches the network, the assertions don't change, and the AC4.1 command reports `3 passed`. But `test_ollama_provider_check_availability_returns_unavailable` would then only check the patch's return value, and the `generate` and `test_connection` tests would stop running the `except Exception` branch at `workmain/ai/providers/ollama.py:50`. The design study already chose the seam: §4 says "each one patches `urllib.request.urlopen` to fail, as `tests/test_ollama_provider.py` already does". `ollama.py:43` reads `urllib.request.urlopen` when the call runs, so that patch works. Fix: DR4 names `urllib.request.urlopen` as the point where the failure is set up, so each test still runs `OllamaProvider.check_availability`. AC4.1 then states that property (`SKILL.md` § Role 3, last paragraph; `docs/standards/1-workflow.md` §1.2). | Accepted, verified at `workmain/ai/providers/ollama.py:43` and `:50`–`:51`. DR4 states the property: each test runs `OllamaProvider.check_availability` itself, and the request it makes through `urllib.request.urlopen` raises, so its `except Exception` branch returns `UNAVAILABLE`. AC4.1's command now traces each test and prints `NO FAILED REQUEST` for any test in which that branch did not run. Tried in a scratch worktree on three builds of Step 3. Patching `urlopen` to raise: `3 passed`, no line printed. Patching it to return an empty model list: `3 passed` and 3 lines. Patching `check_availability`: `3 passed` and 3 lines. At `38aaea1`: `3 failed` and 3 lines. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: DR2 and the §4 opening allow a moved docstring only "the docstring layout the check requires, and nothing more". The AC2.2 command deletes each docstring before comparing (`Norm._fn`), so a reworded docstring passes. Either AC2.2 compares the docstrings after `inspect.cleandoc` and whitespace normalization, or the spec says docstring wording is unchecked. | Accepted, first option. AC2.2 compares each docstring with its whitespace collapsed. There is one exception: the four docstrings whose summary is a sentence that continues onto the next line. They are `test_cli_python_warning_is_a_log_record_and_nothing_to_stderr`, `test_t12_note_persists_when_the_time_entry_prompt_is_cancelled`, `test_application_functions_entry_non_positive_int_raises_naming_it` and `test_call_type_in_both_blocks_raises_naming_it`. Each first line ends mid-sentence, so D205 and D213 can't be met by layout alone. DR2 lets those four be reworded into a one-line summary and a description, and AC2.2 doesn't compare their docstrings. Found by listing every multi-line docstring among the 86 tests at `origin/dev`. Tried in memory: a layout-only change compares equal, and a reworded docstring compares unequal. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: the annotations ANN001 requires need imports that DR2 and the §4 opening don't mention. Without them the step would add lines the spec doesn't name. At `origin/dev`, `tests/test_meetings_merge.py:32` and `tests/test_meetings_reschedule.py:20` take an unannotated `db_session`, and neither file imports `Session`. The §4 opening should say an import an annotation needs is part of that change. | Accepted, verified at both lines. The §4 opening now includes an import an annotation needs. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: Decision Log row 1 says "`402ec1a` is the base of this branch". In fact the branch comes from `dev` `5d9bed2`, and Step 1 cherry-picks `402ec1a` onto it. AC1.2, AC2.1 and AC2.2 say "the branch's base", and their commands mean `git merge-base origin/dev HEAD`. The row should say "the first commit of this branch's work", so nobody compares against `402ec1a`. | Accepted. Row 1 says that now. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: §7 Rollback says "Reverting Step 1 also removes the contributor's commit from the branch". `git revert` doesn't remove a commit; it adds a commit that undoes it. Reverting Step 1 while Step 3 sits on top also conflicts in the three Ollama tests. Step 3 should be reverted first. | Accepted. §7 now says steps are reverted newest first, and that a revert adds a commit. |
| 20261127 | Caliper | 1, Spec defect, non-blocking: two §2 rows rest on the design study and are not marked as carried in, which `_TEMPLATE_SPEC.md` §2 asks for. They are the row with 128 violations (F7) and the row with the 11 providers command tests (F11). This pass re-checked both and both hold. | Accepted. Both rows are marked as carried in from the design study, re-checked by this pass. |
| 20261127 | Caliper | Existing defect, non-blocking: line 2 of the module docstring in `tests/test_provider_foundation.py` reads "Provider Foundation Sprint", a process citation `docs/standards/3-code.md` §3 forbids. No step changes that line, so the style check doesn't flag it. | Verified at `tests/test_provider_foundation.py:2`. Reported to Ray in one line. Ray, 20261127: resolved in this issue. Verified that the rest of the docstring also describes history: "base_provider.py's additions" and "the OllamaProvider ABC-compliant stub". `docs/standards/3-code.md` §3 requires a docstring to describe the code as it is, so the whole docstring is rewritten, not just the one word. DR5, Step 4, AC5.1. The issue has no criterion for it, so AC5.1 is added to the issue body as a fifth criterion at close-out (`docs/standards/1-workflow.md` §1.2). |
| 20261127 | Caliper | Pass at `38aaea1`, full: 25 items checked, 1 blocking, 6 non-blocking. | n/a |
| 20261127 | Ray | The process citation in the module docstring of `tests/test_provider_foundation.py`, which Caliper reported as an existing defect, is resolved in this issue. | Adopted; §1, DR5, Step 4, AC5.1. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: AC5.1 checks less than DR5 requires. DR5, and the resolution of Decision Log row 36, require the whole module docstring to describe the file as it is. That means removing the "Sprint" citation and also the history in "base_provider.py's additions" and "the OllamaProvider ABC-compliant stub". AC5.1 only names citations, and its grep only matches the `_HISTORY` forms. Deleting the one word "Sprint " therefore turns AC5.1 green while the history stays (`SKILL.md` § Role 3, last paragraph; `docs/standards/1-workflow.md` §1.2). AC5.1 is also scoped to the whole file, and says it "cites no … backlog item". After the work the file still has its `Issue #N` comments (`tests/test_provider_foundation.py:226`, `:306`, `:822`, `:877`, `:1037` and others at `HEAD`), and §1 puts those out of scope. Read as written, the property is false even when the command passes. Fix: AC5.1's property becomes DR5's: the module docstring describes the file as it is, with no process citation. It is checked by the grep, run over the module docstring only, plus a Ray reading of that docstring for history, in the §1.2 sign-off form. | Accepted, verified: the `Issue #N` comments are at the lines cited. AC5.1's property is now DR5's. Its command searches the module docstring alone with the `_HISTORY` pattern, and prints line 2 at `3db3cdf`. A stated reading by Ray covers the history. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: AC5.1's grep sits in a table cell, so its alternations are written `\|`. Copied from the raw file, `grep -nE '…\|…'` treats `\|` as a literal pipe. Run at `3db3cdf`, the raw form prints nothing and exits 1, while the form without escapes prints line 2. The row says "It prints line 2 at the **Read at:** commit", which holds only once the escapes are removed. As written, the command passes before any change is made. Fix: move the command into a fenced block below the table, as the AC1.1, AC2.1 and AC2.2 commands already are. AC2.1's `pytest --collect-only -q \| tail -1` has the same form, unchanged since `38aaea1`, but there pytest errors on the `\|` argument instead of passing silently. | Accepted. Both commands are now in fenced blocks: AC5.1's as its own block, and AC2.1's count as two lines in the AC2.1 block. Neither table cell holds an escaped pipe. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: DR2 lets four docstrings be reworded, provided each "says what it said before". Their names are in §2 and are confirmed by AST at `origin/dev`: exactly these four multi-line test docstrings have a summary sentence that continues onto the next line. AC2.2 leaves those four out of its docstring comparison, and no other criterion checks that a rewording keeps its meaning. Fix: AC2.2, or a new criterion, names a Ray reading of the four reworded docstrings against their versions at the branch's base. Alternatively the spec states that this property is not checked. | Accepted, first option. AC2.3 is a stated reading by Ray of the four docstrings against their versions at the branch's base. It maps to the issue's second criterion, which says no test is lost or changed by the move. |
| 20261127 | Caliper | Pass at `3db3cdf`, changes since `38aaea1`: 24 items checked, 0 blocking, 3 non-blocking. | n/a |
| 20261127 | Ray | Spec approved. `git diff 3db3cdf` on the spec, run before the status edit, shows only Decision Log rows and the resolutions of the pass's three non-blocking findings (`docs/standards/1-workflow.md` §1.1 Approval). | Adopted; **Status:** `Approved`. |
| 20261127 | Anvil | §2's row for `tests/test_cost_display.py::test_costs_usage_error_exits_2_on_stderr` cites `tests/test_cost_display.py:133`. The `parametrize` decorator is on line 134 and the `def` on line 135, at the **Read at:** commit too. What the row states is true. | Accepted, verified at `5d9bed2`: line 133 is blank. The row's evidence reads `tests/test_cost_display.py:134`. Recorded here and not edited in §2, because §2 is outside what an `Approved` spec may change (`docs/standards/1-workflow.md` §1.1 Approval). No step, design rule or criterion depends on the line. Design study F10 is corrected in place. |

---

## 1. Scope

**In scope:**

- The 86 module-level tests at the **Read at:** commit (§2), in `tests/test_provider_foundation.py` (66), `tests/test_ai_foundation.py` (6), `tests/test_ai_providers_live.py` (4), `tests/test_cli_logging.py` (4), `tests/test_compare_providers.py` (2), `tests/test_cost_display.py` (1), `tests/test_meetings_merge.py` (1), `tests/test_meetings_reschedule.py` (1) and `tests/test_notes_add.py` (1). Each becomes a method of a plain class in its own file (Steps 1 and 2).
- What `automation/style_check.py` requires of each line those moves change (§4 opening).
- How `test_ollama_provider_generate_raises_unavailable`, `test_ollama_provider_test_connection_returns_false` and `test_ollama_provider_check_availability_returns_unavailable` in `tests/test_provider_foundation.py` get the unavailability they test (Step 3).
- The module docstring of `tests/test_provider_foundation.py` (Step 4).

**Out of scope:**

- What any other test checks (DR2).
- The 60 tests in `unittest.TestCase` classes: the command-group issues under #198 convert them.
- The duplicate coverage of `check_availability` and `generate` in `tests/test_ollama_provider.py` (design study F9). Both files keep their tests.
- Whether the live tests in `tests/test_ai_providers_live.py` leave the application suite: #292.
- `usefixtures('offline_provider_env')` on `TestCompareProviders` in `tests/test_compare_providers.py`: #287.
- AC, DR, T-number and issue-number tags in moved docstrings and comments. `docs/standards/3-code.md` §3 does not list them, and the style check does not flag them (design study §3, standards gap reported to Ray).
- Any other module docstring, and any process citation in another file.
- Any file outside `tests/`, other than this set's documents.

## 2. Verified current state

At `043e8c5`, whose `tests/` is `origin/dev` `5d9bed2`'s, 20261127.

| Claim | Evidence |
| --- | --- |
| The issue's AST command prints 86 lines: the 86 tests §1 lists, by file. | The AC1.1 command in §5 |
| Pull request #290 is one commit, `402ec1a`, authored by its contributor and parented on `3fff87a`. It changes only `tests/test_provider_foundation.py`, `tests/test_ai_foundation.py`, `tests/test_ai_providers_live.py`, `tests/test_cli_logging.py` and `tests/test_compare_providers.py`. Its subject, `Move module-level tests into topic classes`, has no `<type>(<scope>):` prefix, so `.githooks/commit-msg` would refuse it as a commit on this branch. | `git log -1 --format='%an%n%s%n%P' 402ec1a`; `git diff --stat 3fff87a 402ec1a`; `docs/standards/2-git.md` §2.4 |
| In those five files, `402ec1a` moves all 82 module-level tests into plain classes: 7 in `tests/test_provider_foundation.py` and one in each of the others (design study F3). Measured against `3fff87a`, the AC2.2 command prints only the 4 tests `402ec1a` leaves, in the other four files, as `MISSING`. | The AC2.2 command, run as `python3 - 3fff87a 402ec1a` |
| Measured against this branch's base, the same command also prints `CHANGED` for 5 tests whose bodies `f6667a2` (#155) changed on `dev` after `3fff87a`: `test_claude_provider_reads_model_from_config`, `test_claude_provider_requires_model_in_config`, `test_gemini_provider_reads_model_from_config`, `test_gemini_provider_requires_model_in_config` and `test_provider_disabled_by_construction_failure_reports_reason`. | The AC2.2 command, run as `python3 - origin/dev 402ec1a` |
| `git cherry-pick 402ec1a` onto `5d9bed2` conflicts in `tests/test_provider_foundation.py` in two hunks, both where `402ec1a` deletes an original that `f6667a2` changed. The moved copies do not conflict. | `git merge-tree --write-tree origin/dev 402ec1a` |
| `automation/style_check.py --base 3fff87a` on `402ec1a` reports 128 violations on re-indented lines: ANN201 (82), ANN001 (29), ANN202 (11), D205 (3), D213 (3). `pyproject.toml` ignores D101–D103 under `tests/**`, so a new class needs no docstring. | Carried in from design study F7, and re-checked by Caliper at `38aaea1`; `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` |
| Of the 86 tests, four have a docstring whose summary is a sentence that continues onto the next line: `test_cli_python_warning_is_a_log_record_and_nothing_to_stderr`, `test_t12_note_persists_when_the_time_entry_prompt_is_cancelled`, `test_application_functions_entry_non_positive_int_raises_naming_it` and `test_call_type_in_both_blocks_raises_naming_it`. Moving lines around can't give them a one-line summary that D205 and D213 accept. | Every multi-line docstring among the 86 at `origin/dev`, listed by AST |
| `tests/test_meetings_merge.py:32` and `tests/test_meetings_reschedule.py:20` take an unannotated `db_session`, and neither file imports `Session`. | Source |
| 11 of the 66 tests in `tests/test_provider_foundation.py` are providers command tests run through `CliRunner`, which #211 will replace. No other module-level test there reaches `workmain.cli`. | Carried in from design study F11, and re-checked by Caliper at `38aaea1` |
| `tests/test_cost_display.py::test_costs_usage_error_exits_2_on_stderr` is parametrized over `meetings`, `notes`, `providers` and `reports`. | `tests/test_cost_display.py:133` |
| The three Ollama tests each build `OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})` and reach the real `urllib.request.urlopen` through `OllamaProvider.check_availability`. `generate` calls `check_availability` first, and `BaseProvider.test_connection` returns whether it is `AVAILABLE`. `check_availability` returns `UNAVAILABLE` on any exception. | `tests/test_provider_foundation.py:124`, `:137`, `:156`; `workmain/ai/providers/ollama.py` `check_availability`, `generate`; `workmain/ai/base_provider.py` `test_connection` |
| With a server on `127.0.0.1:11434` answering `GET /api/tags` with `mistral-7b:latest` and `POST /api/generate` with a complete reply, all three tests fail. With nothing listening, all three pass. Without the `POST` handler, the `generate` test passes for the wrong reason: the 501 is a `URLError`, which `generate` turns into `ProviderUnavailableError` (`workmain/ai/providers/ollama.py:116`). | The AC4.1 command in §5, run at `043e8c5` |
| `check_availability` makes its request with `urllib.request.urlopen`, looked up when the call runs. Its `except Exception` branch returns `UNAVAILABLE`. A patch of `check_availability` or `test_connection` skips that branch. So does a patched `urlopen` that returns an empty model list: it returns `UNAVAILABLE` at `:49` instead. | `workmain/ai/providers/ollama.py:43`, `:49`, `:50`–`:51`; the Decision Log's AC4.1 trials |
| The collected test IDs, with the class part removed, are identical at `3fff87a` and at `402ec1a`. There are 1707 at each. | The AC2.1 command in §5, run with `3fff87a` as its base and `402ec1a` as the branch |
| The module docstring of `tests/test_provider_foundation.py` opens "Tests for the Provider Foundation Sprint deliverables", which matches the style check's process-citation pattern (`\bSprint\b`). It also describes "base_provider.py's additions" and "the OllamaProvider ABC-compliant stub", which is history. It is the file's only match for the pattern, and `402ec1a` doesn't change it. | `tests/test_provider_foundation.py:1`–`:9`; `automation/style_check.py` `_HISTORY` |
| Suite at `043e8c5`: `1862 passed, 0 failed, 0 skipped`, with 1 xfailed and 3 xpassed, from a bare `pytest` with `.env`'s provider keys set. `pytest --collect-only -q` collects 1866. | Run 20261127 |

## 3. Design rules

- **DR1 — Every test in `tests/` is a method of a plain class.** The class has no base class and no keyword in its `class` statement. Each class is named `Test<Topic>` (`docs/standards/6-testing.md` §6.2). Each test stays in the file it is in.
- **DR2 — No moved test changes what it checks,** except the three Ollama tests (DR4). Each moved test has the same name, decorators and body as at the branch's base. Its arguments are the same after `self`. The only changes are those the §4 opening allows. Each docstring keeps its words, apart from whitespace, except the four §2 names whose summary sentence continues onto the next line. Each of those four is reworded into the one-line summary and description that D205 and D213 require, and says what it said before.
- **DR3 — The 82 tests `402ec1a` moves stay in the classes `402ec1a` puts them in,** under the names it gives those classes (design study F3). That grouping is the contributor's work, adopted with the commit (Decision Log, Q2).
- **DR4 — Each of the three Ollama tests runs `OllamaProvider.check_availability` itself, and the request it makes through `urllib.request.urlopen` raises,** so its `except Exception` branch returns `UNAVAILABLE` (`workmain/ai/providers/ollama.py:43`, `:50`). That is the unreachable host each test's docstring names. The test sets this up in its own body. It reaches no network address, and its result is the same whatever listens on `localhost:11434`. What each test asserts is unchanged. A patch of `check_availability`, `test_connection` or anything else between the test and `urlopen` does not meet this rule. How the patch is written is below the contract.

- **DR5 — The module docstring of `tests/test_provider_foundation.py` describes what the file tests as it is,** with no citation of the process that produced it (`docs/standards/3-code.md` §3, §3.1). Its wording is below the contract.

Anything this spec does not decide is a departure: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Every line a step changes passes `python3 automation/style_check.py` in that step's commit, and a re-indented line counts as changed. That is the one change a moved line may get beyond its indentation: what the check requires, and nothing more. That means the annotations, any import an annotation needs, and the docstring changes DR2 allows.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `402ec1a` on the branch, carrying `dev`'s test bodies and the style check's annotations | `tests/test_provider_foundation.py`, `tests/test_ai_foundation.py`, `tests/test_ai_providers_live.py`, `tests/test_cli_logging.py`, `tests/test_compare_providers.py` |
| 2 | The four tests in command test files move into plain classes | `tests/test_cost_display.py`, `tests/test_meetings_merge.py`, `tests/test_meetings_reschedule.py`, `tests/test_notes_add.py` |
| 3 | The three Ollama tests set up the unavailability themselves | `tests/test_provider_foundation.py` |
| 4 | The module docstring of `tests/test_provider_foundation.py` describes the file as it is | `tests/test_provider_foundation.py` |
| 5 | Results artifact | `docs/dev/results/TEST_CLASSES_RESULTS.md` |

### Step 1 — the contributor's move

`git fetch origin pull/290/head`, then `git cherry-pick 402ec1a`. Resolve the two conflict hunks by keeping `402ec1a`'s deletion of the originals. Then, before the commit:

- Each of the 5 moved tests §2 names gets the body it has on this branch's base. This is the change `f6667a2` made to the original, which the conflict does not carry.
- Every line the style check flags gets what it requires (§4 opening).

The commit keeps `402ec1a`'s author. Its subject is reworded to the `docs/standards/2-git.md` §2.4 form, and its body keeps `402ec1a`'s `Signed-off-by:` line. The body states that the move and the class grouping are the author's, cites `402ec1a` and #290, and lists what the commit adds beyond `402ec1a`: the five bodies from `f6667a2`, and the style check's changes under the §4 opening: annotations, the imports they need, and docstrings.

The AC2.2 command prints only the 4 tests Step 2 moves, each as `MISSING`.

### Step 2 — the four command-file tests

Under DR1 and DR2, each of `test_costs_usage_error_exits_2_on_stderr` (`tests/test_cost_display.py`), `test_merge_keeps_moved_notes_when_the_delete_prompt_is_cancelled` (`tests/test_meetings_merge.py`), `test_reschedule_keeps_the_approved_updates_when_a_later_prompt_is_cancelled` (`tests/test_meetings_reschedule.py`) and `test_t12_note_persists_when_the_time_entry_prompt_is_cancelled` (`tests/test_notes_add.py`) becomes a method of a plain class in its own file. Whether it joins an existing plain class there or a new one, and the class's name, are below the contract. It does not join a `unittest.TestCase` class, because DR1 requires a plain one.

The AC1.1 and AC2.2 commands print nothing.

### Step 3 — the Ollama tests

Under DR4, for `test_ollama_provider_generate_raises_unavailable`, `test_ollama_provider_test_connection_returns_false` and `test_ollama_provider_check_availability_returns_unavailable`, in the class Step 1 puts them in.

This is the defect fix, so the step runs the AC4.1 command twice. Before the change it reports 3 failed and 3 `NO FAILED REQUEST` lines. After it, it reports 3 passed and no such line (`.claude/skills/session-start/references/anvil.md` § Working rules). The commit body records both runs.

### Step 4 — the module docstring

Under DR5. No other line of the file changes. The AC5.1 command prints nothing.

### Step 5 — results artifact

`docs/dev/results/TEST_CLASSES_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. Under "Defect shown before the fix" it records Step 3's two AC4.1 runs. It also records the AC1.1 command's two runs: 86 lines before Step 1, and nothing after Step 2. AC2.3, and AC5.1's reading, are recorded `Not met` with `Awaiting Ray` as evidence (`docs/standards/1-workflow.md` §1.2).

### Close-out

`/closeout` opens this branch's pull request to `dev`. Then Ray edits that pull request's description to credit #290's author for the move. Ray closes #290 with a comment linking the new pull request. Neither is a step of this spec, and neither is an authorization point: closing a pull request deletes nothing (`docs/standards/1-workflow.md` §1.4).

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every test in `tests/` is defined in a class | The AC1.1 command below, the issue's own, printing nothing. It prints 86 lines at the **Read at:** commit. |
| AC1.2 | Every test that was module-level at the branch's base is a method of a plain class in the same file (DR1) | The AC2.2 command below printing no `NOT PLAIN` and no `MISSING` line |
| AC2.1 | No test is lost or added: the suite collects the same tests, by file, name and parameters, as the branch's base | The AC2.1 command below printing no diff line, and its two count lines, base then branch, matching (1866 at the **Read at:** commit) |
| AC2.2 | No moved test changes what it checks, apart from the three Ollama tests (DR2) | The AC2.2 command below printing no `CHANGED` line. It compares each moved test with its original at the branch's base, after removing `self` and annotations and collapsing whitespace in docstrings. It doesn't compare the docstrings of the four DR2 lets be reworded. It reports the 5 `f6667a2` bodies as `CHANGED` when run against `402ec1a` (§2), so it can catch a body the conflict lost. |
| AC2.3 | Each of the four docstrings DR2 lets be reworded says what it said at the branch's base | A stated reading by Ray of the four docstrings §2 names, each against its version at the branch's base (`git show "$(git merge-base origin/dev HEAD)":<file>`), for whether it states the same behaviour. Recorded as `docs/standards/1-workflow.md` §1.2 states for a sign-off. |
| AC3.1 | The full suite passes | A bare `pytest` reporting 0 failed, with the passed, skipped, xfailed and xpassed counts equal to the baseline in §2 when run with the same `.env` |
| AC4.1 | The three Ollama unavailability tests pass whatever listens on `localhost:11434`, and each passes because the request `OllamaProvider.check_availability` makes fails (DR4). The issue body gains this as its fourth criterion at close-out. | The AC4.1 command below reporting `3 passed` and printing no `NO FAILED REQUEST` line. It serves, on `127.0.0.1:11434`, a model list naming the tests' model and a complete reply, which makes all three fail at the **Read at:** commit (§2). While each test runs, it traces `check_availability` and prints `NO FAILED REQUEST` when the `except Exception` branch did not run. A bare `pytest` with nothing listening, AC3.1, covers the other case. |
| AC5.1 | The module docstring of `tests/test_provider_foundation.py` describes what the file tests as it is, with no citation of the process that produced it (DR5). The issue body gains this as its fifth criterion at close-out. | The AC5.1 command below printing nothing. It searches the module docstring alone with `automation/style_check.py` `_HISTORY`, the style check's citation pattern, and prints line 2 at the **Read at:** commit. Plus a stated reading by Ray of the module docstring, for whether it describes the file as it is and not how it came to be. Recorded as `docs/standards/1-workflow.md` §1.2 states for a sign-off. |

**AC1.1 command** (the issue's), run from the repository root:

```bash
python3 -c "import ast,pathlib; [print(f'{p}:{n.lineno} {n.name}') for p in sorted(pathlib.Path('tests').rglob('test_*.py')) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test')]"
```

**AC2.1 command**, run from the repository root. It collects the base in a temporary worktree, removes the class part of every test ID and diffs the two lists, then prints the base's count and the branch's:

```bash
collect() { (cd "$1" && pytest --collect-only -q -p no:cacheprovider 2>/dev/null | grep '::' | sed -E 's/::[A-Za-z_][A-Za-z0-9_]*::/::/' | sort); }
w=$(mktemp -d) && git worktree add --detach "$w" "$(git merge-base origin/dev HEAD)" >/dev/null 2>&1
diff <(collect "$w") <(collect .)
(cd "$w" && pytest --collect-only -q -p no:cacheprovider 2>/dev/null | tail -1); pytest --collect-only -q -p no:cacheprovider 2>/dev/null | tail -1
git worktree remove --force "$w"
```

**AC2.2 command**, run from the repository root as `python3 - "$(git merge-base origin/dev HEAD)" HEAD`. The two arguments are the revision whose module-level tests are read, and the revision whose classes are searched for them:

```python
import ast, subprocess, sys
base, head = sys.argv[1], sys.argv[2]
reworded = {"test_cli_python_warning_is_a_log_record_and_nothing_to_stderr", "test_t12_note_persists_when_the_time_entry_prompt_is_cancelled", "test_application_functions_entry_non_positive_int_raises_naming_it", "test_call_type_in_both_blocks_raises_naming_it"}
ollama = {"test_ollama_provider_generate_raises_unavailable", "test_ollama_provider_test_connection_returns_false", "test_ollama_provider_check_availability_returns_unavailable"}
def src(rev, p):
    r = subprocess.run(["git", "show", f"{rev}:{p}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""
class Norm(ast.NodeTransformer):
    def __init__(self, keep_doc): self.keep_doc = keep_doc
    def visit_arg(self, n): n.annotation = None; return n
    def _fn(self, n):
        n.returns = None
        if n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str):
            n.body[0].value.value = " ".join(n.body[0].value.value.split()) if self.keep_doc else ""
        self.generic_visit(n); return n
    visit_FunctionDef = visit_AsyncFunctionDef = _fn
def norm(fn, drop_self):
    fn = Norm(fn.name not in reworded).visit(ast.parse(ast.unparse(fn)).body[0])
    if drop_self: fn.args.args = fn.args.args[1:]
    fn.name = "_"
    return ast.dump(fn)
files = subprocess.run(["git", "ls-tree", "-r", "--name-only", base, "tests/"], capture_output=True, text=True).stdout.split()
for p in sorted(f for f in files if f.rsplit("/", 1)[-1].startswith("test_") and f.endswith(".py")):
    tests = {n.name: n for n in ast.parse(src(base, p)).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")}
    if not tests: continue
    found = {}
    for c in ast.parse(src(head, p) or "").body:
        if isinstance(c, ast.ClassDef):
            for m in c.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name in tests: found[m.name] = (c, m)
    for name, fn in tests.items():
        if name not in found: print(f"MISSING {p} {name}"); continue
        c, m = found[name]
        if c.bases or c.keywords: print(f"NOT PLAIN {p}::{c.name}::{name}")
        if name not in ollama and norm(fn, False) != norm(m, True): print(f"CHANGED {p}::{c.name}::{name}")
```

**AC4.1 command**, run from the repository root with port 11434 free:

```python
import ast, http.server, inspect, json, sys, textwrap, threading
import pytest
names = ["test_ollama_provider_generate_raises_unavailable", "test_ollama_provider_test_connection_returns_false", "test_ollama_provider_check_availability_returns_unavailable"]
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"models": [{"name": "mistral-7b:latest"}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = json.dumps({"response": "ok", "prompt_eval_count": 1, "eval_count": 1, "done_reason": "stop"}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
reached = {}
class Probe:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        from workmain.ai.providers.ollama import OllamaProvider
        code = OllamaProvider.check_availability.__code__
        lines, start = inspect.getsourcelines(OllamaProvider.check_availability)
        handler = next(h for h in ast.walk(ast.parse(textwrap.dedent("".join(lines)))) if isinstance(h, ast.ExceptHandler))
        target = start + handler.body[0].lineno - 1
        hit = []
        def line(frame, event, arg):
            if event == "line" and frame.f_lineno == target: hit.append(True)
            return line
        sys.settrace(lambda frame, event, arg: line if frame.f_code is code else None)
        try:
            yield
        finally:
            sys.settrace(None)
            reached[item.name] = bool(hit)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 11434), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
rc = pytest.main(["-q", "-p", "no:cacheprovider", "tests/test_provider_foundation.py", "-k", " or ".join(names)], plugins=[Probe()])
for n in names:
    if not reached.get(n): print(f"NO FAILED REQUEST {n}: check_availability's except branch did not run")
sys.exit(rc)
```

Run as `python3 - <<'EOF'` with the block above, then `EOF`.

**AC5.1 command**, run from the repository root:

```bash
python3 -c "import ast, re; d = ast.get_docstring(ast.parse(open('tests/test_provider_foundation.py').read()), clean=False) or ''; [print(l) for l in d.splitlines() if re.search(r'\bGate \d+[A-Z]?\b|\bPhase \d+\b|_Sprint\b|\bSprint\b|\bItem #?\d+\b|\bOQ\d+\b', l)]"
```

## 6. Test plan

- **Baseline before this work:** `1862 passed, 0 failed, 0 skipped`, with 1 xfailed and 3 xpassed, from a bare `pytest` at `043e8c5` (§2).
- **Expected after:** the same counts. No test is added or removed (AC2.1).
- **Test files:** the nine files §1 lists, changed as Steps 1 to 4 state. No test file is added.

## 7. Risks and rollback

- **A conflict resolution that keeps `402ec1a`'s moved copies leaves the five `f6667a2` bodies out.** The tests then build providers without the rate keys `BaseProvider` requires, and fail. AC2.2 names each such test, and AC3.1 fails on it.
- **Annotating a moved line could change a test.** AC2.2 removes annotations and collapses docstring whitespace before it compares, so any other change shows as `CHANGED`.
- **AC4.1 needs port 11434 free.** If an Ollama server is running on the machine, the stub can't bind and the command errors out instead of giving a result.
- **Rollback:** each step is one commit. Steps are reverted newest first, because Steps 3 and 4 change a file that Step 1 changed. `git revert` adds a commit that undoes the step, so the contributor's commit stays in the branch's history, and #290 still holds it.

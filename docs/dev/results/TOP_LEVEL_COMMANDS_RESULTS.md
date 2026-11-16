# Top-Level Commands — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261116
**Spec:** `../specs/TOP_LEVEL_COMMANDS_SPEC.md`
**Released as:** v1.58.6 (tag v1.58.6)

---

## 1. Summary

Complete. `workmain init`, `workmain status` and `workmain today` are removed with every name only they used, and running one gives Click's `No such command` error with exit 2. Their one test is deleted and the CLI conventions test no longer allows their names. `README.md`'s Quick Start, `docs/ARCHITECTURE.md` §2 and `docs/standards/5-cli.md` §5.1 name only commands that exist.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | The three commands and the names only they used are removed; the `status` test is deleted; `TOP_LEVEL` is `{"eod"}` and `"init"` has left `EXISTING_EXCEPTIONS`. Commit `9ab5f89`. | `workmain/cli/interface.py`, `tests/test_status_command.py` (deleted), `tests/test_cli_conventions.py` | -1 |
| 2 | The Quick Start shows DR3's block; the map entry and §5.1 name no removed command (DR4). Commit `52ed06f`. | `README.md`, `docs/ARCHITECTURE.md`, `docs/standards/5-cli.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | The AC1.1 command printed `['init', 'status', 'today']` before Step 1 and `[]` after it (§5). |
| AC2.1 | Met | `git grep -nE '\brich\b\|console\.\|click\.echo\|\bprint\(\|get_db\|Repository' workmain/cli/interface.py`: no hits (exit 1), after Step 1. |
| AC3.1 | Met | `git grep -nE 'workmain (init\|today\|status)\b' -- . ':!docs/archive' ':!docs/dev' ':!CHANGELOG.md'` and `git grep -nE '"(init\|today\|status)"' tests/test_cli_conventions.py`: no hits (exit 1 each), after Step 2. |
| AC3.2 | Met | Ray, 20261116: `docs/ARCHITECTURE.md` §2's `interface.py` entry and `docs/standards/5-cli.md` §5.1 name no removed command, and §5.1 still states that a top-level command is permitted only for an orchestration workflow |
| AC4.1 | Met | The AC4.1 check after Step 2 printed three `OK` lines and no `FAIL` line: `notes add` → `tags='cr'`, `text='Completed security audit'`; `time add` → `time='1430'`, `description='Bug fix'`, `duration='2h'`; `reports preview` → `template='daily_internal'`. |
| AC5.1 | Met | `pytest`: 1707 passed, 0 failed, 0 skipped (§5). |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | `automation/style_check.py` failed on `docs/dev/specs/TOP_LEVEL_COMMANDS_SPEC.md:77`, `81`, `82`, inside DR3's nested ```` ````text ```` fence, which it read as hard-wrapped prose. The fix was in a file Step 1 does not list. | 1 | The spec was corrected to quote DR3's block without the nested fence (`807c0a7`) and re-approved (`1933427`). The style check then passed. | Ray, 20261116 |
| 2 | Step 1's staged changes were swept into Spanner's spec-correction commit, so Step 1 had no commit of its own and could not be reverted alone (spec §7). | 1 | The branch history was rebuilt: the spec correction and re-approval were committed alone, and Step 1's changes returned to the working tree unchanged (no diff against the swept commit), then were committed as `9ab5f89`. | Ray, 20261116 |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | The blank line above `console = Console()` went with it, so two blank lines separate the imports from `_configure_cli_logging`. | Removing only the two `console` lines, which leaves three blank lines. | Keeps the module's two-blank-line spacing between top-level blocks; changes no behaviour. |
| 2 | 1 | The `# Import Phase …` comments above the group imports are left as they were. | Tidying them while the file was open. | DR1: nothing else in the module changes. |

## 5. Verification

- **Test suite:** 1707 passed, 0 failed, 0 skipped (baseline: 1708 passed, 0 failed, 0 skipped). The one fewer is `tests/test_status_command.py`'s test, deleted in Step 1.
- **Defect shown before the fix** (`docs/standards/6-testing.md` §6.2 rule 9, as the spec's Spanner Decision Log row and §6 state): the AC1.1 command, run before Step 1, printed `['init', 'status', 'today']`; run after Step 1, it printed `[]`.
- **Live verification:** `workmain status`, on the working branch after Step 1, printed `Error: No such command 'status'.` and exited 2 (DR2).
- **Daemon restart:** for close-out (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #42 | First-run setup wizard, replacing `init`. | Out of scope (spec §1). |
| #256 | A command reporting the system's current state, replacing `status`. | Out of scope (spec §1). |
| #279 | The recording renderer, the fake `ClientRepository` and §5.6's unit-of-work form. | Moved there by Ray (spec Decision Log, design study Q1). |

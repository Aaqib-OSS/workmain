# Top-Level Commands — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261116
**Branch:** `hotfix/issue-206-interface-commands` (from `main`)
**Target release:** set by `/closeout`
**Originating item:** Issue #206
**Design study:** `../design/DESIGN_TOP_LEVEL_COMMANDS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261116 | Ray | Branch type: `hotfix/*`. | Adopted; header. One application file changes (design study F9). |
| 20261116 | Ray | Design study Q1: `init`, `today` and `status` are removed, not converted. #42 replaces `init`, #256 replaces `status`, and `today` is retired. The edits to #42, #222, #254, #255, #256 and #279 are made, and #279 takes the work that outlives the conversion. | Adopted; §1, DR1, DR2. Issue edits applied 20261116. |
| 20261116 | Ray | The two map and standards removals: the three names in `docs/ARCHITECTURE.md` §2's `interface.py` entry, and `docs/standards/5-cli.md` §5.1's parenthetical list of top-level commands, which is deleted rather than updated because a hand-kept list is a register (`docs/standards/1-workflow.md` §1.5). | Adopted; DR4, Step 2. |
| 20261116 | Ray | Design study Q2: `README.md`'s Quick Start is corrected in this issue to commands that exist. | Adopted; DR3, Step 2. |
| 20261116 | Spanner | `docs/standards/6-testing.md` §6.2 rule 9 asks for a defect's test to be seen failing first. No pytest test shows this defect, because it is the existence of the commands. The AC1.1 command shows it: `['init', 'status', 'today']` before Step 1, `[]` after. The results artifact records both runs. No test that asserts the commands' absence is added, because it would pin a removal nothing can undo silently: re-adding a command is a reviewed change. | Adopted; AC1.1, §6. |
| 20261116 | Spanner | The Quick Start's `#cr` follows an unquoted argument, so the shell reads it as a comment and the tag never reaches the command. The corrected line passes the tag with `-t cr`. | Adopted; DR3. |
| 20261116 | Spanner | The issue's README criterion, "run with its arguments replaced by `--help`", is made into a command. Every Quick Start command is a group and a subcommand, so the first three words of each `workmain` line are the command. | Adopted; AC4.1. |

---

## 1. Scope

**In scope:**

- `workmain/cli/interface.py`: remove `init`, `status` and `today`, and everything only they use.
- `tests/test_status_command.py`: deleted.
- `tests/test_cli_conventions.py`: remove the removed names from `TOP_LEVEL` and `EXISTING_EXCEPTIONS`.
- `README.md`: the Quick Start block.
- `docs/ARCHITECTURE.md` §2: the `interface.py` entry.
- `docs/standards/5-cli.md` §5.1: the top-level-command bullet.
- The results artifact.

**Out of scope:**

- A replacement for any removed command. `init`'s is #42 and `status`'s is #256; `today` has none (Ray, 20261116).
- The recording renderer, the fake `ClientRepository` and §5.6's unit-of-work form, which moved to #279.
- `README.md` outside its Quick Start block.
- `CHANGELOG.md`, which `/closeout` writes.

## 2. Verified current state

Measured on `origin/main` `91102e0`, 20261116.

| Claim | Evidence |
| --- | --- |
| The three commands, and the names only they use: the module `console`, `Console`, `Table`, `date`, `get_db`, `ClientRepository`, `SystemStateRepository` | `workmain/cli/interface.py:8`, `11-16`, `58-59`, `105-116` (`init`), `119-194` (`status`), `197-270` (`today`) |
| What stays: `logging`, `os`, `sys`, `click`, `__version__`, the command-group imports, `Renderer`, `WorkmAInGroup`, `_configure_cli_logging`, `cli`, and the `cli.add_command` registrations | `interface.py:5-7`, `10`, `18-56`, `62-102`, `273-319` |
| Callers of the removed commands, found by `git grep -nE "workmain (status\|today\|init)\b\|['\"](status\|today\|init)['\"]" -- . ':!docs/archive' ':!CHANGELOG.md'` with each hit read, plus `run_workmain(` calls: none. `run_workmain` is called with `time today` only, and `interface.py:116`'s "Try: workmain status" is removed with `init` | `workmain/workflows/eod_workflow.py:364`; design study F8 |
| Importers of `interface` use only `cli` and `_configure_cli_logging` | `setup.py:10`; `tests/test_cli_conventions.py:18`, `test_cli_logging.py:20`, `38`, `75`, `86`, `test_email.py:13`, `test_output.py:18`, `test_task_lifecycle.py:27` |
| `tests/test_status_command.py` holds one test, of `status` only | `tests/test_status_command.py:12-25` |
| `TOP_LEVEL = {"eod", "status", "today"}`; `EXISTING_EXCEPTIONS` holds `"init"`; `test_every_existing_exception_is_still_in_use` fails on an entry whose command is gone | `tests/test_cli_conventions.py:40`, `55`, `170-172` |
| The Quick Start shows `workmain init`, `workmain note add "Completed security audit" #cr`, `workmain track "Bug fix" 2h` and `workmain report daily`, each of which exits 2 with `--help`. `notes add`, `time add` and `reports preview` exist; `time add` requires `-T`; `notes add` takes `-t`; `daily_internal` is a report type | `README.md:14-27`; `workmain <command> --help`; `config/ai_settings.json:52` |
| `docs/ARCHITECTURE.md` reads "- `workmain/cli/interface.py` — the root `workmain` group, and `init`, `status`, `today`." | `docs/ARCHITECTURE.md:39` |
| `docs/standards/5-cli.md` reads "- Top-level standalone commands (`eod`, `status`, `today`) are permitted **only** for orchestration workflows that coordinate across multiple groups." | `docs/standards/5-cli.md:14` |

## 3. Design rules

- **DR1 — Removal only.** `interface.py` loses the three commands and every name only they use. Nothing else in the module changes: the root group, its version option, its logging setup and its group registrations behave as before.
- **DR2 — Nothing replaces a removed name.** No command, alias or message is added for `init`, `status` or `today`. A user who runs one gets Click's own `No such command` error, with exit 2.
- **DR3 — The Quick Start shows only commands that exist.** Its block becomes exactly:

  ````text
  ```bash
  # Install
  pip install -r requirements.txt
  pip install -e .

  # Start using
  workmain notes add "Completed security audit" -t cr
  workmain time add "Bug fix" 2h -T 1430
  workmain reports preview daily_internal
  ```
  ````

- **DR4 — The map and §5.1 name no removed command.**
  - `docs/ARCHITECTURE.md:39` becomes "- `workmain/cli/interface.py` — the root `workmain` group."
  - `docs/standards/5-cli.md:14` becomes "- Top-level standalone commands are permitted **only** for orchestration workflows that coordinate across multiple groups."
  - The sub-bullet below it is unchanged.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The three commands are removed (DR1, DR2). The test of `status` is deleted. `TOP_LEVEL` becomes `{"eod"}` and `"init"` leaves `EXISTING_EXCEPTIONS`. These are one step because the conventions test fails between them. | `workmain/cli/interface.py`, `tests/test_status_command.py` (deleted), `tests/test_cli_conventions.py` |
| 2 | The Quick Start (DR3), the map entry and §5.1 (DR4). | `README.md`, `docs/ARCHITECTURE.md`, `docs/standards/5-cli.md` |
| 3 | The results artifact. | `docs/dev/results/TOP_LEVEL_COMMANDS_RESULTS.md` |

This spec adds no module, public class, public function or table.

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The root `workmain` group registers no `init`, `today` or `status` command | `python3 -c "from workmain.cli.interface import cli; print(sorted({'init','today','status'} & set(cli.commands)))"` prints `[]`, after printing `['init', 'status', 'today']` before Step 1 |
| AC2.1 | `workmain/cli/interface.py` holds the root group and its logging setup, and neither prints nor reads the database | `git grep -nE '\brich\b\|console\.\|click\.echo\|\bprint\(\|get_db\|Repository' workmain/cli/interface.py` returns no hits |
| AC3.1 | No live document or test tells a user to run a removed command, or allows its name | `git grep -nE 'workmain (init\|today\|status)\b' -- . ':!docs/archive' ':!docs/dev' ':!CHANGELOG.md'` and `git grep -nE '"(init\|today\|status)"' tests/test_cli_conventions.py` each return no hits |
| AC3.2 | `docs/ARCHITECTURE.md` §2's `interface.py` entry and `docs/standards/5-cli.md` §5.1 name no removed command, and §5.1 still states that a top-level command is permitted only for an orchestration workflow | A stated reading by Ray of those two passages |
| AC4.1 | Every command `README.md`'s Quick Start shows exists | `sed -n '/^## Quick Start/,/^## /p' README.md \| grep '^workmain ' \| while read -r w g s _; do $w $g $s --help >/dev/null; echo "$g $s $?"; done` prints at least one line, and every line ends in `0` |
| AC5.1 | The full suite passes | `pytest` reports 0 failed |

## 6. Test plan

- **Baseline before this work:** 1708 passed, 0 failed, 0 skipped (`CHANGELOG.md`, 1.58.5).
- **Expected after:** 1707 passed, 0 failed, 0 skipped. The one test in `tests/test_status_command.py` is deleted, and nothing parametrizes over the removed commands.
- No test is added (Decision Log, Spanner, 20261116). The AC1.1 command, run before Step 1 and after it, is the defect's before-and-after record that `docs/standards/6-testing.md` §6.2 rule 9 asks for, and the results artifact records both runs.

## 7. Risks and rollback

- **Someone runs a removed command.** They get Click's `No such command` error with exit 2 (DR2). No code calls these commands (§2).
- **The map, §5.1 and the Quick Start fall out of step with the code** if Step 2 is skipped. AC3.1, AC3.2 and AC4.1 catch it.
- **Rollback:** each step is one commit and reverts on its own. Reverting Step 1 restores the commands, their test and the conventions entries together.

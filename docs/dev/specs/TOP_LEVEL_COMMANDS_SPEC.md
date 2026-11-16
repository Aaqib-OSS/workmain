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
| 20261116 | Spanner | The issue's README criterion, "run with its arguments replaced by `--help`", is made into a command. Every Quick Start command is a group and a subcommand, so the first three words of each `workmain` line are the command. | Superseded by the Caliper AC4.1 row below. |
| 20261116 | Caliper | 2, Spec defect, non-blocking: §2's callers row says "`run_workmain` is called with `time today` only". That is false. `eod_workflow.py` also calls it with `meetings condense` (`226`), `clockify sync push` (`286`, `302`), `time date` (`366`), `cmd_args` for `reports save` (`914`, `936`) and `clockify report save` (`1146`, `1165`), `gdocs upload` (`1198`), `slack post weekly` (`1247`) and `email save weekly_client` (`1297`). None of these runs `init`, `today` or `status`, so the row's conclusion still holds. Design study F8 says it correctly ("called with `time today`, and with no top-level command"), so the spec and the study disagree (criterion 8). | Accepted. §2's callers row now says no `run_workmain` call runs a top-level command. |
| 20261116 | Caliper | 2, Spec defect, non-blocking: §2's Quick Start row says all four shown commands, `workmain init` included, exit 2 with `--help`. At `HEAD`, `workmain init --help` exits 0, because `init` exists until Step 1. `note add`, `track` and `report daily` exit 2. Design study F7 makes the same claim. Nothing built depends on it. | Accepted. §2's Quick Start row and design study F7 now say `init` exits 0 until Step 1 removes it. |
| 20261116 | Caliper | 7, Spec defect, non-blocking: AC4.1 checks only the first three words of each Quick Start line, so it passes when the line's arguments are wrong. It passes on `workmain notes add "…" #cr`, the shell-comment defect the Spanner `#cr` Decision Log row corrects. It also passes on `workmain time add "Bug fix" 2h` without the required `-T`. DR3's lines are correct: parsing each with Click's `make_context`, with nothing invoked, gives `tags='cr'`, `time='1430'`/`duration='2h'` and `template='daily_internal'`. A check that parses each full line the same way, splitting it with `shlex` comment handling, would tell a working line from a broken one. This doesn't block because DR3 states the text exactly. | Accepted. AC4.1 now states that each line parses with the arguments it shows and holds no shell comment, and is checked by the script under §5, which parses each full line through `make_context` and invokes nothing. Tried at 4427483: on the current README it fails `note add` (shell comment), `track` and `report daily` (no such command); on DR3's three lines it passes all three; on `time add "Bug fix" 2h` it fails with `Missing parameter: time`. |
| 20261116 | Caliper | 3, Standards gap, non-blocking: `docs/standards/6-testing.md` §6.2 rule 9 assumes a test exists that shows the defect. It doesn't say what fail-first evidence a defect fix records when the defect is that a command exists and no test can show it. The spec fills the gap with a Spanner Decision Log row that uses AC1.1's before-and-after runs. Proposed issue for Ray: rule 9 should state what a removal-only defect fix records. | **Not taken.** The same gap was opened as #289 from #286's review and closed as not planned by Ray, 20261116. The AC1.1 before-and-after record stands, as it did for #286. |
| 20261116 | Caliper | Pass at 4427483, full: 22 items checked, 0 blocking, 4 non-blocking. | n/a |

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
| Callers of the removed commands, found by `git grep -nE "workmain (status\|today\|init)\b\|['\"](status\|today\|init)['\"]" -- . ':!docs/archive' ':!CHANGELOG.md'` with each hit read, plus every `run_workmain(` call read: none. No `run_workmain` call runs a top-level command; the one that passes `today` runs `time today`. `interface.py:116`'s "Try: workmain status" is removed with `init` | `workmain/workflows/eod_workflow.py:364`; design study F8 |
| Importers of `interface` use only `cli` and `_configure_cli_logging` | `setup.py:10`; `tests/test_cli_conventions.py:18`, `test_cli_logging.py:20`, `38`, `75`, `86`, `test_email.py:13`, `test_output.py:18`, `test_task_lifecycle.py:27` |
| `tests/test_status_command.py` holds one test, of `status` only | `tests/test_status_command.py:12-25` |
| `TOP_LEVEL = {"eod", "status", "today"}`; `EXISTING_EXCEPTIONS` holds `"init"`; `test_every_existing_exception_is_still_in_use` fails on an entry whose command is gone | `tests/test_cli_conventions.py:40`, `55`, `170-172` |
| The Quick Start shows `workmain init`, `workmain note add "Completed security audit" #cr`, `workmain track "Bug fix" 2h` and `workmain report daily`. `note add`, `track` and `report daily` exit 2 with `--help`; `init` exits 0 until Step 1 removes it. `notes add`, `time add` and `reports preview` exist; `time add` requires `-T`; `notes add` takes `-t`; `daily_internal` is a report type | `README.md:14-27`; `workmain <command> --help`; `config/ai_settings.json:52` |
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
| AC4.1 | Every command `README.md`'s Quick Start shows exists and accepts the arguments the line gives it, and no line holds a shell comment that drops part of it | The AC4.1 check below, run from the repository root, prints at least one `OK` line and no `FAIL` line |
| AC5.1 | The full suite passes | `pytest` reports 0 failed |

**The AC4.1 check.** It parses each `workmain` line of the Quick Start block through Click's `make_context`, resolving each group to its subcommand, and invokes nothing.

```bash
python3 - <<'EOF'
import shlex
import click
from workmain.cli.interface import cli

def parse(cmd, name, args, parent=None):
    ctx = cmd.make_context(name, list(args), parent=parent)
    if isinstance(cmd, click.Group):
        sub_name, sub, rest = cmd.resolve_command(ctx, ctx.protected_args + ctx.args)
        return parse(sub, sub_name, rest, ctx)
    return ctx.params

block = open("README.md").read().split("## Quick Start")[1].split("\n## ")[0]
for line in (l for l in block.splitlines() if l.startswith("workmain ")):
    words = shlex.split(line)
    if shlex.split(line, comments=True) != words:
        print("FAIL shell comment:", line)
        continue
    try:
        print("OK", line, "->", parse(cli, "workmain", words[1:]))
    except click.ClickException as e:
        print("FAIL", line, "->", e.format_message())
EOF
```

## 6. Test plan

- **Baseline before this work:** 1708 passed, 0 failed, 0 skipped (`CHANGELOG.md`, 1.58.5).
- **Expected after:** 1707 passed, 0 failed, 0 skipped. The one test in `tests/test_status_command.py` is deleted, and nothing parametrizes over the removed commands.
- No test is added (Decision Log, Spanner, 20261116). The AC1.1 command, run before Step 1 and after it, is the defect's before-and-after record that `docs/standards/6-testing.md` §6.2 rule 9 asks for, and the results artifact records both runs.

## 7. Risks and rollback

- **Someone runs a removed command.** They get Click's `No such command` error with exit 2 (DR2). No code calls these commands (§2).
- **The map, §5.1 and the Quick Start fall out of step with the code** if Step 2 is skipped. AC3.1, AC3.2 and AC4.1 catch it.
- **Rollback:** each step is one commit and reverts on its own. Reverting Step 1 restores the commands, their test and the conventions entries together.

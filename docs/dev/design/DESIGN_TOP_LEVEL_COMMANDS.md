# Top-Level Commands — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261116
**Originating item:** Issue #206

---

## 1. Purpose

Issue #206 removes `workmain init`, `workmain today` and `workmain status` (`workmain/cli/interface.py`) and corrects `README.md`'s Quick Start (Ray, 20261116; Q1, Q2). This study measures everything the removal touches, at `origin/main` `91102e0`, so that the spec can name every site.

The study first examined converting the three commands. Ray ruled that out (Q1). The findings that outlive the conversion went to #279's body with the work that uses them (`docs/standards/1-workflow.md` §1.3): the recording renderer, the fake `ClientRepository`'s seeding, §5.6's unit-of-work form, and the test-database probe. Git keeps the earlier text.

## 2. Scope of the read

Read: `workmain/cli/interface.py`; every importer of it (`git grep -nE 'cli\.interface|interface import'`); `tests/test_status_command.py`; `tests/test_cli_conventions.py`; `README.md`; `docs/ARCHITECTURE.md` §2; `docs/standards/5-cli.md` §5.1; and every live mention of the three commands (`git grep -nE "workmain (status|today|init)\b|['\"](status|today|init)['\"]" -- . ':!docs/archive' ':!CHANGELOG.md'`, read hit by hit, setting aside the group subcommands of the same name).

Run: `workmain <command> --help` for each command the Quick Start shows, and for the existing commands that replace them.

Not read: `CHANGELOG.md`, which records the past and is written at close-out.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The three commands are `init`, `status` and `today`. Only they use the module `console`, `rich.console.Console`, `rich.table.Table`, `datetime.date`, `get_db`, `ClientRepository` and `SystemStateRepository`. `logging`, `os`, `sys` and `click` stay for the root group and `_configure_cli_logging`, as do `__version__`, the command-group imports, `Renderer`, `WorkmAInGroup` and the `cli.add_command` registrations. | `interface.py:5-16`, `58-59`, `105-270` | — |
| F2 | The modules that import `interface` use only `cli` and `_configure_cli_logging`, and both stay. They are the `workmain` entry point in `setup.py`, and tests in `test_cli_conventions.py`, `test_cli_logging.py`, `test_email.py`, `test_output.py` and `test_task_lifecycle.py`. None of them invokes a removed command. | `setup.py:10`; the grep in §2 | — |
| F3 | `tests/test_status_command.py` holds one test. It runs `status` through `CliRunner` and asserts the active client's name in the output. It tests nothing else, and the issue's original census did not list it. | `tests/test_status_command.py:12-25` | — |
| F4 | `tests/test_cli_conventions.py` allows the three names. `TOP_LEVEL = {"eod", "status", "today"}` and `EXISTING_EXCEPTIONS` contains `"init"`. `test_every_existing_exception_is_still_in_use` fails once `init` is gone and its entry remains, so the entry is removed in the same step. Nothing tests that `TOP_LEVEL` names a command in use. | `tests/test_cli_conventions.py:40`, `55`, `170-172` | — |
| F5 | `docs/ARCHITECTURE.md` §2 lists `interface.py` as "the root `workmain` group, and `init`, `status`, `today`". | `docs/ARCHITECTURE.md` §2 Surfaces | — |
| F6 | `docs/standards/5-cli.md` §5.1 reads: "Top-level standalone commands (`eod`, `status`, `today`) are permitted **only** for orchestration workflows that coordinate across multiple groups." | `docs/standards/5-cli.md:14` | — |
| F7 | `README.md`'s Quick Start shows four commands that do not exist: `workmain init`, `workmain note add "Completed security audit" #cr`, `workmain track "Bug fix" 2h` and `workmain report daily`. `note add`, `track` and `report daily` exit 2 with `--help`; `init` exits 0 until #206 removes it. Each of `notes add`, `time add`, `reports save` and `reports preview` exits 0 with `--help`. | `README.md:14-27`; `--help` runs | — |
| F8 | No code runs the three commands or reads their output: `run_workmain` is called with `time today`, and with no top-level command. The only other live mention is `init`'s own text, "Try: workmain status", which goes with it. | `eod_workflow.py:364`; `interface.py:116` | — |
| F9 | One application file changes: `workmain/cli/interface.py`. The rest are tests and documentation, which do not count toward `docs/standards/2-git.md` §2.2's `hotfix/*` limit. | F1–F7 | — |

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Are `init`, `today` and `status` converted to the service layer, or removed? | Ray, 20261116: **removed**. They hold almost no decisions, and converting them preserves text with no future. #42 replaces `init`, #256 replaces `status` (built on a service from the start), and `today` is retired with no replacement. The recording renderer, the fake `ClientRepository` and §5.6's unit-of-work form move to #279. Ray also approved the edits to #42, #222, #254, #255, #256 and #279, and the two removals in F5 and F6. In F6, the parenthetical list is deleted rather than updated, because a list kept in step by hand is a register (`docs/standards/1-workflow.md` §1.5). |
| Q2 | Is the rest of `README.md`'s Quick Start (F7) its own issue? | Ray, 20261116: **folded into #206**. It is the same block #206 already edits, and it is corrected to commands that exist. |

## 6. Disposition

- Promoted to:
- Superseded by:

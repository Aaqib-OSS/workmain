# The note and time-entry write family on the unit of work — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261118
**Branch:** `feature/issue-278-note-time-entry-use-cases` (from `dev`)
**Target release:** v1.61.0
**Originating item:** Issue #278
**Design study:** `../design/DESIGN_NOTE_TIME_ENTRY_USE_CASES.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261118 | Ray | The condensed summary is written by the use case, with the condensed note and the linked entry, in one unit of work. `condense_meeting` stops writing (design study Q1). | DR6, Step 3. |
| 20261118 | Spanner | The issue's first criterion's check cannot see a call through an aliased module import, and its import half matches no import form in use (design study F2). AC1.1 restates the check as a search for the four names in every unquoted form. The issue body's edit is made at close-out (`docs/standards/1-workflow.md` §1.2). | AC1.1. |
| 20261118 | Spanner | The issue's third criterion says "with nothing patched". The condense paths reach an AI provider before the use case runs (design study F18). AC3.1 restates it: nothing between the command and the use case is patched, and the provider's reply comes from `tests/mocks/stub_providers.py`. The issue body's edit is made at close-out. | AC3.1. |
| 20261124 | Ray | `record_condensation` lives in a new `workmain/services/meetings_service.py`, and `docs/ARCHITECTURE.md` §2 Application gains its line (design study Q2). | §1 Scope, DR4, Step 3, Step 4 text, AC2.1, §6. |
| 20261124 | Ray | #208's and #209's bodies are edited now to say the condense-and-link is `meetings_service.record_condensation`, delivered by #278 (design study Q3). | Edited 20261124. No spec change. |
| 20261124 | Spanner | The branch was rebased onto `dev` at `6716907`. No file §2 cites changed between `df06370` and `6716907`. The baseline is re-measured there (R16, §6). | R16, §6. |

---

## 1. Scope

**In scope:**

- `workmain/services/notes_service.py`: `create_note` and `apply_cf_hook_on_create` become operations on an entered unit of work, and the use case `add_note` is added.
- `workmain/services/time_entry_service.py`: `create_time_entry`, `create_paired_time_entry` and `link_condensed_note` become operations, and the use cases `log_meeting_time` and `log_task_time` are added.
- `workmain/services/meetings_service.py` (new): the use case `record_condensation`.
- `docs/ARCHITECTURE.md` §2 Application: the line for `workmain/services/meetings_service.py`.
- `workmain/services/clockify_service.py`: `apply_pull` takes a unit of work from its caller.
- `workmain/database/repositories/meetings_repo.py`: `MeetingsRepository.set_condensed_summary` is added.
- `workmain/ai/note_condenser.py`: `NoteCondenser.condense_meeting` stops writing the meeting.
- `workmain/orchestration/action_executor.py`: `ActionExecutor` takes no session and owns a scope for each call.
- The call sites: `workmain/cli/commands/notes.py` (`notes_add`, `notes_log`), `workmain/cli/commands/meetings.py` (`track`, `condense`), `workmain/cli/commands/time.py` (`time_add`), `workmain/cli/commands/clockify.py` (`_pull_entries`), `workmain/daemon/daemon.py` (`_execute_action`), and `workmain/integrations/slack/slack_eod.py` (`_execute_and_reprompt`).
- `tests/mocks/fake_unit_of_work.py` and `tests/test_fake_unit_of_work.py`: fakes and contract tests for every repository method the operations call (§2 row R14).
- Every test that calls a changed function or constructs `ActionExecutor` (§2 rows R3, R11, R12).
- `CLAUDE.md` § Note Write-Path Convergence.

**Out of scope:**

- The rest of each command (its reads, decisions and printing). That is #208, #209 and #216. Each command changed here still prints with `click` and still reads through its own `session_scope()`.
- `notes_service.update_note` and `apply_cf_hook_on_tag_update`. They serve only `notes edit`, which #209 converts (design study F4).
- The condenser's queries, and the models it is handed. Both are #208's under `docs/ARCHITECTURE.md` §3, "Capabilities fetching their own data". This spec removes only its write.
- `clockify_service.classify`, `plan_entry_push` and `_record_clockify_link`. The first two are #281's. The third takes no session, and `push` shares it.
- Dating a meeting's notes by the meeting (#141). Whichever of #141 and this spec lands second re-reads the other's call sites (issue body § Scope).
- The `ActionExecutor` handlers' own logic. Only where each one gets its session or unit of work changes.

## 2. Verified current state

Verified on `df06370`, 20261118, except where a row says otherwise. Re-checked on `6716907`, 20261124: `git diff --stat df06370 6716907` lists none of the files these rows cite.

| # | Claim | Evidence (file:line, symbol) |
| --- | --- | --- |
| R1 | The four functions and the hook take a session. The session-parameter check over the two modules lists seven functions: these five, plus `update_note` and `apply_cf_hook_on_tag_update`. | `python3 automation/session_param_check.py workmain/services/notes_service.py workmain/services/time_entry_service.py`, exit 1: `notes_service.py:18`, `:25`, `:39`, `:93`; `time_entry_service.py:23`, `:102`, `:130` |
| R2 | Production call sites of the four functions, found by `git grep -nP "(?<![\"'])\b(create_note\|create_paired_time_entry\|create_time_entry\|link_condensed_note)\b(?![\"'])" -- workmain`, each confirmed a call on `notes_service` or `time_entry_service` by reading it. The search also returns two comments (`time.py:285`, `action_executor.py:105`), the Clockify client's own `create_time_entry` (`workmain/integrations/clockify/client.py:83`, and its call at `clockify_service.py:274`), which are not calls of these functions, and the definitions. | `workmain/cli/commands/meetings.py:707`, `:714`, `:885`, `:894`; `workmain/cli/commands/notes.py:320`, `:356`, `:363`, `:636`, `:674`, `:683`; `workmain/cli/commands/time.py:288`, `:296`, `:307`, `:336`; `workmain/orchestration/action_executor.py:111`, `:150`; `workmain/services/clockify_service.py:477`, `:480`; inside the services, `time_entry_service.py:88` (hook), `:159` (`create_paired_time_entry` from `link_condensed_note`), and `notes_service.py:89` (hook) |
| R3 | Test call sites of the four functions, found by the same search over `tests`. Six files test the functions or a command around them. Three use them only to seed rows. `tests/test_notes_log.py:252` and `tests/test_time_add.py:88-91` patch them. | `tests/test_notes_service.py` (create_note tests, `:30`–`:216`), `tests/test_time_entry_service.py` (`:37`–`:409`), `tests/test_notes_log.py:81`, `:252`, `:270`, `:274`, `tests/test_time_add.py:88-91`, `tests/test_clockify_service.py:69`, `:78`, `:562`, `tests/test_meetings_merge.py:35`, `tests/test_meetings_reschedule.py:30`, `:37` |
| R4 | `apply_pull` is called at one production site, outside any scope. Tests call it directly, and `tests/test_clockify.py` patches it and asserts its arguments. | `workmain/cli/commands/clockify.py:163`, `:168`; `tests/test_clockify_service.py:483`–`:608`; `tests/test_clockify.py:174`, `:185`, `:194`, `:209`, `:217`, `:225`, `:283`, `:294` |
| R5 | Which call sites sit inside an open `session_scope()`, and which have written before the call. | design study F5 |
| R6 | The condenser writes `condensed_summary` and `condensed_at` on the meeting it queries, on both its return paths. No repository method writes either column. | `workmain/ai/note_condenser.py:162-164`, `:178-180`; `MeetingsRepository.update` (`meetings_repo.py:568-615`) takes neither |
| R7 | `condense_meeting`'s callers: the two commands, and tests. No test asserts that it writes the summary. `tests/test_note_condenser.py:338` asserts that a refusal leaves it unwritten. | `workmain/cli/commands/meetings.py:861-864`, `notes.py:667-668`; `tests/test_note_condenser.py`, `tests/test_compare_providers.py:109`, `tests/test_cost_display.py:109-113` |
| R8 | Readers of `condensed_summary`. | `workmain/workflows/eod_workflow.py:208`; `workmain/cli/commands/meetings.py:690-691` |
| R9 | `link_condensed_note` takes `Meeting` and `Note` models and reads `meeting.id`, `start_time`, `end_time` and `condensed_note.id`. | `workmain/services/time_entry_service.py:130-167` |
| R10 | Values the callers read from the returned models. | design study F11 |
| R11 | `ActionExecutor(session)`: every handler runs in `self.session.begin_nested()` (`:72`). The handlers `_execute_create_time_entry` and `_execute_create_note` call the write family. The other six build `TaskStatusRepository` or `ReportsRepository` on `self.session`. `_execute_create_time_entry` builds `TimeEntriesRepository(self.session)` only for `parse_time`, which delegates to `workmain/utils/time_parser.parse_time`. | `workmain/orchestration/action_executor.py:28-79`, `:87-101`, `:141-150`; `workmain/database/repositories/time_entries_repo.py:639-642` |
| R12 | `ActionExecutor` construction sites, found by `git grep -n 'ActionExecutor(' -- workmain tests automation scripts`: two in production, 37 in `tests/test_action_executor.py`. `tests/test_orchestration.py:1362` patches the class and `daemon.get_db`. `tests/test_orchestration.py` `test_t4`, `test_t5` and `test_t6` drive `_execute_action` and `_execute_and_reprompt` through the real executor. | `workmain/daemon/daemon.py:491-493`, `workmain/integrations/slack/slack_eod.py:467-469`; `tests/test_orchestration.py:1360-1366`, `:1612-1646` |
| R13 | `UnitOfWork.__enter__` raises when a non-record unit of work is entered inside an open `session_scope()`. Under `tests/conftest.py` `_isolated_database`, every session a test opens through `get_db()` joins the test's transaction, so `db_session` sees the code's writes. | `workmain/services/unit_of_work.py:84-115`; `workmain/database/connection.py:80-102`, `:134-144`; `tests/conftest.py:130-187` |
| R14 | Repository methods the operations call, and whether a fake exists. Faked: `SystemStateRepository.get_int`, `NotesRepository.get_by_id`. Not faked: `NotesRepository.create`, `TaskStatusRepository.ensure_active`, `TimeEntriesRepository.create`, `get_by_meeting`, `update`, and `MeetingsRepository.get_by_id`. `FakeUnitOfWork.REPOSITORIES` has no `time_entries` or `meetings`. `TimeEntriesRepository.create` and `update` raise `ValueError` when a project's client differs from the entry's (`_validate_client_project_consistency`). | `tests/mocks/fake_unit_of_work.py:72-75`, `:275-279`, `:426-431`; `workmain/database/repositories/time_entries_repo.py` `create`, `update`, `get_by_meeting`, `_validate_client_project_consistency`; `task_status_repo.py` `ensure_active`; `meetings_repo.py:124` |
| R15 | Use-case form in the converted services: a module docstring naming which functions are use cases and which are operations; a use case takes `uow: UnitOfWork` first, enters it with `with uow:`, and returns frozen dataclasses built inside it; an operation takes an entered `uow` and never enters it. | `workmain/services/tasks_service.py:1-8`, `:64-106`, `:138-142` |
| R16 | Baseline: `python3 automation/architecture_check.py` prints `PASS`; the suite collects 1800 tests and reports 1796 passed, 0 failed, 1 xfailed, 3 xpassed. The four x-marks are #297's non-strict `xfail` marks (`8cda7aa`), in `tests/test_slack_channel_config.py`, `tests/test_database_isolation.py` and `tests/test_gdrive.py`, none of which this spec changes. | run 20261124 on `6716907` |

## 3. Design rules

- **DR1 — Operations take an entered unit of work.** `notes_service.create_note`, `notes_service.apply_cf_hook_on_create`, `time_entry_service.create_time_entry`, `time_entry_service.create_paired_time_entry` and `time_entry_service.link_condensed_note` take `uow: UnitOfWork` as their first parameter in place of `session`. They reach the database only through `uow`'s repositories, and never enter, exit or build a unit of work. Their other parameters and their behaviour are unchanged, except `link_condensed_note`'s, which DR3 states.
- **DR2 — A use case enters the unit of work its caller builds.** Each use case DR4 names takes a `UnitOfWork` not yet entered as its first parameter, enters it once with `with uow:`, and calls only operations inside it. It returns a frozen dataclass whose fields are built inside the `with` block from plain values, never a model. A use case never calls another use case, and never builds a unit of work (`docs/standards/4-database.md` §4.1).
- **DR3 — Use cases take ids, not models.** No use case has a parameter annotated as, or passed, a model from `workmain/database/models.py`. `link_condensed_note`'s signature becomes `link_condensed_note(uow: UnitOfWork, meeting_id: int, condensed_note: Note) -> Tuple[TimeEntry, bool]`. It loads the meeting with `uow.meetings.get_by_id`, raises `ServiceValidationError` naming the id when there is none, and otherwise behaves as today. Its `condensed_note` is a model created in the same unit of work by `create_note`, so it never crosses a session.
- **DR4 — The use cases.** Each grouping is exactly one use case:

  | Use case | Module | Signature | Calls | Returns |
  | --- | --- | --- | --- | --- |
  | `add_note` | `notes_service` | `add_note(uow, content, tags=None, source="ad-hoc", meeting_id=None, project_id=None, created_at=None) -> CreatedNote` | `create_note` | `CreatedNote(id: int, content: str, display_tags: str)` |
  | `log_meeting_time` | `time_entry_service` | `log_meeting_time(uow, meeting_id: int, content: str, tags: Optional[List[str]], duration_hours: float, entry_date: date, entry_time: time, category: Optional[str] = 'meeting', project_id: Optional[int] = None, created_at: Optional[datetime] = None) -> CreatedEntry` | `create_note` with `source='meeting'`, then `create_paired_time_entry` | `CreatedEntry(entry_id: int, note_id: int, content: str, duration_hours: Decimal, display_time: str)` |
  | `log_task_time` | `time_entry_service` | `log_task_time(uow, description: str, duration_hours: float, entry_time: Optional[time] = None, entry_date: Optional[date] = None, category: Optional[str] = None, tags: Optional[List[str]] = None, project_id: Optional[int] = None) -> CreatedEntry` | `create_time_entry` | `CreatedEntry` |
  | `record_condensation` | `meetings_service` | `record_condensation(uow, meeting_id: int, summary: str, tags: List[str]) -> CondensedEntry` | `uow.meetings.set_condensed_summary(meeting_id, summary, datetime.now())`, `create_note` with `source='condensed'`, then `link_condensed_note` | `CondensedEntry(note_id: int, entry_id: int, duration_hours: Decimal, created: bool)` |
  | `apply_pull` | `clockify_service` | `apply_pull(uow: UnitOfWork, item: PullItem, answer: Optional[PullAnswer]) -> PullOutcome` | on the import path only, `create_note` with `source="clockify"`, then `create_paired_time_entry` with `clockify_id` | `PullOutcome`, unchanged |

  Each result type is defined in the use case's own module, beside it (`docs/ARCHITECTURE.md` §1, Result types). `apply_pull` enters `uow` on its import path and nowhere else. The link path keeps `_record_clockify_link`, and the skip paths write nothing. Each path returns the outcome it returns today. A failure on the import path rolls back `uow` and is caught outside the `with`, as `docs/standards/4-database.md` §4.1 places a recovering handler, and becomes today's `failed` outcome.
- **DR5 — No use case runs inside an open scope.** Every caller builds one `UnitOfWork` for each use-case call, after any `session_scope()` it opened has exited, and opens a new `session_scope()` for anything it reads afterwards. `_pull_entries` builds `UnitOfWork(record=True)`, because the pull's import records an outside action (`docs/standards/4-database.md` §4.3). Every other caller builds `UnitOfWork()`. A caller reads the values it needs from its scope as plain values, ids and strings, before the scope exits (`docs/standards/4-database.md` §4.2).
- **DR6 — The condensed summary is written by the use case.** `NoteCondenser.condense_meeting` returns the same tuple it returns today, and writes nothing: it neither sets `condensed_summary` or `condensed_at`, nor flushes. `record_condensation` writes both columns, the condensed note and the linked entry, so all three commit together or none does. `MeetingsRepository.set_condensed_summary(meeting_id: int, summary: str, condensed_at: datetime) -> Optional[Meeting]` sets the two columns on the meeting, flushes, and returns it, or returns `None` when no meeting has the id. `record_condensation` raises `ServiceValidationError` naming the id when it returns `None`.
- **DR7 — `ActionExecutor` owns a scope for each call.** `ActionExecutor()` takes no arguments. `execute(action)` keeps its signature, return type and dispatch. A handler that builds a repository runs in a `get_db().session_scope()` that `execute` opens for that call. A handler that writes a note or a time entry builds one `UnitOfWork()` and calls `add_note` or `log_task_time`, with no scope open. An exception from a handler leaves its scope or unit of work, which rolls back, and `execute` turns it into the failure `ActionResult` it returns today. `ActionExecutorError` still propagates. `_execute_create_time_entry` parses the start time with `workmain.utils.time_parser.parse_time`. `workmain/daemon/daemon.py` `_execute_action` and `workmain/integrations/slack/slack_eod.py` `_execute_and_reprompt` call `ActionExecutor().execute(action)` with no scope around it, and keep their exception handling.
- **DR8 — Behaviour is unchanged at every entry path.** Each command prints, prompts, exits and writes what it does today, in the same order. Two exceptions, both intended: a scope that today commits before a prompt (`notes.py:340`, `:658`; `time.py:333`, `:349`) is closed instead, because nothing is left in it to commit; and the condensed summary commits with the note and entry (DR6). `notes log` calls `add_note` once per line on a unit of work of its own, so a failed line is reported and rolls back alone, as its savepoint does today.
- **DR9 — Fakes answer as the real repository does.** Each repository method an operation calls has a fake in `tests/mocks/fake_unit_of_work.py`, with the real method's name and signature, and a contract class in `tests/test_fake_unit_of_work.py`, parametrized over `real` and `fake`, covering every outcome the operations rely on. These include the client-project `ValueError` in `TimeEntriesRepository.create` and `update`, `get_by_meeting`'s ordering by date then time, `ensure_active`'s idempotence, and `None` from `get_by_id` and `set_condensed_summary` for an unknown id. The methods are the six R14 lists as not faked, plus `MeetingsRepository.set_condensed_summary`. `FakeUnitOfWork.REPOSITORIES` gains `time_entries` and `meetings`. Each new fake repository's docstring states its row shapes. The `meetings` rows gain `start_time`, `end_time`, `condensed_summary` and `condensed_at`, which existing seeds that never reach `FakeMeetingsRepository` may omit.

Anything a step meets that these rules do not decide is a departure (`.claude/skills/session-start/SKILL.md` § Role 3).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `MeetingsRepository.set_condensed_summary` (owner: `MeetingsRepository`, the meetings table's repository). The fakes and contract tests DR9 names. Nothing calls the new methods yet. | `workmain/database/repositories/meetings_repo.py`, `tests/mocks/fake_unit_of_work.py`, `tests/test_fake_unit_of_work.py` |
| 2 | `ActionExecutor` owns a scope for each call (DR7). The two handlers still call the session-taking functions, on the scope `execute` opens for them. The two production callers stop opening a scope. Every test construction becomes `ActionExecutor()`. `tests/test_orchestration.py:1360-1366` patches only what `_execute_action` now reaches. | `workmain/orchestration/action_executor.py`, `workmain/daemon/daemon.py`, `workmain/integrations/slack/slack_eod.py`, `tests/test_action_executor.py`, `tests/test_orchestration.py` |
| 3 | The conversion. The operations (DR1, DR3) and the use cases (DR4) in their modules, `workmain/services/meetings_service.py` among them, with its line added to `docs/ARCHITECTURE.md` §2 Application after `time_entry_service.py`'s: `` `workmain/services/meetings_service.py` — meeting records, and a meeting's condensation. `` The map line lands in the same commit as the module, because `automation/architecture_check.py` reads the owned modules from §2. Each module's docstring states which functions are use cases and which are operations (R15). The condenser stops writing (DR6). Every call site in R2 and R4, and `ActionExecutor`'s two handlers, moves to its use case (DR5, DR7, DR8). The comments at `time.py:285` and `action_executor.py:105` that name the old calls are rewritten or removed. Every test in R3 and R4 is replaced or reseeded as §6 states. | `workmain/services/notes_service.py`, `workmain/services/time_entry_service.py`, `workmain/services/meetings_service.py`, `docs/ARCHITECTURE.md`, `workmain/services/clockify_service.py`, `workmain/ai/note_condenser.py`, `workmain/cli/commands/notes.py`, `workmain/cli/commands/meetings.py`, `workmain/cli/commands/time.py`, `workmain/cli/commands/clockify.py`, `workmain/orchestration/action_executor.py`, and the test files §6 names |
| 4 | `CLAUDE.md` § Note Write-Path Convergence is replaced with the text below. | `CLAUDE.md` |
| 5 | The results artifact, `docs/dev/results/NOTE_TIME_ENTRY_USE_CASES_RESULTS.md`. It holds the three tables AC1.2, AC2.2 and AC4.1 name, and the table pairing each faked method with its contract tests. | `docs/dev/results/NOTE_TIME_ENTRY_USE_CASES_RESULTS.md` |

Step 3 is one step because the five functions call each other (`create_time_entry` and `create_note` call the hook, `link_condensed_note` calls `create_paired_time_entry`, and `record_condensation` calls `create_note`), and a step that changes a signature updates every caller in that step (`docs/standards/1-workflow.md` §1.2).

**Step 4 replacement text.** The section's heading stays. Its body becomes:

> All note and time-entry creation in `workmain/` goes through the use cases below. Each groups operations that `notes_service.py` and `time_entry_service.py` own (`docs/standards/4-database.md` §4.1).
>
> **Use cases** — what a command, `ActionExecutor` or another surface calls, with a `UnitOfWork` it builds and does not enter:
>
> - `notes_service.add_note()` - a note on its own.
> - `time_entry_service.log_meeting_time()` - a meeting's note with its paired time entry.
> - `time_entry_service.log_task_time()` - a task-shaped time entry with its note (`source='task'`; meeting_id never reaches the Note - intentional).
> - `meetings_service.record_condensation()` - a meeting's condensed summary, its condensed note, and the time entry linked to it, committed together.
> - `clockify_service.apply_pull()` - a pulled Clockify entry's note and paired time entry, on a `UnitOfWork(record=True)`.
>
> **Operations** — called only inside a use case, on its entered unit of work: `notes_service.create_note()`, `notes_service.apply_cf_hook_on_create()`, `time_entry_service.create_time_entry()`, `time_entry_service.create_paired_time_entry()` (derives meeting_id and client_id from the created Note) and `time_entry_service.link_condensed_note()`.
>
> No file under `workmain/` outside `notes_service.py` calls `TaskStatusRepository.ensure_active` or `.set_dismissed_by_tag_removal` directly. The CF→TaskStatus hook fires from `notes_service.apply_cf_hook_on_create()` and `apply_cf_hook_on_tag_update()` (any tag-mutating update, e.g. `notes edit`). No direct `NotesRepository.create()` or `TimeEntriesRepository.create()` call exists in `workmain/` outside those two service modules.

### Authorization points

None. No migration, no GitHub object deletion, no merge to `main`, no force-push, and no change to a live service's run state. The post-merge restart is close-out's (`docs/standards/1-workflow.md` §1.4).

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No code under `workmain/` outside `workmain/services/` calls or imports any of the four operations, in any form, including through an aliased module. | `git grep -nP "(?<![\"'])\b(create_note\|create_paired_time_entry\|create_time_entry\|link_condensed_note)\b(?![\"'])" -- workmain ':!workmain/services' ':!workmain/integrations/clockify'` returning no hits. `workmain/integrations/clockify` is excluded because its `create_time_entry` is the Clockify API's, a same-named method on another object (R2), and a capability cannot import the application layer (`docs/ARCHITECTURE.md` §1). |
| AC1.2 | Every former call site in R2 and R4 calls the one use case its grouping maps to in DR4. | A stated reading by Ray of the results artifact's table of each former call site, its use case, and the commit that moved it. |
| AC1.3 | The condensed summary, the condensed note and the linked entry commit together or not at all, on both condense paths. | A service test on `fake_uow` in which `link_condensed_note` fails, asserting that the store holds no summary and no condensed note. An end-to-end `notes log` test and an end-to-end `meetings condense` test, each failing the link, asserting through `db_session` that `condensed_summary` is `None` and no `source='condensed'` note exists. |
| AC2.1 | The four operations and `apply_cf_hook_on_create` take an entered unit of work rather than a session, and so does every use case DR4 names. | `python3 -c "import inspect; from workmain.services import notes_service as n, time_entry_service as t, meetings_service as m, clockify_service as c; print([f.__name__ for f in (n.create_note, n.apply_cf_hook_on_create, n.add_note, t.create_paired_time_entry, t.create_time_entry, t.link_condensed_note, t.log_meeting_time, t.log_task_time, m.record_condensation, c.apply_pull) if 'session' in inspect.signature(f).parameters or list(inspect.signature(f).parameters)[0] != 'uow'])"` printing `[]`. |
| AC2.2 | Each operation and each use case in AC2.1 is tested at the service on `fake_uow`, with no `db_session`. | A stated reading by Ray of the results artifact's table pairing each function with its tests. |
| AC2.3 | Every repository method the operations call has a fake that matches the real method's name and signature and answers as the real one does. | `pytest tests/test_fake_unit_of_work.py` passing, with `TestFakeParity` and a contract class covering each method DR9 names. |
| AC3.1 | No use case runs inside a `session_scope()` its caller holds open, on any entry path that reaches one: `notes add`, `notes log`, `meetings track`, `meetings condense`, `time add` (the meeting path, the task path, and the extra note), Slack and the daemon through `ActionExecutor` (`create_note` and `create_time_entry`), and `clockify pull`. | For each listed path, a test that drives it from its entry point with nothing patched between the entry point and the use case passes. `UnitOfWork.__enter__` raises on any such path that enters a use case inside an open scope (R13). A condense path's provider reply comes from `tests/mocks/stub_providers.py`, and a prompt's answer comes from `CliRunner`'s `input`. The results artifact lists each path with its test's node ID. |
| AC4.1 | No use case receives a database model from its caller. | A stated reading by Ray of the results artifact's table of each use case and its parameters. |
| AC5.1 | A Clockify pull's note and paired time entry stay recorded when a later step of the pull fails. | A test that applies a pull's import through `apply_pull` on a `UnitOfWork(record=True)`, then raises inside a later `UnitOfWork()`, and finds both rows through `db_session`. A spy shows the import opened `record_scope()` (`docs/standards/6-testing.md` §6.2). |
| AC6.1 | `CLAUDE.md` § Note Write-Path Convergence describes the converted write path: the use cases a caller calls and the operations they group. | A stated reading by Ray of that section, for whether a reader knows from it alone which function to call to write a note with its time entry. |
| AC7.1 | `architecture_check` reports no new finding. | `python3 automation/architecture_check.py` printing `New findings: 0`. |
| AC8.1 | The full suite passes. | `pytest` reporting 0 failed. |

## 6. Test plan

- **Baseline before this work:** 1796 passed, 0 failed, 1 xfailed, 3 xpassed (R16).
- **Expected after:** N passed, 0 failed, and R16's four x-marks unchanged, where N is the count the results artifact records in the form `docs/standards/6-testing.md` §6 states. The count changes because tests are replaced, not only added.

Every test of changed code is replaced in its new form, in whichever file it is (`docs/standards/6-testing.md` §6.2):

- **`tests/test_fake_unit_of_work.py`** (Step 1): contract classes for the fakes DR9 names, added to `TestNotesContract` and `TestTaskStatusContract` where those exist, and new `TestTimeEntriesContract` and `TestMeetingsContract` classes.
- **`tests/test_action_executor.py`, `tests/test_orchestration.py`** (Step 2): `ActionExecutor()` in place of `ActionExecutor(db_session)`. `test_t4`, `test_t5` and `test_t6` still pass unchanged, since `UnitOfWork` and `execute`'s own scope both exit through `session_scope` (R12, R13). `tests/test_orchestration.py:1360-1366` stops patching `daemon.get_db`.
- **`tests/test_notes_service.py`, `tests/test_time_entry_service.py`** (Step 3): every test of the five operations and the three use cases in those modules runs on `fake_uow`. `update_note`'s tests stay on `db_session`.
- **`tests/test_meetings_service.py`** (new, Step 3): `record_condensation`'s tests on `fake_uow`, AC1.3's service test among them.
- **`tests/test_clockify_service.py`** (Step 3): `apply_pull`'s tests pass a unit of work. The import path is tested on `fake_uow`, the outside-action record by AC5.1's test. The seeding helper at `:69`/`:78` seeds through `NotesRepository` and `TimeEntriesRepository` on `db_session`. The test at `:562` fails the import on the fake.
- **`tests/test_clockify.py`** (Step 3): the patched `apply_pull` is asserted with a `UnitOfWork(record=True)` as its first argument.
- **`tests/test_meetings_merge.py`, `tests/test_meetings_reschedule.py`, `tests/test_notes_log.py:270-274`** (Step 3): seeding through repositories on `db_session`.
- **`tests/test_notes_add.py`, `tests/test_notes_log.py`, `tests/test_meetings_track.py`, `tests/test_meetings_condense.py`, `tests/test_time_add.py`** (Step 3): the tests for AC3.1's paths, one per path listed there, and AC1.3's two end-to-end tests. Tests that patched the old functions (`tests/test_notes_log.py:81`, `:252`; `tests/test_time_add.py:88-91`) are replaced by tests that fail the write through the repository, as `test_t16_a_failed_line_rolls_back_only_that_line` already does.
- **`tests/test_note_condenser.py`, `tests/test_cost_display.py`, `tests/test_compare_providers.py`** (Step 3): run unchanged. If any asserts that the condenser writes the meeting, it is a departure, because R7 found none.

## 7. Risks and rollback

- **A call site left inside its scope.** On a real connection, a use case under an open scope would hang where the caller holds a lock it needs. In tests it would raise instead (R13). AC3.1 covers every entry path in R2 and R4, so such a site fails the suite rather than reaching production.
- **The condenser change reaches EOD.** EOD's condense step runs `workmain meetings condense` as a child process (`workmain/workflows/eod_workflow.py:226-227`). It reaches the condenser only through that command, which Step 3 converts. A child that fails after the condenser leaves no summary, so EOD offers the meeting again, which today's grouping also guarantees.
- **`ActionExecutor` in the running daemon.** The daemon loads code at start. Until close-out restarts it, it runs the old executor against the old callers, which is consistent. Step 2 changes both together.
- **Rollback.** Each step is one commit. Reverting step 3 restores the session forms and their callers. Steps 1 and 2 stand on their own, so either can be reverted after step 3 is.

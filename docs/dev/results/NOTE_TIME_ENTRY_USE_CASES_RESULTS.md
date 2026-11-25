# The note and time-entry write family on the unit of work — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261124
**Spec:** `../specs/NOTE_TIME_ENTRY_USE_CASES_SPEC.md`
**Released as:** v1.61.0 (tag v1.61.0)

---

## 1. Summary

Complete. The five functions in the note and time-entry write family are now operations on an entered unit of work: `create_note`, `apply_cf_hook_on_create`, `create_time_entry`, `create_paired_time_entry` and `link_condensed_note`. Every caller outside `workmain/services/` reaches them through one of five use cases: `add_note`, `log_meeting_time`, `log_task_time`, `record_condensation` (in the new `workmain/services/meetings_service.py`) and `apply_pull`. Each caller builds a unit of work per call, with no scope open. The condenser no longer writes: the summary, the condensed note and the linked entry commit together. `ActionExecutor` takes no session, opens a scope for each session-taking action, and sends its two write actions to their use cases. `CLAUDE.md` § Note Write-Path Convergence is deleted, and its two pointers are corrected. `create_time_entry` writes its task note through `create_note`, so within `workmain/services/` only `notes_service.py` writes the notes table (Steps 6 and 7, folded in after the post-implementation review). Step 3 stopped once on a departure, which Ray resolved (§4).

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `MeetingsRepository.set_condensed_summary`. `NotesRepository.create` and `TimeEntriesRepository.get_by_meeting` signatures in built-in generics. Fakes for the seven methods DR9 names, `FakeUnitOfWork.REPOSITORIES` gaining `time_entries` and `meetings`, and their contract tests. Commit `984385e`. | `workmain/database/repositories/meetings_repo.py`, `workmain/database/repositories/notes_repo.py`, `workmain/database/repositories/time_entries_repo.py`, `tests/mocks/fake_unit_of_work.py`, `tests/test_fake_unit_of_work.py` | +38 |
| 2 | `ActionExecutor()` opens a scope for each call (DR7). The daemon and Slack EOD stop opening one. Commit `e31333f`. | `workmain/orchestration/action_executor.py`, `workmain/daemon/daemon.py`, `workmain/integrations/slack/slack_eod.py`, `tests/test_action_executor.py`, `tests/test_orchestration.py` | 0 |
| 3 | The operations, the use cases and `meetings_service.py` with its map line. The condenser stops writing. Every call site moves to its use case. Tests replaced, reseeded and added as §6 states. Commit `207e8a0`. | `workmain/services/notes_service.py`, `workmain/services/time_entry_service.py`, `workmain/services/meetings_service.py`, `docs/ARCHITECTURE.md`, `workmain/services/clockify_service.py`, `workmain/ai/note_condenser.py`, `workmain/cli/commands/notes.py`, `workmain/cli/commands/meetings.py`, `workmain/cli/commands/time.py`, `workmain/cli/commands/clockify.py`, `workmain/orchestration/action_executor.py`; tests: `tests/test_notes_service.py`, `tests/test_time_entry_service.py`, `tests/test_meetings_service.py` (new), `tests/test_clockify_service.py`, `tests/test_clockify.py`, `tests/test_meetings_merge.py`, `tests/test_meetings_reschedule.py`, `tests/test_notes_add.py`, `tests/test_notes_log.py`, `tests/test_meetings_track.py`, `tests/test_meetings_condense.py`, `tests/test_time_add.py`, `tests/test_note_condenser.py`, `tests/test_orchestration.py` | +16 (net: replaced, deleted and added) |
| 4 | `CLAUDE.md` § Note Write-Path Convergence deleted. Its pointers in `docs/ARCHITECTURE.md` §2 and `docs/standards/README.md` corrected. Commit `b3819e0`. | `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/standards/README.md` | 0 |
| 5 | This artifact. | `docs/dev/results/NOTE_TIME_ENTRY_USE_CASES_RESULTS.md` | 0 |
| 6 | `create_time_entry` writes its task note through `notes_service.create_note`, and its entry takes the note's client (DR10). Commit `dcdae78`. | `workmain/services/time_entry_service.py` | 0 |
| 7 | This artifact brought up to the branch tip: the Step 6 decision, the AC9.1 row, and AC7.1 and AC8.1 re-run after Step 6. | `docs/dev/results/NOTE_TIME_ENTRY_USE_CASES_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `git grep -nP "(?<![\"'])\b(create_note\|create_paired_time_entry\|create_time_entry\|link_condensed_note)\b(?![\"'])" -- workmain ':!workmain/services' ':!workmain/integrations/clockify'` exits 1 with no hits (run at `b3819e0`). |
| AC1.2 | Met | Ray, 20261124: a reading of §5 "Former call sites". |
| AC1.3 | Met | Service: `tests/test_meetings_service.py::TestRecordCondensation::test_a_failed_link_writes_no_summary_and_no_condensed_note`. End to end: `tests/test_notes_log.py::TestNotesLog::test_t17_a_failed_link_writes_no_summary_and_keeps_the_cost_and_the_notes` and `tests/test_meetings_condense.py::TestMeetingsCondense::test_a_failed_link_writes_no_summary_and_keeps_the_cost_row`. Both end-to-end tests assert through `db_session` that `condensed_summary` is `None`, that no `source='condensed'` note exists, and that the meeting's `note_condensation` `AiCost` row exists. All pass. |
| AC2.1 | Met | The spec's `python3 -c "import inspect; …"` check prints `[]`. |
| AC2.2 | Met | Ray, 20261124: a reading of §5 "Functions and their service tests". |
| AC2.3 | Met | `pytest tests/test_fake_unit_of_work.py`: 166 passed, 0 failed, 0 skipped. This includes `TestFakeParity`, and a contract class for each method DR9 names (§5 "Fakes and their contract tests"). |
| AC3.1 | Met | Every path's test passes (§5 "Entry paths and their tests"). Clockify paths replace only `ClockifyClient`, and their `apply_pull` wrapper recorded `scope_open()` as `[False]`. Condense paths replace only `_provider_manager_instance`. |
| AC4.1 | Met | Ray, 20261124: a reading of §5 "Use cases and their parameters". |
| AC5.1 | Met | `tests/test_clockify_service.py::TestPull::test_s28_an_import_stays_recorded_when_a_later_unit_of_work_fails` passes. It applies the import on a `UnitOfWork(record=True)`, raises inside a later `UnitOfWork()`, and finds the note and the entry through `db_session`. A `record_scope()` spy is called once. |
| AC6.1 | Met | `git grep -n -i -E 'write-path (convergence\|map)' -- ':!docs/archive' ':!CHANGELOG.md' ':!docs/dev/specs/NOTE_TIME_ENTRY_USE_CASES_SPEC.md' ':!docs/dev/design/DESIGN_NOTE_TIME_ENTRY_USE_CASES.md' ':!docs/dev/results/NOTE_TIME_ENTRY_USE_CASES_RESULTS.md'` exits 1 with no hits (run at `bfdc27b`, the branch tip, with the results artifact excluded as the spec's AC6.1 now states). |
| AC6.2 | Met | Ray, 20261124: a reading of `docs/ARCHITECTURE.md` §2 Application, and the module and function docstrings of `workmain/services/notes_service.py`, `time_entry_service.py` and `meetings_service.py`, for which function writes a note with its time entry. |
| AC7.1 | Met | `python3 automation/architecture_check.py` prints `New findings: 0` and `PASS` (run at `dcdae78`, after Step 6). |
| AC8.1 | Met | Bare `pytest` at `dcdae78`, after Step 6: 1850 passed, 0 failed, 0 skipped (note: 1 xfailed, 3 xpassed). |
| AC9.1 | Met | `git grep -nP 'uow\.notes\.(?!get_)\w+\|NotesRepository' -- workmain/services ':!workmain/services/notes_service.py' ':!workmain/services/unit_of_work.py'` exits 1 with no hits (run at `dcdae78`). Before Step 6 it returned `time_entry_service.py:118` (R17). The existing `tests/test_time_entry_service.py` tests ran unchanged: 27 passed. |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | `tests/test_note_condenser.py::TestCondensationRecording::test_commit_failure_after_reply_still_leaves_the_row` depended on the condenser's summary flush, which DR6 removes. §6 required that file to run unchanged. | 3 | Option B. The test is deleted. AC1.3's two end-to-end tests also assert that the `note_condensation` `AiCost` row survives the failed `record_condensation`. The spec's R7, AC1.3 and §6 were amended (Decision Log, Anvil row). | Ray, 20261124 |

The pre-implementation discrepancies D1 to D3 are Decision Log rows in the spec, settled before Step 1.

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | `notes` fake rows gain `source` and `project_id`, read with `.get` so older seeds still build. | Leaving them out. | A service test must be able to assert a note's source (`condensed`, `task`). |
| 2 | 1 | One `_build_meeting` helper serves the notes and meetings fakes. The new keys are read with `.get`. | A second builder in `FakeMeetingsRepository`. | One row-to-model mapping, and DR9 lets seeds omit the new keys. |
| 3 | 1 | One `_validate_client_project` helper, taking the record name the real message uses. | A copy per fake of each real `_validate_client_project_consistency`. | One rule, one copy. |
| 4 | 1 | `FakeTaskStatusRepository.ensure_active` writes the new row itself. | Adding a fake `create_active`. | DR9 doesn't name `create_active`. |
| 5 | 1 | `FakeTimeEntriesRepository` attaches each entry's note. | Leaving `.note` unset. | The real `create` (lazy load) and `get_by_meeting` (`joinedload`) both make it readable. |
| 6 | 1 | The contract tests seed through the `_seed_projects`, `_seed_meeting` and `_seed_note` helpers. | Inline real/fake seeding in each test. | It would repeat each seed's two branches across 19 tests. |
| 7 | 1 | `FakeClientRepository`'s docstring drops `time_entries` from its `id, client_id` row-shape line, and points `time_entries` and `meetings` rows at `FakeTimeEntriesRepository`'s and `FakeMeetingsRepository`'s shapes. | Leaving the line as it was. | Those rows gain columns in Step 1, so the old line would misstate their shape; each shape is stated once, in its own fake's docstring. |
| 8 | 2 | Handlers take the scope's session as a parameter: `handler(session, action)`. | Setting `self.session` for each call. | No per-call state left on the instance. |
| 9 | 2 | DR7's `parse_time` change is left for Step 3. | Making it in Step 2. | In Step 2 the handler still has a session, and Step 2's text changes only where handlers get one. |
| 10 | 3 | `ActionExecutor.execute` keeps two dispatch tables: use-case handlers and session handlers. | One table plus a set of names that skip the scope. | That would split one fact across two places. |
| 11 | 3 | `meetings condense` runs `record_condensation` after its scope closes, with its own `except ValueError` that prints "Condensation failed" and exits `failure_exit_code(e)`. | One handler around both calls. | One handler would have kept the scope open across the use case. |
| 12 | 3 | `notes log` re-reads the meeting by id in a new scope for the condenser, and keeps only `meeting_id` and `meeting_title` from the resolving scope. | Holding the model across scopes. | `docs/standards/4-database.md` §4.2: the model expires when its scope closes. |
| 13 | 3 | `time add` reads the push plan in a new scope and calls `push` after that scope closes. | Calling `push` inside the scope. | `docs/standards/5-cli.md` §5.6: close the scope before a service that acts outside WorkmAIn. |
| 14 | 3 | `log_task_time`'s `CreatedEntry.content` is the description it was given. | Reading `entry.note.content`. | The task note's content is that description by construction. |
| 15 | 3 | AC1.3's end-to-end link failure is a real repository failure. The meeting's entry is seeded with another client's project, so `TimeEntriesRepository.update` raises. | Patching a repository method to raise. | The failure is reached with nothing patched. |
| 16 | 3 | The condense tests take the stub reply through `_provider_manager_instance`, including the two that patched `ProviderManager.generate`. | Keeping the `generate` patch. | It is AC3.1's one replacement, and §6 says to use it. |
| 17 | 3 | The replaced command tests read no printed text except the `Error:` line on stderr. The old fallback test's check of the stderr warning is replaced by the rows the fallback reply writes. | Keeping the stderr warning check. | §6 "Form of the end-to-end tests". The notice stays covered at the condenser by `tests/test_note_condenser.py::…::test_fallback_condensation_returns_notice`. |
| 18 | 3 | AC3.1's daemon `create_time_entry` and Slack EOD `create_note` and `create_time_entry` paths are tested in `tests/test_orchestration.py::TestActionsReachTheirUseCasesWithNoScopeOpen`. | A new test file. | `tests/test_orchestration.py` is a test file §6 names, and it already holds the daemon's `create_note` path (`test_t4`). |
| 19 | 6 | The module docstring's note-first sentence now says every note is written through `notes_service.create_note`: by `create_time_entry` for a task's note, and by every other caller before `create_paired_time_entry`. | Leaving the sentence, which said `create_time_entry` writes the task note itself. | After DR10 that sentence describes the old write. |

## 5. Verification

- **Test suite:** 1850 passed, 0 failed, 0 skipped (note: 1 xfailed, 3 xpassed), 1854 collected. Baseline: 1796 passed, 0 failed, 0 skipped (note: 1 xfailed, 3 xpassed), the spec's §6.
- **Defect shown before the fix:** n/a; this is a conversion, not a defect fix.
- **Live verification:** none run. The CLI paths run on the working branch (`docs/standards/2-git.md` §2.6). The daemon and Slack paths wait for close-out's restart.

**Former call sites.** Each R2 site outside `workmain/services/`, and R4's `clockify.py:168`. Old lines are at `6716907`, new lines at `b3819e0`, and every move is commit `207e8a0`.

| Former site | Grouping | Use case | New call |
| --- | --- | --- | --- |
| `workmain/cli/commands/notes.py:320` (`notes add`) | note | `notes_service.add_note` | `notes.py:336` |
| `workmain/cli/commands/notes.py:356`, `:363` (`notes add` follow-on) | meeting note + paired entry | `time_entry_service.log_meeting_time` | `notes.py:369` |
| `workmain/cli/commands/notes.py:636` (`notes log`, each line) | note | `notes_service.add_note` | `notes.py:646` |
| `workmain/cli/commands/notes.py:674`, `:683` (`notes log` condense) | summary + condensed note + linked entry | `meetings_service.record_condensation` | `notes.py:685` |
| `workmain/cli/commands/meetings.py:707`, `:714` (`meetings track`) | meeting note + paired entry | `time_entry_service.log_meeting_time` | `meetings.py:714` |
| `workmain/cli/commands/meetings.py:885`, `:894` (`meetings condense`) | summary + condensed note + linked entry | `meetings_service.record_condensation` | `meetings.py:896` |
| `workmain/cli/commands/time.py:288`, `:296` (`time add`, meeting path) | meeting note + paired entry | `time_entry_service.log_meeting_time` | `time.py:294` |
| `workmain/cli/commands/time.py:307` (`time add`, task path) | task note + entry | `time_entry_service.log_task_time` | `time.py:308` |
| `workmain/cli/commands/time.py:336` (`time add`, extra note) | note | `notes_service.add_note` | `time.py:335` |
| `workmain/orchestration/action_executor.py:111` (`create_time_entry`) | task note + entry | `time_entry_service.log_task_time` | `action_executor.py:121` |
| `workmain/orchestration/action_executor.py:150` (`create_note`) | note | `notes_service.add_note` | `action_executor.py:161` |
| `workmain/cli/commands/clockify.py:168` (`_pull_entries`) | pulled entry | `clockify_service.apply_pull` on `UnitOfWork(record=True)` | `clockify.py:169` |

**Functions and their service tests.** Every test runs on `fake_uow` or a `FakeUnitOfWork`, with no `db_session`, except AC5.1's outside-action record (last row).

| Function | Tests |
| --- | --- |
| `notes_service.create_note` | `tests/test_notes_service.py::TestCreateNote` (10 tests) |
| `notes_service.apply_cf_hook_on_create` | `tests/test_notes_service.py::TestApplyCfHookOnCreate` (3 tests) |
| `notes_service.add_note` | `tests/test_notes_service.py::TestAddNote` (3 tests) |
| `time_entry_service.create_time_entry` | `tests/test_time_entry_service.py::TestCreateTimeEntry` (12 tests) |
| `time_entry_service.create_paired_time_entry` | `tests/test_time_entry_service.py::TestCreatePairedTimeEntry` (3 tests) |
| `time_entry_service.link_condensed_note` | `tests/test_time_entry_service.py::TestLinkCondensedNote` (6 tests) |
| `time_entry_service.log_meeting_time` | `tests/test_time_entry_service.py::TestLogMeetingTime` (3 tests) |
| `time_entry_service.log_task_time` | `tests/test_time_entry_service.py::TestLogTaskTime` (3 tests) |
| `meetings_service.record_condensation` | `tests/test_meetings_service.py::TestRecordCondensation` (5 tests) |
| `clockify_service.apply_pull` | `tests/test_clockify_service.py::TestPull`: `test_s25_classification_sees_an_earlier_link`, `test_s26_a_link_is_written_in_a_record_scope`, `test_s27_import_stamps_the_active_client`, `test_s27_import_created_at_is_not_backdated`, `test_s27_import_tags_from_the_answer`, `test_s27_import_with_the_cf_tag_creates_an_active_task`, `test_s29_a_failed_import_is_failed_writes_nothing_and_the_result_carries_an_error`, `test_s29_a_skip_returns_without_entering_the_unit_of_work`, `test_s30_a_link_that_cannot_be_recorded_is_skipped_with_a_warning`, `test_s32_an_invalid_tag_is_ignored_with_a_warning`; the outside-action record: `test_s28_an_import_stays_recorded_when_a_later_unit_of_work_fails`, on `db_session` (`docs/standards/6-testing.md` §6.2) |

**Entry paths and their tests.** AC3.1.

| Path | Test |
| --- | --- |
| `notes add` | `tests/test_notes_add.py::TestNotesAdd::test_a_note_without_a_meeting_is_written_alone`, `tests/test_notes_add.py::TestNotesAdd::test_a_meeting_note_and_its_follow_on_entry_with_the_prompted_tag` |
| `notes log` | `tests/test_notes_log.py::TestNotesLog::test_each_line_is_written_as_a_meeting_note_with_its_tags`, `tests/test_notes_log.py::TestNotesLog::test_condense_writes_the_summary_note_and_entry_with_the_computed_tags` |
| `meetings track` | `tests/test_meetings_track.py::TestMeetingsTrack::test_the_note_and_entry_carry_the_tag_and_the_active_client` |
| `meetings condense` | `tests/test_meetings_condense.py::TestMeetingsCondense::test_condense_writes_the_summary_note_and_entry_with_the_computed_tags` |
| `time add`, meeting path | `tests/test_time_add.py::TestTimeAdd::test_the_meeting_path_stamps_the_active_client_on_note_and_entry` |
| `time add`, task path | `tests/test_time_add.py::TestTimeAdd::test_the_task_path_writes_a_task_note_with_its_tags_and_entry` |
| `time add`, extra note | `tests/test_time_add.py::TestTimeAdd::test_the_meeting_path_and_its_extra_note_are_backdated_meeting_notes` |
| Daemon, `create_note` | `tests/test_orchestration.py::TestActionResultFollowsCommit::test_t4_create_note_is_in_the_database_after_the_call` |
| Daemon, `create_time_entry` | `tests/test_orchestration.py::TestActionsReachTheirUseCasesWithNoScopeOpen::test_the_daemon_logs_a_time_entry` |
| Slack, `create_note` | `tests/test_orchestration.py::TestActionsReachTheirUseCasesWithNoScopeOpen::test_slack_eod_writes_a_note` |
| Slack, `create_time_entry` | `tests/test_orchestration.py::TestActionsReachTheirUseCasesWithNoScopeOpen::test_slack_eod_logs_a_time_entry` |
| `clockify sync pull` | `tests/test_clockify.py::TestPullReachesApplyPullWithNoScopeOpen::test_sync_pull_imports_a_new_entry_with_no_scope_open` |
| `clockify sync both` | `tests/test_clockify.py::TestPullReachesApplyPullWithNoScopeOpen::test_sync_both_pushes_then_imports_with_no_scope_open` |

**Use cases and their parameters.** AC4.1. No parameter is annotated as, or passed, a model from `workmain/database/models.py`.

| Use case | Parameters |
| --- | --- |
| `notes_service.add_note` | `uow: UnitOfWork, content: str, tags: list[str] \| None, source: str, meeting_id: int \| None, project_id: int \| None, created_at: datetime \| None` |
| `time_entry_service.log_meeting_time` | `uow: UnitOfWork, meeting_id: int, content: str, tags: list[str] \| None, duration_hours: float, entry_date: date, entry_time: time, category: str \| None, project_id: int \| None, created_at: datetime \| None` |
| `time_entry_service.log_task_time` | `uow: UnitOfWork, description: str, duration_hours: float, entry_time: time \| None, entry_date: date \| None, category: str \| None, tags: list[str] \| None, project_id: int \| None` |
| `meetings_service.record_condensation` | `uow: UnitOfWork, meeting_id: int, summary: str, tags: list[str]` |
| `clockify_service.apply_pull` | `uow: UnitOfWork, item: PullItem, answer: PullAnswer \| None`. `PullItem` and `PullAnswer` are frozen dataclasses of plain values in `clockify_service.py`. |

**Fakes and their contract tests.** Each contract test is parametrized over `real` and `fake` in `tests/test_fake_unit_of_work.py`. `TestFakeParity::test_fake_methods_exist_on_real_with_equal_signatures` checks every signature.

| Faked method | Contract tests |
| --- | --- |
| `NotesRepository.create` | `TestNotesContract::test_create_writes_the_note_with_its_tags_deduplicated_and_sorted`, `test_create_without_a_time_or_tags_stamps_now_with_no_tags`, `test_create_with_its_clients_project_links_it`, `test_create_with_another_clients_project_raises`, `test_create_with_an_unknown_project_raises` |
| `TaskStatusRepository.ensure_active` | `TestTaskStatusContract::test_ensure_active_creates_an_active_task_for_a_note_without_one`, `test_ensure_active_of_an_active_task_keeps_the_one_task`, `test_ensure_active_reactivates_a_completed_task` |
| `TimeEntriesRepository.create` | `TestTimeEntriesContract::test_create_writes_the_entry_with_its_note`, `test_create_with_another_clients_project_raises` |
| `TimeEntriesRepository.get_by_meeting` | `TestTimeEntriesContract::test_get_by_meeting_orders_by_date_then_time_with_notes`, `test_get_by_meeting_of_a_meeting_without_entries_is_empty` |
| `TimeEntriesRepository.update` | `TestTimeEntriesContract::test_update_repoints_the_note_and_keeps_the_rest`, `test_update_of_unknown_id_is_none`, `test_update_to_another_clients_project_raises` |
| `MeetingsRepository.get_by_id` | `TestMeetingsContract::test_get_by_id_returns_the_meeting_with_its_times`, `test_get_by_id_of_unknown_id_is_none` |
| `MeetingsRepository.set_condensed_summary` | `TestMeetingsContract::test_set_condensed_summary_sets_both_columns_and_returns_the_meeting`, `test_set_condensed_summary_of_unknown_id_is_none` |

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Issue body edits | AC1.1's and AC3.1's restated checks (spec Decision Log, Spanner rows of 20261118) are edited into #278's body. | Close-out's (`docs/standards/1-workflow.md` §1.2). |

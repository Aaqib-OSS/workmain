# clients_service and tasks_service on the unit of work — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261117
**Spec:** `../specs/CLIENTS_TASKS_UNIT_OF_WORK_SPEC.md`
**Released as:** set by `/closeout`

---

## 1. Summary

Complete. Every public function of `clients_service` and `tasks_service` takes a `UnitOfWork` and enters it once, and every `clients` and `tasks` command builds one per use-case call. Service tests run on `fake_uow` with no database. The three new fake repositories are checked against the real ones by contract tests, and each command path runs end to end through `CliRunner` with the recording renderer. `docs/standards/5-cli.md` §5.6 states the unit-of-work form.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `FakeClientRepository`, `FakeNotesRepository` and `FakeTaskStatusRepository` with their row-shape docstrings, registered in `FakeUnitOfWork.REPOSITORIES`; the parity test with `eval_str=True`; `TestClientContract`, `TestNotesContract`, `TestTaskStatusContract`. Commit `d4c9573`. | `tests/mocks/fake_unit_of_work.py`, `tests/test_fake_unit_of_work.py` | +82 |
| 2 | The `recording_renderer` fixture and `TestRecordingRenderer`. Commit `697730b`. | `tests/conftest.py`, `tests/test_output.py` | +4 |
| 3 | `clients_service` on the unit of work, its commands, its service tests on `fake_uow`, its command tests end to end. Commit `7ebd0bf`. | `workmain/services/clients_service.py`, `workmain/cli/commands/clients.py`, `tests/test_clients_service.py`, `tests/test_clients_commands.py` | −6 |
| 4 | `tasks_service` on the unit of work, its commands, its service tests on `fake_uow`, its command tests moved to a new file end to end, the loading test moved to `TestQueries`. Commit `4a6e185`. | `workmain/services/tasks_service.py`, `workmain/cli/commands/tasks.py`, `tests/test_tasks_service.py`, `tests/test_tasks_commands.py`, `tests/test_task_lifecycle.py` | 0 |
| 5 | §5.6's unit-of-work form. Commit `ddc565b`. | `docs/standards/5-cli.md` | 0 |
| 6 | This artifact. | `docs/dev/results/CLIENTS_TASKS_UNIT_OF_WORK_RESULTS.md` | 0 |

## 3. Acceptance criteria

All checks run at `2644cfb`.

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `python3 automation/session_param_check.py workmain/services/clients_service.py workmain/services/tasks_service.py` printed nothing and exited 0. |
| AC2.1 | Met | Ray, 20261117: reviewed § 4, Functions and their service tests. `pytest tests/test_clients_service.py tests/test_tasks_service.py`: 47 passed, 0 failed, 0 skipped. `grep -n db_session tests/test_clients_service.py tests/test_tasks_service.py` returned nothing (exit 1). |
| AC3.1 | Met | `pytest tests/test_fake_unit_of_work.py::TestFakeParity`: 2 passed, 0 failed, 0 skipped. `FakeUnitOfWork.REPOSITORIES` holds `clients`, `notes`, `system_state`, `task_status`. The signature test compares `inspect.signature(..., eval_str=True)` on both sides (`tests/test_fake_unit_of_work.py:199-200`). |
| AC3.2 | Met | Ray, 20261117: reviewed the § 4, Faked methods and their contract tests. `pytest tests/test_fake_unit_of_work.py::TestClientContract tests/test_fake_unit_of_work.py::TestNotesContract tests/test_fake_unit_of_work.py::TestTaskStatusContract`: 82 passed, 0 failed, 0 skipped, 41 tests each run as `real` and `fake`. |
| AC4.1 | Met | `pytest tests/test_clients_commands.py tests/test_tasks_commands.py`: 20 passed, 0 failed, 0 skipped: the 19 tests DR15 lists and `test_c1_group_is_a_workmain_group`, kept. `grep -n -e get_db -e session_scope workmain/cli/commands/clients.py workmain/cli/commands/tasks.py` returned nothing (exit 1). `grep -n patch` hits only `tests/test_clients_commands.py:9`, the `unittest.mock` import, and `:175`, the abort test's patch of `click.confirm`. |
| AC5.1 | Met | `python3 automation/architecture_check.py` printed `New findings: 0`. |
| AC6.1 | Met | `pytest tests/test_output.py::TestRecordingRenderer`: 4 passed, 0 failed, 0 skipped. `test_is_a_renderer_so_pass_renderer_keeps_it` asserts `isinstance(recording_renderer, Renderer)`. `test_every_public_method_records_its_call_and_prints_nothing` calls each public `Renderer` method found by `inspect` and asserts the call is in `mock_calls` and `capsys` captured nothing. |
| AC7.1 | Met | Ray, 20261117: Reviewed `docs/standards/5-cli.md` §5.6's converted-command bullet and its preview and outside-action sub-bullets. |
| AC8.1 | Met | `pytest` at `2644cfb`: 1787 passed, 0 failed, 0 skipped. |
| AC8.2 | Met | `pytest tests/test_task_lifecycle.py::TestQueries`: 8 passed, 0 failed, 0 skipped, including `test_get_filtered_statement_count_does_not_grow_with_rows`. With `contains_eager(TaskStatus.note)` removed from `get_filtered` it failed. |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| 1 | `python automation/style_check.py` failed on `docs/dev/specs/CLIENTS_TASKS_UNIT_OF_WORK_SPEC.md:126`, a hard wrap in DR6 from commit `4f92185`. Working rule 5 has a style violation fixed before the commit, and the fix is an edit to the approved spec, outside step 1's files. | 1 | Spanner fixed the line (`2b85db4`) and the spec was approved again (`d42e8e5`). Step 1 then committed with the check passing. | Ray, 20261117 |
| 2 | Three `clients` command tests asserted on printed text, which `docs/standards/6-testing.md` §6.2 reserves for renderer tests and the `Error:` line: `question in result.stdout` (answered `y`), `result.stdout == ''` (`--force`) and `result.stderr == 'Aborted!\n'` (aborted). Found by the post-implementation review. | none | Revert: the three asserts are deleted from `tests/test_clients_commands.py`. Decision 17 is withdrawn. | Ray, 20261117 |
| 3 | Four read-only `tasks` command tests did not read their seeded rows back: `TestTasksList::test_limit_and_filters_cap_the_matching_tasks`, `TestTasksList::test_all_removes_the_cap_whatever_limit_says`, `TestTasksToday::test_today_shows_todays_active_tasks_matching_the_search`, `TestTasksShow::test_show_picks_the_task_and_records_its_detail`. DR15 requires the read-back. Found by the post-implementation review. | none | Revert: each test now calls `db_session.expunge_all()`, queries the seeded tasks and asserts them unchanged. | Ray, 20261117 |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | `FakeClientRepository` takes `_validate_name` and `RESERVED_NAME` from `ClientRepository`. | Copying the reserved-name message into the fake. | The message is then the real code, word for word, as `FakeSystemStateRepository` reuses `get_bool` and its siblings. |
| 2 | 1 | Private module helpers `_rows` (reads a table without creating it), `_next_id` and `_build_note`, shared by the notes and task-status fakes. | A note builder in each fake. | DR8 and DR9 build a note the same way. One builder keeps the two the same. |
| 3 | 1 | Contract tests write their rows in each test body. Each class's `_repository` (and `TestClientContract._state`) builds a repository and writes nothing, as `TestSystemStateContract._repository` does. | A shared seeding helper. | DR6: "No helper writes rows for a test"; `docs/standards/6-testing.md` §6.2: a test "builds everything else in its own body". |
| 4 | 1 | The inner-join test deletes the note: through `NotesRepository.delete` on the real side, where the database cascade removes the task, and by removing the note row on the fake side, which leaves the task row behind. | Seeding a task with no note. | The real side cannot hold one: `task_status.note_id` is a foreign key. |
| 5 | 1 | Seeded names start `Zqv` and search text is `zqv`. `list_all`'s real-side check keeps only `Zqv` names. | The existing `_T204_` prefix. | DR13 forbids `_` in search text. The test database may hold other clients. |
| 6 | 1 | Real-side seeding: `Project` and `ReportRecipient` as ORM models, everything else through its repository (`MeetingsRepository`, `NotesRepository`, `ReportsRepository`, `TimeEntriesRepository`, `TaskStatusRepository`). | ORM models throughout, as `_seed_linked` did. | DR13 has rows seeded through the repository that owns them, and ORM models only where no repository creates them. |
| 7 | 1 | Checked the contract tests against 10 deliberate faults in the fake: name order, unlinking, sort direction, limit, computed date, aware time, case folding, key order, inner join, flagged fallback. Each made at least one `fake` case fail. | Trusting a first green run. | A contract test that passes with a wrong fake proves nothing. |
| 8 | 2 | `TestRecordingRenderer`'s `isinstance` test also runs a command through `pass_renderer` and asserts it received the fixture. | `isinstance` alone. | That is the path AC6.1 guards, and it costs one command. |
| 9 | 2 | Added `test_pick_returns_the_first_row_or_none` for DR12's `side_effect`. | Leaving it to the command tests. | The cancelled-pick tests rely on overriding it. The default is otherwise untested. |
| 10 | 2 | The fixture is annotated `-> NonCallableMagicMock`, and `Renderer` is imported inside it. | Annotating `Renderer`. | It is what `create_autospec(..., instance=True)` returns. `tests/conftest.py` defers `workmain` imports until `pytest_configure` has set `DB_NAME`. |
| 11 | 3 | `_status(repo)` is the private operation `get_status` and `set_active` share (DR2). | Inlining it twice. | DR2 requires one shared operation. |
| 12 | 3 | Service tests take descriptive names without the `s<N>` prefix, and command tests without `c<N>`, except `test_c1_group_is_a_workmain_group`, which DR15 keeps unchanged. | Keeping the prefixes. | `docs/standards/1-workflow.md` §1.2: a test is cited by its node ID, never an invented ID. |
| 13 | 3 | `test_c1_group_is_a_workmain_group` gains `-> None`. | Leaving it unannotated. | The rewrite marks the line changed, and `style_check.py` then requires the annotation (ANN201). The test is otherwise unchanged. |
| 14 | 3 | The search in `test_not_found_suggests_substring_matches` is `corp`, not `_T204_`. | Keeping the old text. | DR13 binds DR14: no search text contains `_`. |
| 15 | 3 | Service tests write store rows in DR6's shapes, not through `FakeClientRepository.create`. | Seeding clients through `create`. | DR14: the store is "seeded in DR6's shapes". |
| 16 | 3 | The read-only command tests (`list`, `show`, `status`) read the seeded clients back after `expunge_all()`. | Reading back only for writing paths. | `docs/standards/6-testing.md` §6.2 asserts "the rows the path writes or leaves alone". |
| 17 | 3 | Withdrawn: reverted as departure 2. The `y` test asserted the preview's question appears on stdout, and the `--force` test asserted stdout is empty. | Patching `click.confirm` to observe it. | It conflicted with `docs/standards/6-testing.md` §6.2 on printed text. |
| 18 | 4 | `list_tasks` and `list_today` build their filters tuple before `with uow:`. The page is built and returned inside. | Everything inside the block. | The filters read no repository. DR1's result is built inside. |
| 19 | 4 | `test_complete_task` and `test_dismiss_task` become one test parametrized over both. | Two tests. | The two paths differ only in the function and the status. |
| 20 | 4 | Added `TestListToday::test_search_narrows_and_is_a_filter`, `TestGetTask::test_unknown_note_raises` and `TestChangeTask::test_complete_unknown_note_raises`. | No additions. | DR15's disposition names `TaskNotFoundError` from `get_task` and `complete_task`, and `list_today`'s search filter, as service-tested. No test covered them. |
| 21 | 4 | The `tasks today` test seeds notes at 00:01–00:03 on `date.today()`. | Patching the date. | DR15 allows no patch here. A run that crosses midnight between seeding and the command would fail. |
| 22 | 4 | `test_get_filtered_statement_count_does_not_grow_with_rows` reads each row's note `id`, `content`, `tags` and `created_date`, and asserts the row count. | Reading `ts.note` alone. | DR16 has it read the note's columns. Removing `contains_eager` makes it fail. |
| 23 | 4 | `tests/test_task_lifecycle.py`'s module docstring now states what the file covers. | Leaving it. | It described the removed command classes. |

**Functions and their service tests** (AC2.1). Classes are in `tests/test_clients_service.py` and `tests/test_tasks_service.py`.

| Function | Service tests |
| --- | --- |
| `clients_service.list_clients` | `TestList::test_lists_clients_in_name_order` |
| `clients_service.get_client` | `TestGet::test_by_id_digit_string`, `::test_by_name_in_other_case`, `::test_digit_string_gets_no_suggestions`, `::test_not_found_suggests_substring_matches`, `::test_not_found_without_matches` |
| `clients_service.add_client` | `TestAdd::test_adds_an_inactive_client`, `::test_reserved_name`, `::test_duplicate_name_in_other_case` |
| `clients_service.preview_delete` | `TestDelete::test_preview_states_linked_counts`, `::test_active_client_without_force`, `::test_active_client_with_force`, `::test_preview_of_unknown_client` |
| `clients_service.delete_client` | `TestDelete::test_delete_unlinks_linked_rows`, `::test_deleting_the_active_client_clears_the_context`, `::test_delete_of_unknown_id` |
| `clients_service.get_status` | `TestStatus::test_reports_the_active_client`, `::test_falls_back_to_the_flagged_client`, `::test_internal_when_nothing_is_active_and_formatters` |
| `clients_service.set_active` | `TestActive::test_sets_the_active_client_by_name`, `::test_internal_clears_the_context` (3 cases), `::test_unknown_name_leaves_the_active_client` |
| `tasks_service.list_tasks` | `TestListTasks::test_limit_caps_rows_and_total_counts_all`, `::test_limit_zero_returns_every_row`, `::test_status_all_returns_every_status`, `::test_status_filter_narrows`, `::test_row_fields_equal_seeded`, `::test_filters_hold_only_narrowing_filters` |
| `tasks_service.list_today` | `TestListToday::test_active_tasks_on_the_date_only`, `::test_search_narrows_and_is_a_filter` |
| `tasks_service.find_tasks` | `TestFindTasks::test_digit_string_is_a_note_id`, `::test_unknown_id_raises`, `::test_note_without_task_raises`, `::test_search_finds_tasks_only`, `::test_search_covers_every_status`, `::test_search_is_capped_at_ten`, `::test_no_match_raises` |
| `tasks_service.get_task` | `TestGetTask::test_completed_task_with_meeting_and_forwarding_note`, `::test_dismissed_task_sets_dismissed_at`, `::test_note_without_task_raises`, `::test_unknown_note_raises` |
| `tasks_service.complete_task` | `TestChangeTask::test_change_sets_the_status_and_returns_the_row[complete_task-completed]`, `::test_complete_note_without_task_raises`, `::test_complete_unknown_note_raises` |
| `tasks_service.dismiss_task` | `TestChangeTask::test_change_sets_the_status_and_returns_the_row[dismiss_task-dismissed]` |

**Faked methods and their contract tests** (AC3.2). All in `tests/test_fake_unit_of_work.py`, each run with `kind` `real` and `fake`.

| Method | Contract tests |
| --- | --- |
| `ClientRepository.create` | `TestClientContract::test_create_writes_an_inactive_client`, `::test_create_refuses_the_reserved_name`, `::test_create_refuses_a_duplicate_in_other_case` |
| `ClientRepository.get_by_id` | `TestClientContract::test_get_by_id_of_unknown_id_is_none`; the found case in `::test_create_writes_an_inactive_client` |
| `ClientRepository.get_by_name` | `TestClientContract::test_get_by_name_ignores_case_and_padding`, `::test_get_by_name_of_unknown_name_is_none` |
| `ClientRepository.find_by_name_fuzzy` | `TestClientContract::test_find_by_name_fuzzy_matches_substrings_in_name_order` |
| `ClientRepository.list_all` | `TestClientContract::test_list_all_returns_every_client_in_name_order` |
| `ClientRepository.delete` | `TestClientContract::test_delete_of_unknown_id_is_false`, `::test_delete_removes_the_client_and_unlinks_its_rows` |
| `ClientRepository.count_linked_records` | `TestClientContract::test_count_linked_records_counts_by_table_in_order` |
| `ClientRepository.set_active` | `TestClientContract::test_set_active_flags_one_client_and_stores_its_id`, `::test_set_active_of_unknown_id_raises` |
| `ClientRepository.clear_active` | `TestClientContract::test_clear_active_unflags_and_deletes_the_stored_id` |
| `ClientRepository.get_active` | `TestClientContract::test_get_active_returns_the_client_the_stored_id_names`, `::test_get_active_without_a_stored_id_falls_back_to_the_flagged_client`, `::test_get_active_falls_back_when_the_stored_id_names_no_client`, `::test_get_active_with_nothing_active_is_none` |
| `NotesRepository.get_by_id` | `TestNotesContract::test_get_by_id_returns_the_note_with_its_meeting`, `::test_get_by_id_of_a_note_without_a_meeting`, `::test_get_by_id_of_unknown_id_is_none` |
| `TaskStatusRepository.get_by_note_id` | `TestTaskStatusContract::test_get_by_note_id_returns_the_task_with_its_note`, `::test_get_by_note_id_of_a_note_without_a_task_is_none` |
| `TaskStatusRepository.get_filtered` | `TestTaskStatusContract::test_get_filtered_filters_by_status` (5 cases), `::test_search_and_date_filter_narrow_both_queries`, `::test_get_filtered_orders_newest_first_and_applies_the_limit` (2 cases), `::test_a_task_whose_note_is_gone_is_neither_listed_nor_counted` |
| `TaskStatusRepository.count_filtered` | `TestTaskStatusContract::test_count_filtered_filters_by_status` (5 cases), `::test_search_and_date_filter_narrow_both_queries`, `::test_a_task_whose_note_is_gone_is_neither_listed_nor_counted` |
| `TaskStatusRepository.set_completed` | `TestTaskStatusContract::test_status_change_sets_status_and_times` and `::test_status_change_of_a_note_without_a_task_raises`, their `set_completed` cases |
| `TaskStatusRepository.set_dismissed` | `TestTaskStatusContract::test_status_change_sets_status_and_times` and `::test_status_change_of_a_note_without_a_task_raises`, their `set_dismissed` cases |

**Replaced tests.** Each existing test, with the test that replaced it or its disposition under DR14–DR16.

| Existing test | Replaced by |
| --- | --- |
| `tests/test_clients_service.py::TestList::test_s1_lists_clients_in_name_order` | `TestList::test_lists_clients_in_name_order` |
| `::TestGet::test_s2_by_id_digit_string` | `TestGet::test_by_id_digit_string` |
| `::TestGet::test_s3_by_name_in_other_case` | `TestGet::test_by_name_in_other_case` |
| `::TestGet::test_s4_digit_string_gets_no_suggestions` | `TestGet::test_digit_string_gets_no_suggestions` |
| `::TestGet::test_s5_not_found_suggests_substring_matches` | `TestGet::test_not_found_suggests_substring_matches` |
| `::TestGet::test_s6_not_found_without_matches` | `TestGet::test_not_found_without_matches` |
| `::TestAdd::test_s7_adds_an_inactive_client` | `TestAdd::test_adds_an_inactive_client` |
| `::TestAdd::test_s8_reserved_name` | `TestAdd::test_reserved_name` |
| `::TestAdd::test_s9_duplicate_name_in_other_case` | `TestAdd::test_duplicate_name_in_other_case` |
| `::TestDelete::test_s10_preview_states_linked_counts` | `TestDelete::test_preview_states_linked_counts` |
| `::TestDelete::test_s11_active_client_without_force` | `TestDelete::test_active_client_without_force` |
| `::TestDelete::test_s12_active_client_with_force` | `TestDelete::test_active_client_with_force` |
| `::TestDelete::test_s13_preview_of_unknown_client` | `TestDelete::test_preview_of_unknown_client` |
| `::TestDelete::test_s14_delete_unlinks_linked_rows` | `TestDelete::test_delete_unlinks_linked_rows`; against the database, `tests/test_fake_unit_of_work.py::TestClientContract::test_delete_removes_the_client_and_unlinks_its_rows` |
| `::TestDelete::test_s15_deleting_the_active_client_clears_the_context` | `TestDelete::test_deleting_the_active_client_clears_the_context` |
| `::TestDelete::test_s16_delete_of_unknown_id` | `TestDelete::test_delete_of_unknown_id` |
| `::TestActive::test_s17_sets_the_active_client_by_name` | `TestActive::test_sets_the_active_client_by_name` |
| `::TestActive::test_s18_internal_clears_the_context` (3 cases) | `TestActive::test_internal_clears_the_context` (3 cases) |
| `::TestActive::test_s19_unknown_name_leaves_the_active_client` | `TestActive::test_unknown_name_leaves_the_active_client` |
| `::TestStatus::test_s20_reports_the_active_client` | `TestStatus::test_reports_the_active_client` |
| `::TestStatus::test_s21_falls_back_to_the_flagged_client` | `TestStatus::test_falls_back_to_the_flagged_client`; against the database, `tests/test_fake_unit_of_work.py::TestClientContract::test_get_active_without_a_stored_id_falls_back_to_the_flagged_client` |
| `::TestStatus::test_s22_internal_when_nothing_is_active_and_formatters` | `TestStatus::test_internal_when_nothing_is_active_and_formatters` |
| `tests/test_clients_commands.py::TestClientsCommands::test_c1_group_is_a_workmain_group` | Kept |
| `::test_c2_add` | `TestClientsCommands::test_add` |
| `::test_c3_list` | `TestClientsCommands::test_list` |
| `::test_c4_show` | `TestClientsCommands::test_show` |
| `::test_c5_status` | `TestClientsCommands::test_status` |
| `::test_c6_set_active` | `TestClientsCommands::test_set_active` |
| `::test_c7_confirmed_delete` | `TestClientsCommands::test_delete_answered_yes_deletes_and_unlinks` |
| `::test_c8_declined_delete_does_not_apply` | `TestClientsCommands::test_delete_answered_no_keeps_the_client` |
| `::test_c9_force_deletes_without_asking` | `TestClientsCommands::test_delete_with_force_deletes_the_active_client_without_asking` |
| `::test_c10_preview_scope_closes_before_the_question` | Retired: the preview use case exits its unit of work before it returns, and a `UnitOfWork` is never entered twice |
| `::test_c11_errors_exit_1_with_one_error_line` (4 cases) | The service tests raising each error: `TestGet::test_not_found_without_matches`, `TestAdd::test_reserved_name`, `TestDelete::test_active_client_without_force`, `TestActive::test_unknown_name_leaves_the_active_client`; and `tests/test_output.py::TestWiring::test_service_error_is_a_clean_error_line` |
| `::test_c12_show_needs_an_argument` | Retired: Click's usage error, covered by `tests/test_output.py::TestWiring::test_click_exceptions_keep_their_exit_codes` |
| `::test_c13_interrupted_prompt_aborts` | `TestClientsCommands::test_delete_aborted_prompt_exits_1_and_keeps_the_client` |
| `tests/test_tasks_service.py::TestListTasks` `test_limit_caps_rows_and_total_counts_all`, `test_limit_zero_returns_every_row`, `test_status_all_returns_every_status`, `test_status_filter_narrows`, `test_row_fields_equal_seeded`, `test_filters_hold_only_narrowing_filters` | The fake-unit-of-work test of the same name in `TestListTasks` |
| `::TestListTasks::test_statement_count_does_not_grow_with_rows` | `tests/test_task_lifecycle.py::TestQueries::test_get_filtered_statement_count_does_not_grow_with_rows` (DR16) |
| `::TestListToday::test_active_tasks_on_the_date_only` | `TestListToday::test_active_tasks_on_the_date_only` |
| `::TestFindTasks` `test_digit_string_is_a_note_id`, `test_unknown_id_raises`, `test_note_without_task_raises`, `test_search_finds_tasks_only`, `test_search_covers_every_status`, `test_search_is_capped_at_ten`, `test_no_match_raises` | The fake-unit-of-work test of the same name in `TestFindTasks` |
| `::TestGetTask` `test_completed_task_with_meeting_and_forwarding_note`, `test_dismissed_task_sets_dismissed_at`, `test_note_without_task_raises` | The fake-unit-of-work test of the same name in `TestGetTask` |
| `::TestChangeTask::test_complete_task` | `TestChangeTask::test_change_sets_the_status_and_returns_the_row[complete_task-completed]` |
| `::TestChangeTask::test_dismiss_task` | `TestChangeTask::test_change_sets_the_status_and_returns_the_row[dismiss_task-dismissed]` |
| `::TestChangeTask::test_complete_note_without_task_raises` | `TestChangeTask::test_complete_note_without_task_raises` |
| `tests/test_task_lifecycle.py::TestTasksListCommand::test_defaults` | `tests/test_tasks_commands.py::TestTasksList::test_defaults_show_active_tasks_capped_at_20` |
| `::TestTasksListCommand::test_every_option` | `tests/test_tasks_commands.py::TestTasksList::test_all_removes_the_cap_whatever_limit_says` |
| `::TestTasksListCommand::test_bad_status_is_a_usage_error` | Retired: `click.Choice` refuses the value; `tests/test_output.py::TestWiring::test_click_exceptions_keep_their_exit_codes` |
| `::TestTasksListCommand::test_bad_date_is_a_usage_error` | `tests/test_cli_params.py::TestDateParamType::test_bad_date_is_a_usage_error` |
| `::TestTasksTodayCommand::test_today` | `tests/test_tasks_commands.py::TestTasksToday::test_today_shows_todays_active_tasks_matching_the_search` |
| `::TestTasksShowCommand::test_show_finds_picks_gets_and_records` | `tests/test_tasks_commands.py::TestTasksShow::test_show_picks_the_task_and_records_its_detail` |
| `::TestTasksShowCommand::test_cancelled_pick_exits_zero_and_gets_nothing` | `tests/test_tasks_commands.py::TestTasksShow::test_show_with_the_pick_cancelled_records_nothing` |
| `::TestTasksShowCommand::test_service_error_reaches_stderr_with_exit_1` | `tests/test_tasks_service.py::TestFindTasks::test_no_match_raises` and `tests/test_output.py::TestWiring::test_service_error_is_a_clean_error_line` |
| `::TestTasksCompleteDismissCommand::test_complete` | `tests/test_tasks_commands.py::TestTasksCompleteDismiss::test_complete_marks_the_picked_task_completed` |
| `::TestTasksCompleteDismissCommand::test_dismiss` | `tests/test_tasks_commands.py::TestTasksCompleteDismiss::test_dismiss_marks_the_picked_task_dismissed` |
| `::TestTasksCompleteDismissCommand::test_cancelled_pick_changes_nothing` | `tests/test_tasks_commands.py::TestTasksCompleteDismiss::test_complete_with_the_pick_cancelled_changes_nothing` |
| `::TestTasksCompleteDismissCommand::test_service_error_on_change` | `tests/test_tasks_service.py::TestChangeTask::test_complete_note_without_task_raises` and `tests/test_output.py::TestWiring::test_service_error_is_a_clean_error_line` |
| `::TestTasksCompleteDismissCommand::test_dismiss_with_find_error_dismisses_nothing` | `tests/test_tasks_service.py::TestFindTasks::test_note_without_task_raises` and `tests/test_output.py::TestWiring::test_service_error_is_a_clean_error_line` |

New tests with no predecessor: `tests/test_tasks_commands.py::TestTasksList::test_limit_and_filters_cap_the_matching_tasks` and `::TestTasksCompleteDismiss::test_dismiss_with_the_pick_cancelled_changes_nothing` (DR15), and the three service tests of decision 20.

## 5. Verification

- **Test suite:** 1787 passed, 0 failed, 0 skipped at `2644cfb` (baseline at `b63ccac`: 1707 passed, 0 failed, 0 skipped) — form per `docs/standards/6-testing.md` §6.
- **Defect shown before the fix:** n/a; no defect fix.
- **Live verification:** none run. The spec names no live check.
- **Daemon restart:** close-out's (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| `.claude/skills/session-start/references/anvil.md` read 5, Command | The open-time rule takes exit 1 as a discrepancy for any command other than `grep`/`git grep`. A check whose expected pre-work result is exit 1, such as `automation/session_param_check.py` listing session-taking functions, is then reported as a discrepancy when it is the claim (session open, 20261117). Needs: the rule compares a command's exit status with what the spec states before the work. | Outside this spec's scope (`docs/standards/1-workflow.md` §1.2). For Ray to decide whether it becomes an issue. |

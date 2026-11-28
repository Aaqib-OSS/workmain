# The active client in one home — Implementation Results

**Status:** Active

**Author:** Anvil

**Date:** 20261127

**Spec:** `../specs/ACTIVE_CLIENT_SPEC.md`

**Released as:** set at close-out

---

## 1. Summary

Complete. `clients.is_active` is now the only store of the active client, and `ClientRepository.get_active()` is its only lookup. Revision `0002` moves the `system_state` key `active_client_id` into the flag, deletes the key, and replaces `idx_clients_is_active` with the unique partial index `uq_clients_one_active`, so the database refuses a second flagged row. Every lookup in the spec's §2 calls `get_active()`, and the repository and its fake read and write the flag alone. `docs/ARCHITECTURE.md` §2 names the one lookup, and §3's #255 entry is gone. `0002` is applied to live. `workmain-notify.service` is stopped and stays stopped until `/closeout`'s restart.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Revision `0002`, with `move_key_to_flag` and `move_flag_to_key`; `Client` declares `uq_clients_one_active` (`3817608`) | `workmain/database/migrations/versions/0002_active_client_flag.py`, `workmain/database/models.py`, `tests/test_active_client_revision.py`, `tests/test_client_repository.py` | +10 |
| 2 | Every lookup calls `get_active()`; key seeds and reader patches replaced; entry-path tests (`bef0333`) | `workmain/services/notes_service.py`, `workmain/services/email_service.py`, `workmain/cli/commands/email.py`, `workmain/cli/commands/meetings.py`, `workmain/cli/commands/reports.py`, `workmain/cli/commands/slack.py`, `workmain/cli/commands/time.py`, `workmain/workflows/eod_workflow.py`, `scripts/compare_providers.py`, `tests/test_action_executor.py`, `tests/test_ai_arguments.py`, `tests/test_clockify_service.py`, `tests/test_compare_providers.py`, `tests/test_email_recipients_client.py`, `tests/test_email_service.py`, `tests/test_eod_workflow.py`, `tests/test_meetings_track.py`, `tests/test_notes_service.py`, `tests/test_report_generator.py`, `tests/test_slack_channel_config.py`, `tests/test_time_add.py`, `tests/test_time_entry_service.py` | +6 |
| 3 | The architecture map (`3b5b8aa`) | `docs/ARCHITECTURE.md` | 0 |
| 4 | The repository and its fake hold the flag alone; the fake refuses two flagged clients (`3ec7c6b`) | `workmain/database/repositories/client_repository.py`, `tests/mocks/fake_unit_of_work.py`, `tests/test_client_repository.py`, `tests/test_fake_unit_of_work.py`, `tests/test_clients_service.py`, `tests/test_clients_commands.py`, `tests/test_notes_service.py` | +2 (8 added, 6 removed) |
| 5 | Service stopped; `0002` applied to live | none | n/a |
| 6 | This artifact | `docs/dev/results/ACTIVE_CLIENT_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | At `3ec7c6b`, the spec's `git grep -nE` over `workmain scripts tests/mocks` hits only `workmain/database/repositories/client_repository.py` (the `Client.is_active == True` filters and the flag write) and `workmain/database/migrations/versions/0002_active_client_flag.py` (`_KEY`). Both are allowed files. |
| AC1.2 | Met | Ray, 20261127: read the lookup table under §5 Verification, each former lookup and the call that replaced it |
| AC1.3 | Met | The spec's `pytest` over the ten files: 259 passed, 0 failed, 0 skipped (1 xfailed, 1 xpassed). The test for each lookup is in the lookup table under §5. Each seeds a flagged client and no key. |
| AC2.1 | Met | `pytest tests/test_client_repository.py tests/test_fake_unit_of_work.py`: 186 passed, 0 failed, 0 skipped. Covers `tests/test_client_repository.py::TestClientRepositoryActiveContext::test_flushing_a_second_flagged_client_raises` and `tests/test_fake_unit_of_work.py::TestFakeClientRefusesTwoFlaggedClients::test_the_active_client_methods_raise[get_active]` |
| AC2.2 | Met | `pytest tests/test_clients_service.py tests/test_notes_service.py`: 44 passed, 0 failed, 0 skipped. Covers `tests/test_clients_service.py::TestDelete::test_deleting_the_active_client_clears_the_context` and `tests/test_notes_service.py::TestCreateNote::test_after_the_active_client_is_deleted_no_client_is_stamped` |
| AC2.3 | Met | `pytest tests/test_active_client_revision.py`: 9 passed, 0 failed, 0 skipped. That is seven `TestMoveKeyToFlag` cases, one per DR6 case, including the two that raise and change neither store. The other two are `TestMoveFlagToKey`, including `test_writes_no_key_when_no_client_is_flagged`. |
| AC2.4 | Met | `pytest tests/test_fake_unit_of_work.py`: 169 passed, 0 failed, 0 skipped. Covers `tests/test_fake_unit_of_work.py::TestClientContract::test_set_active_moves_the_flag_without_raising`, with targets `another client` and `the flagged client`, each on `real` and `fake` |
| AC3.1 | Met | Ray, 20261127: read the `clients` and `system_state` table comments as `0002` sets them (under §5, live verification) and `docs/ARCHITECTURE.md` §2's Data line naming `get_active()`. `grep -n 'The active client' docs/ARCHITECTURE.md` exits 1, with no §3 entry. |
| AC4.1 | Met | Bare `pytest` at `3ec7c6b`: 1880 passed, 0 failed, 0 skipped (1 xfailed, 3 xpassed) |

## 4. Deviations and decisions

No step stopped on a departure.

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | The revision parses the key with a private `_parse_key` that copies `SystemStateRepository.get_int`'s rule | Calling `SystemStateRepository` | It takes a `Session`, not a `Connection`. A revision should also stay independent of application code that later changes. |
| 2 | 1 | Table comments are set with `op.create_table_comment`, with the baseline texts as constants checked equal to `0001_baseline.sql` | Raw `COMMENT ON` statements | It is Alembic's mechanism (`docs/standards/3-code.md` §3.8) |
| 3 | 1 | The `RuntimeError` gives the key's raw value and every flagged client as `<id> (<name>)`, and says to settle the stores and rerun | Listing only the clients that disagree | DR6 asks for every flagged client |
| 4 | 1 | `move_flag_to_key` upserts with `INSERT ... ON CONFLICT (key) DO UPDATE` on `system_state_pkey`, from the lowest flagged id | Delete, then insert | One statement. The index allows only one flagged row anyway. |
| 5 | 1 | `Client`'s `Index` takes the `is_active` `Column` object and `postgresql_where=is_active`, with `__table_args__` after the columns | String column name and `text('is_active')` | Uses the declared column. It compiles to the revision's DDL: `CREATE UNIQUE INDEX uq_clients_one_active ON clients (is_active) WHERE is_active` |
| 6 | 1 | The revision header uses `str \| None`, not the template's `Union` | The template as generated | `automation/style_check.py` requires it (§3.5) |
| 7 | 1 | The revision test loads the module by path with `importlib`. The `move_flag_to_key` tests are a `TestMoveFlagToKey` class beside `TestMoveKeyToFlag`. | `import_module`; one class | The file name is not an identifier, and related tests share a class (§6.2) |
| 8 | 2 | Each session-form lookup keeps its local `active_client_id`, set from `get_active()` | Passing the `Client` downstream | The code after each lookup is unchanged |
| 9 | 2 | `slack status` drops its `(unknown)` branch | Keeping it | It printed only when the key named a deleted client; `get_active()` returns a client or `None` |
| 10 | 2 | Lookup tests seed the flag on the client row, not through `set_active()`. `_make_active_client` keeps `set_active()`, as step 2 allows. | `set_active()` everywhere | Until step 4, `set_active()` also wrote the key; a flag-only seed shows the flag alone resolves the client |
| 11 | 2 | The unassign test seeds a global and a client-scoped assignment | One client-scoped assignment | Only a lookup that finds the flagged client leaves the global one |
| 12 | 2 | The CLI tests patch `require_report_type` or `require_eligible_provider` | Reading `config/` | A test sets up what it needs (§6.2) |
| 13 | 2 | The EOD tests without `db_session` take it to seed or clear the flag | Patching `ClientRepository` | Every `get_db()` session joins the test's transaction (`tests/conftest.py` `_isolated_database`) |
| 14 | 2 | Added `tests/test_meetings_track.py::TestMeetingsCreate::test_the_meeting_carries_the_flagged_client` | Relying on the file's existing test | AC1.3 names this file for the `meetings create` lookup, but its one test runs `meetings track`, which does not reach `meetings.py` `create`. The file is a step 2 file, and AC1.3 requires a test per lookup. |
| 15 | 2 | `scripts/compare_providers.py`'s import block, which the step edits, is wrapped as ruff I001 requires | Leaving it | `automation/style_check.py` checks every changed line |
| 16 | 4 | `get_active` uses `.first()` | `.one_or_none()` | It keeps the exceptions it had (DR8). The index allows only one flagged row. |
| 17 | 4 | The fake checks the store through one private `_flagged()` at the start of each of the three methods, before it changes anything | A check after each write | A refused call leaves the store as it was |
| 18 | 4 | The fake's refusal test is parametrized over `set_active`, `clear_active` and `get_active` | `get_active` alone, as AC2.1 asks | DR5 names all three |
| 19 | 4 | `test_delete_active_client` also asserts `get_active() is None` | Removing only its comments | Its docstring says it shows that |
| 20 | 4 | `TestClientContract`'s `_state` helper is removed | Keeping it | No rewritten test reads `system_state` |

## 5. Verification

- **Test suite:** 1880 passed, 0 failed, 0 skipped (1 xfailed, 3 xpassed), at `3ec7c6b`. The baseline was 1862 passed, 0 failed, 0 skipped (1 xfailed, 3 xpassed). Step 1 added 10, step 2 added 6, and step 4 added 8 and removed 6.
- **Revision round trip, test database only:** with `DB_NAME=workmain_test`, `alembic downgrade 0001` then `alembic upgrade head` each exited 0. At `0001` the database held `idx_clients_is_active` and the baseline comments, and at `0002` it held `uq_clients_one_active` and the new comments.
- **Live verification, 20261127:**
  - **Item 1:** Ray stopped `workmain-notify.service`, after Claude Code's permission check refused Anvil's `systemctl` call. `systemctl --user is-active` then read `inactive`.
  - **Item 2:** `alembic current` read `0001`, on database `workmain`.
  - **Item 3:** 1 flagged client and 1 `active_client_id` key. A read-only check, printing true or false only, found that the key parsed, named an existing client, and named the flagged one.
  - **Item 4:** `alembic upgrade head` ran `0001 -> 0002` and exited 0, and `alembic current` read `0002 (head)`.
  - **Item 5:** 1 flagged client and 0 `active_client_id` keys. `clients` holds `uq_clients_one_active` and no `idx_clients_is_active`, and both table comments match the spec's step 1 text.
- **Lookups and their tests (AC1.2, AC1.3):**

| Former lookup | Replaced by | Test |
| --- | --- | --- |
| `clients_service._status` | `repo.get_active()` (already; now flag only) | `tests/test_clients_service.py::TestStatus::test_reports_the_active_client` |
| `notes_service.create_note` | `uow.clients.get_active()` | `tests/test_notes_service.py::TestCreateNote::test_the_active_client_is_stamped` |
| `email_service._draft_recipients` | `ClientRepository(session).get_active()` | `tests/test_email_service.py::TestBuildDraft::test_build_draft_includes_the_flagged_clients_recipients` |
| `cli/commands/email.py` `email_assign` | `ClientRepository(session).get_active()` | `tests/test_email_recipients_client.py::TestEmailCommandsUseTheActiveClient::test_assign_writes_the_assignment_at_the_flagged_clients_scope` |
| `cli/commands/email.py` `email_unassign` | `ClientRepository(session).get_active()` | `tests/test_email_recipients_client.py::TestEmailCommandsUseTheActiveClient::test_unassign_removes_the_assignment_at_the_flagged_clients_scope` |
| `cli/commands/meetings.py` `create` | `ClientRepository(session).get_active()` | `tests/test_meetings_track.py::TestMeetingsCreate::test_the_meeting_carries_the_flagged_client` |
| `cli/commands/reports.py` `generate_report_impl` | `ClientRepository(session).get_active()` | `tests/test_report_generator.py::TestPreviewRouting::test_cli_preview_of_a_client_template_filters_on_the_flagged_client` |
| `cli/commands/slack.py` `_resolve_client_channel` | `ClientRepository(session).get_active()` | `tests/test_slack_channel_config.py::TestResolveSlackChannel::test_returns_client_channel_when_set` |
| `cli/commands/slack.py` `slack_status` | `ClientRepository(session).get_active()` | `tests/test_slack_channel_config.py::TestSlackStatusDisplay::test_slack_status_shows_client_channel` |
| `cli/commands/slack.py` `slack_set_channel` | `client_repo.get_active()`, then `update` by its id | `tests/test_slack_channel_config.py::TestSlackSetChannel::test_slack_set_channel_active_client` |
| `workflows/eod_workflow.py` `_run_report_review_step` weekly guard | `ClientRepository(session).get_active()` | `tests/test_eod_workflow.py::TestReportReviewStepCollapse::test_weekly_generation_error_fatal_when_non_interactive` (the step runs); `::test_weekly_g1_no_active_client_skips_without_generating` (the skip) |
| `scripts/compare_providers.py` `_report_request` | `ClientRepository(session).get_active()` | `tests/test_compare_providers.py::TestCompareProviders::test_weekly_client_runs_for_the_flagged_client` |
| `cli/commands/time.py` `time_add` | Deleted: the value was never used | none, as AC1.3 states |

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Issue #255's criteria | Edit the issue's acceptance criteria to match the spec's §5 restatement | Made at close-out (`docs/standards/1-workflow.md` §1.2), as the spec's §5 states |
| Service restart | `workmain-notify.service` is stopped | `/closeout`'s restart starts it on `dev` (`.claude/skills/closeout/references/feature.md` step 10) |

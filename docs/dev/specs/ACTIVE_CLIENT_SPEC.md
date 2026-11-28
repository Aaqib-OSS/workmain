# The active client in one home — Spec

**Status:** Draft

**Author:** Spanner

**Date:** 20261127

**Read at:** `bc9e4ee`

**Branch:** `feature/issue-255-active-client-one-home` (base: `dev`, `docs/standards/2-git.md` §2.1)

**Target release:** v1.64.0

**Originating item:** Issue #255

**Design study:** `../design/DESIGN_ACTIVE_CLIENT.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261127 | Ray | Which store survives (study Q1). | Accepted — Option B: `clients.is_active` alone, held to one row by a unique partial index. |
| 20261127 | Ray | Where the one lookup lives (study Q2). | Accepted — (a): `ClientRepository.get_active()`; `clients_service` keeps the set, clear and status use cases. |
| 20261127 | Ray | Which store wins when live's key and flag disagree at the revision (study Q3). | Accepted — the key. DR6 states the consequence. |
| 20261127 | Ray | #300, parked on `workmain/cli/commands/time.py` (study Q4). | Accepted — left parked; out of scope (§1). |
| 20261127 | Ray | The issue's criteria as study §7 restates them, with AC1's check matching the key as a string literal and allowing hits in `workmain/database/models.py`, and AC2 dropping time-entry creation. | Accepted — §5 states them; the issue's criteria are edited at close-out (`docs/standards/1-workflow.md` §1.2). |
| 20261127 | Ray | Spec requirements: state the Q3 consequence; `set_active` unflags in its own UPDATE before it flags, tested; `models.py` declares the index in the revision's commit; the fake refuses a second flagged row and the fallback tests are rewritten, not reseeded. | Accepted — DR4, DR5, DR6, step 1, step 3. |
| 20261127 | Spanner | The index is on the column, `ON clients (is_active) WHERE is_active`, not on the expression `((true))` the study named. Every row it indexes holds `true`, so it admits one row. The column form is the one SQLAlchemy's `Index` declares on `Client` without an expression, which §4.5's model-in-the-same-commit rule needs. | Accepted. |
| 20261127 | Spanner | The revision's data moves are module-level functions, `move_key_to_flag` and `move_flag_to_key`, that `upgrade()` and `downgrade()` call with `op.get_bind()`. A test calls them on `db_session`'s connection. The alternative, running `alembic downgrade` and `upgrade` against `workmain_test`, leaves the test's transaction, which `docs/standards/6-testing.md` §6.1 allows only for tests of the database build. | Accepted. |
| 20261127 | Ray | When `0002` is applied to live relative to the service restart. | Accepted — option (c): the service is stopped before the upgrade and stays stopped until `/closeout`'s restart, which starts a stopped unit (`.claude/skills/closeout/references/feature.md` step 10). No work runs on the application in the window, and it is clear of the T1 and EOD triggers. Step 5 and §7 state it. |
| 20261127 | Caliper | 1, 4, Spec defect, blocking: tests that patch `SystemStateRepository` to stand in for the active client are not in §2 or any step: `tests/test_eod_workflow.py:1045`, `:1079`, `:1102`, `:1110`, `:1168`; `tests/test_ai_arguments.py:187`, `:259`, `:335`, `:360`; `tests/test_report_generator.py:246`; `tests/test_compare_providers.py:161`, `:174`. After step 2, `get_int` patched to 1 finds no client, so the weekly step is skipped and two EOD tests fail; removing `reports.py`'s `SystemStateRepository` import makes the four `reports` patches raise `AttributeError`; and the `None` patches do nothing. | Accepted — §2 adds the sites and the search that finds them; step 2 lists the files and states how each seeds the flag or patches `ClientRepository`. |
| 20261127 | Caliper | 1, Spec defect, blocking: AC1.3's check runs no test of four lookups through their own entry path: `email assign` and `email unassign`, `reports.generate_report_impl`, the EOD weekly guard, and `scripts/compare_providers.py` `_report_request`. | Accepted — AC1.3 names a test per lookup, through its own entry path, that seeds a flagged client and asserts its id is used; step 2 adds the missing ones, and `email_service._draft_recipients`'s client path, which had none either. `time_add` is left out: its read is deleted, so there is no behaviour to test. |
| 20261127 | Caliper | 4, Design gap, blocking: from step 3's commit to step 5's upgrade, the branch's CLI writes only the flag while live's key still names the previous client, so the upgrade's key-wins move (DR6) silently reverts any `clients set active` run in that period; the hold §7 states has no decision behind it. Options: (a) a hold on every `workmain` command against live from step 3's commit through close-out; (b) steps 3–5 in one sitting, with a hold on CLI use from step 3's commit to the upgrade; (c) `set_active` keeps writing the key until step 5. Caliper recommends (b). | Accepted — Ray, 20261127: (b), with the three changes in the next row. |
| 20261127 | Ray | Ruling on Caliper's design gap: (b), changed three ways. (1) The hold covers only `clients set active <name>` and `clients set active internal`, from the repository step's commit to the upgrade. (2) Before it moves anything, `0002`'s upgrade raises and prints both stores when live's key and flag name different clients, instead of applying the key-wins rule; DR6's rule still applies when only one store is set. A test covers the raise. (3) The architecture-map step moves ahead of the repository step, so the sequence is the repository step, then stopping the daemon and applying `0002`, then the results artifact, then `/closeout`. This amends the Q3 row: the key wins only when the flag is unset. | Accepted — DR6, steps 1, 3, 4 and 5, AC2.3, §7. Steps are renumbered: the map is step 3 and the repository is step 4. Rows above cite the old numbers. |
| 20261127 | Spanner | Reading of Ray's change (2) for a key naming a deleted client while a client is flagged: the key is set, because it parses, so the stores name different clients and the upgrade raises. Taking it as unset would leave nothing flagged and silently revert a `clients set active` run after `clients delete --force` of the key's client, the case the check exists to catch. `clients delete --force` of the active client is left out of the hold: after step 4 it leaves a key naming a deleted client with nothing flagged, which DR6 leaves with nothing flagged, the state the branch made. | Accepted — Ray confirmed, 20261127. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: step 3's `test_clients_service.py` bullet leaves the key assertions at `:223`, `:245` and `:259`, which raise `KeyError` once the fake never creates `store['system_state']`; and its added AC2.2 test duplicates `test_deleting_the_active_client_clears_the_context` (`:211`). | Accepted — step 3 removes the three assertions, each beside a flag assertion that stays, and rewrites `:211` without the key in place of a new test. |
| 20261127 | Caliper | 2, Spec defect, non-blocking: DR5. The real repository refuses a second flagged row at its flush; the fake has no flush, so it can refuse only on a later call, and "every method that reads or writes the flag" names no methods. No single action raises on both kinds. | Accepted — DR5 names `set_active`, `clear_active` and `get_active` as the methods that check. The refusal is two tests: the real one flushes a second flagged `Client` (step 1); the fake one seeds two flagged rows and calls `get_active` (step 3). AC2.1 says so. |
| 20261127 | Caliper | 1, Spec defect, non-blocking: AC2.3 asks for one test per DR6 case, and step 1 has no test of `move_flag_to_key` with no client flagged. | Accepted — step 1 adds it. |
| 20261127 | Caliper | Pass at a05c254, full: 40 items checked, 3 blocking, 3 non-blocking. | n/a |

---

## 1. Scope

**In scope:**

- A revision, `0002`, that moves live's active client into `clients.is_active`, deletes the `system_state` key `active_client_id`, replaces `idx_clients_is_active` with a unique partial index, and rewrites the `clients` and `system_state` table comments. The model declares the index.
- `ClientRepository.set_active`, `clear_active` and `get_active` reading and writing the flag alone, and `FakeClientRepository` answering the same.
- Every lookup of the active client in §2 calling `ClientRepository.get_active()`.
- `docs/ARCHITECTURE.md` §2's data line naming the one lookup, and §3's #255 entry removed.
- The tests that seed, read or assert the key, and new tests for each criterion in §5.
- Stopping the service and applying `0002` to live, each an authorization point.

**Out of scope:**

- How `clients set active` targets a client (#251).
- Moving any command's lookup into a service. A command keeps its session and calls `ClientRepository(session).get_active()`. Moving the lookup is the conversion issues' work (#205, #208, #212, #214, #216), and the EOD guard's is #254.
- `reports.py` `get_client_filter` and its parameter name `active_client_id`. It takes an id, and its contract is unchanged.
- `clients_service.delete_client`'s `clear_active()` call before the delete. After step 4 it unflags a row the delete removes, so it does nothing and does no harm.
- #300 (parked), #219 (`client_repository.py` fuzzy search), and the `CHANGELOG.md` history entries that name the key.

## 2. Verified current state

Verified at `bc9e4ee`. The study's findings F1–F20 are the evidence; each row cites the finding and the symbol.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| The flag has a plain partial index; the table comments name both stores. | `0001_baseline.sql:131` (`clients` comment), `:551` (`system_state` comment), `:912` `idx_clients_is_active` (F1, F2) |
| `system_state` is `key varchar(100)`, `value text`, `updated_at`; the key cannot carry a foreign key. | `0001_baseline.sql:540` (F3) |
| `SystemStateRepository.get_int` returns the default for an absent or unparseable value. | `system_state_repository.py:64` `get_int` |
| `ClientRepository.set_active` runs a bulk UPDATE unflagging every flagged row, sets the target's flag through the ORM, and writes the key. `clear_active` unflags and deletes the key. `get_active` reads the key, then the first flagged row. | `client_repository.py:149` `set_active`, `:177` `clear_active`, `:188` `get_active` (F4) |
| `FakeClientRepository` copies all three, and its docstring describes the `clients` row shape. | `fake_unit_of_work.py:171` `FakeClientRepository`, `:277`, `:288`, `:294` (F4) |
| `Client` declares no index and no `__table_args__`. | `models.py:51` `Client` |
| `0001` is the only revision; the test database is built by `alembic upgrade head`. | `versions/0001_baseline.py`; `tests/conftest.py:77` `build_test_database` |
| Lookups of the active client, every one, found by `git grep -nE "[\"']active_client_id[\"']" -- workmain scripts` and `git grep -nE "\.get_active\(" -- workmain scripts`: | |
| — key, then flag | `clients_service.py:101` `_status` (F5) |
| — key, unit-of-work form | `notes_service.py:113` `create_note` (F8) |
| — key, session form | `email_service.py:116` `_draft_recipients`; `cli/commands/email.py:481` `email_assign`, `:516` `email_unassign`; `meetings.py:201` `create`; `reports.py:137` `generate_report_impl`; `slack.py:119` `_resolve_client_channel`, `:248` `slack_status`, `:315` `slack_set_channel`; `eod_workflow.py:884` the weekly-client guard in `_run_report_review_step`; `scripts/compare_providers.py:87` `_report_request` (F12, F13) |
| — key read and never used | `time.py:200` `time_add` (F19) |
| Reads of one loaded client's flag, which stay. | `clients_service.py:79` `_row`, `:129` `get_client`, `:160` `preview_delete`, `:192` `delete_client` (F20) |
| Time entries take the note's client and look up nothing. | `time_entry_service.py:115` `create_time_entry`, `:162` `create_paired_time_entry` (F9) |
| Call sites of `set_active`, `clear_active` and `get_active`, found by `git grep -nE "\.(get_active\|set_active\|clear_active)\b" -- workmain tests automation scripts`; `getattr` references searched, none. | `clients_service.py:101`, `:193`, `:213`, `:218`; `cli/commands/clients.py:189` (the service's `set_active`); tests: `test_client_repository.py`, `test_clients_commands.py:87`, `:102`, `:192`, `test_clients_service.py:240`, `:254`, `:268`, `test_fake_unit_of_work.py:547`–`607`, `test_slack_channel_config.py:35`, `:168` |
| Tests that seed or read the key. | `test_action_executor.py:248`, `:368`; `test_client_repository.py:115`–`170`; `test_clients_commands.py:115`, `:205`; `test_clients_service.py:162`, `:173`, `:217`, `:245`, `:252`, `:265`, `:281`; `test_clockify_service.py:74`, `:111`, `:523`; `test_email_recipients_client.py:210`, `:229`, `:246`; `test_email_service.py:46`, `:125`; `test_fake_unit_of_work.py:553`, `:572`, `:590`, `:600`; `test_meetings_track.py:46`; `test_notes_service.py:64`, `:70`; `test_slack_channel_config.py:67`, `:88`, `:104`, `:127`; `test_time_add.py:85`; `test_time_entry_service.py:137`, `:147`, `:195`, `:322`, `:347`, `:361`, `:404` (F15) |
| Tests that patch `SystemStateRepository` by name to stand in for the active client, found by `git grep -nE "SystemStateRepository\|get_int" -- tests` and reading each hit. | `test_eod_workflow.py:1045`, `:1079`, `:1102`, `:1110`, `:1168` (`patch.object(SystemStateRepository, 'get_int', ...)`); `test_ai_arguments.py:187`, `:335`, `:360` and `test_report_generator.py:246` (`patch('workmain.cli.commands.reports.SystemStateRepository')`); `test_ai_arguments.py:259` (the `system_state_repository` module's class, for `email assign`); `test_compare_providers.py:161`, `:174` (`patch.object(SystemStateRepository, 'get_int', return_value=None)`) |
| Documents that state the key, outside history: `docs/ARCHITECTURE.md:134`, the §3 entry. `CHANGELOG.md:2166`–`2194` is history and stays. | `git grep -nE "active_client_id\|is_active" -- ':!docs/archive' ':!workmain' ':!tests' ':!scripts' ':!docs/dev/design'` |
| Suite at read: 1862 passed, 0 failed, 0 skipped; 1 xfailed, 3 xpassed. | bare `pytest`, `bc9e4ee` |

## 3. Design rules

- **DR1 — One store.** `clients.is_active` is where the active client is stored. Once step 4 is committed, nothing reads or writes the `system_state` key `active_client_id` except revision `0002`.
- **DR2 — One lookup.** Every lookup of which client is active calls `ClientRepository.get_active()`: `uow.clients.get_active()` in the unit-of-work form, `ClientRepository(session).get_active()` in the session-taking form (`docs/standards/4-database.md` §4.1). A read of `is_active` on a client already loaded reads that same store, and stays.
- **DR3 — The database holds it to one row.** A unique partial index, `uq_clients_one_active`, `ON clients (is_active) WHERE is_active`, refuses a second flagged row.
- **DR4 — Unflag before flag.** PostgreSQL checks a non-deferrable unique index row by row, so a single statement that unflags one row and flags another can fail on its order. Every write that moves the flag unflags every flagged row in one statement, then flags the target in a later one. That covers `set_active` and `move_key_to_flag`.
- **DR5 — The fake answers as the database does.** `FakeClientRepository` holds the flag alone, and `set_active`, `clear_active` and `get_active` raise `sqlalchemy.exc.IntegrityError` when the store holds more than one flagged client, so a test that seeds a state the database refuses fails as it would there (`docs/standards/6-testing.md` §6.2).
- **DR6 — The stores are checked, then the key wins once.** The key is set when it parses as `SystemStateRepository.get_int` parses it; absent or unparseable, it is unset. `move_key_to_flag` first checks the two stores, and changes nothing until the check passes:
  - **The key is set and a flagged client has another id**, including when the key names no client: it raises `RuntimeError`, whose message gives the key's value and the id and name of every flagged client. Nothing is moved, and Alembic's one transaction (`workmain/database/migrations/env.py`) leaves the database at `0001`.
  - **The key is set and names an existing client, and no other client is flagged:** that client is flagged, and the key is deleted.
  - **The key is set, names no client, and nothing is flagged:** nothing is flagged, and the key is deleted.
  - **The key is unset:** every flagged client is unflagged, and the key is deleted if present. `clients status` then changes from the flagged client it showed to internal, which is what note writes were already stamping.

  `move_flag_to_key` writes the key from the flagged client, or writes none when none is flagged.
- **DR7 — Read inside the scope.** A caller reads the returned client's `id`, `name` or `slack_channel` while its scope is open, and carries the plain value out (`docs/standards/4-database.md` §4.2).
- **DR8 — Signatures stay.** `set_active(client_id: int) -> Client`, `clear_active() -> None` and `get_active() -> Optional[Client]` keep their signatures and their exceptions. The only public symbols added are the revision's `move_key_to_flag` and `move_flag_to_key`, each taking a SQLAlchemy `Connection` and returning `None`.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Revision `0002` and the model's index | `workmain/database/migrations/versions/0002_active_client_flag.py`, `workmain/database/models.py`, `tests/test_active_client_revision.py`, `tests/test_client_repository.py` |
| 2 | Every lookup calls `get_active()` | `workmain/services/notes_service.py`, `workmain/services/email_service.py`, `workmain/cli/commands/email.py`, `workmain/cli/commands/meetings.py`, `workmain/cli/commands/reports.py`, `workmain/cli/commands/slack.py`, `workmain/cli/commands/time.py`, `workmain/workflows/eod_workflow.py`, `scripts/compare_providers.py`, and the tests listed in step 2, `tests/test_eod_workflow.py`, `tests/test_ai_arguments.py`, `tests/test_report_generator.py` and `tests/test_compare_providers.py` among them |
| 3 | The architecture map | `docs/ARCHITECTURE.md` |
| 4 | The repository and its fake hold the flag alone | `workmain/database/repositories/client_repository.py`, `tests/mocks/fake_unit_of_work.py`, `tests/test_client_repository.py`, `tests/test_fake_unit_of_work.py`, `tests/test_clients_service.py`, `tests/test_clients_commands.py`, `tests/test_notes_service.py` |
| 5 | Service stopped, `0002` applied to live | none (authorization points) |
| 6 | Results artifact | `docs/dev/results/ACTIVE_CLIENT_RESULTS.md` |

### Step 1 — Revision `0002` and the model's index

Written with `alembic revision -m "active client flag" --rev-id 0002` (§4.5); `down_revision` is `"0001"`. The suite stays green: the repository still writes both stores until step 4, and no test holds two flagged rows.

- `move_key_to_flag(connection)`: DR6 and DR4, in this order. Check the two stores and raise where DR6 says; unflag every flagged row; flag the client the key names, if it exists; delete the key.
- `move_flag_to_key(connection)`: DR6's reverse. Upsert the key with the flagged client's id when one is flagged.
- `upgrade()`, in order: `move_key_to_flag(op.get_bind())`; drop `idx_clients_is_active`; create `uq_clients_one_active` (DR3); set the comments below.
- `downgrade()`, in order: drop `uq_clients_one_active`; create `idx_clients_is_active` as the baseline has it (`0001_baseline.sql:912`); `move_flag_to_key(op.get_bind())`; restore both comments as the baseline has them (`:131`, `:551`). Nothing is destroyed, so it reverses rather than raises (§4.5).
- The `clients` comment becomes: `Client records. is_active=TRUE identifies the active client, and the unique partial index uq_clients_one_active allows one such row. NULL client_id on data records = internal/company work. The reserved keyword internal on clients set active clears context. A client named internal cannot be created (CHECK constraint + functional unique index on lower(name)).`
- The `system_state` comment becomes: `General-purpose KV store for WorkmAIn runtime state. String values only — repository layer handles type casting. Keys: notify_method, notify_enabled.`
- `Client` in `models.py` declares `uq_clients_one_active` in `__table_args__`, unique, with `postgresql_where` on `is_active`, in this commit.
- `tests/test_active_client_revision.py`, a `TestMoveKeyToFlag` class calling the functions on `db_session.connection()`. One test for each DR6 case: the key names one client and another is flagged, which raises and changes neither store; the key names no client while a client is flagged, which raises the same way; the key names an existing client and nothing is flagged; the key names the flagged client; the key names no client and nothing is flagged; the key is absent while a client is flagged; the key is unparseable while a client is flagged. Each case that does not raise asserts which client is flagged and that the key is gone. Plus two tests of `move_flag_to_key`: it writes the flagged client's id, and it writes no key when no client is flagged.
- `tests/test_client_repository.py`: a test that flushing a second client with `is_active=True` raises `IntegrityError` (AC2.1).

### Step 2 — Every lookup calls `get_active()`

Each lookup in §2's session-form and unit-of-work rows replaces its key read with `get_active()` (DR2) and reads the id, name or channel inside its scope (DR7). The repository's `get_active` still reads the key, then the flag, so seeding the flag alone or both stores in agreement resolves the same client.

- `notes_service.create_note` stamps `uow.clients.get_active()`'s id, or `None`.
- `slack_set_channel` updates the active client by the id `get_active()` returned; `slack_status` and `_resolve_client_channel` read its name and channel.
- `time_add` loses its unused key read, and its `SystemStateRepository` import if nothing else uses it.
- The `SystemStateRepository` imports each edited function or module no longer uses are removed.
- Tests that seed the key: each test that seeds the key to make a client active seeds the flag instead. It does this through `ClientRepository.set_active` or a `Client` row with `is_active=True` on `db_session`, or a flagged `clients` row in `fake_uow.store`. A test that clears the context calls `clear_active()` instead of deleting the key. The files are `test_action_executor.py`, `test_clockify_service.py` (`_seed_entry` reads `get_active()`), `test_email_recipients_client.py`, `test_email_service.py`, `test_meetings_track.py`, `test_notes_service.py`, `test_slack_channel_config.py`, `test_time_add.py` and `test_time_entry_service.py`, at the lines §2 lists. A test that seeds an unparseable key, such as `test_notes_service.py:70`, seeds no flagged client instead.
- Tests that patch the key's reader, at the lines §2 lists:
  - `test_eod_workflow.py`: each `get_int` patch returning 1 becomes a flagged `Client` seeded on `db_session`. The patch returning `None` (`:1079`) becomes `ClientRepository(db_session).clear_active()`, so the test sets up the state it asserts.
  - `test_compare_providers.py:161`, `:174`: the `None` patches become `clear_active()` on `db_session`.
  - `test_ai_arguments.py:187`, `:335`, `:360` and `test_report_generator.py:246`: these tests mock `get_db`, so no database is reached. Each patch of `workmain.cli.commands.reports.SystemStateRepository` patches the `ClientRepository` name `reports.py` now resolves. `test_ai_arguments.py:259` does the same for `email assign`.
- Entry-path tests (AC1.3). Each seeds a flagged client on `db_session` and asserts that client's id reaches the result, through the lookup's own entry point:
  - `email assign` and `email unassign`, run through `CliRunner` against the test's database, in `test_email_recipients_client.py`: the assignment is written, then removed, at the flagged client's scope.
  - `email_service._draft_recipients`'s client path, in `test_email_service.py`: a client-scoped recipient of the flagged client is among the draft's recipients.
  - `reports.generate_report_impl`, run through `CliRunner` with `get_report_generator` patched and the database real, in `test_report_generator.py`: a template whose `recipient_type` is `client` reaches the generator with the flagged client's id as its client filter.
  - The EOD weekly guard, in `test_eod_workflow.py`: the seeded tests above, and the `clear_active()` test for the skip.
  - `scripts/compare_providers.py` `_report_request`, in `test_compare_providers.py`: with a flagged client, `weekly_client` is not skipped.

### Step 3 — The architecture map

In `docs/ARCHITECTURE.md`:

- §2 Data, replace `` - `workmain/database/repositories/` — one repository per table, named for it. `system_state_repository` is the key-value store. `` with `` - `workmain/database/repositories/` — one repository per table, named for it. `system_state_repository` is the key-value store. `client_repository`'s `get_active()` is the one lookup of the active client, which is stored as `clients.is_active` alone. ``
- §3, delete the paragraph `` **The active client — #255.** It is stored as `clients.is_active` and as `system_state.active_client_id`, and read three ways. ``

### Step 4 — The repository and its fake hold the flag alone

- `ClientRepository.set_active` unflags every flagged row in one bulk UPDATE, then flags the target in a later flush (DR4), and writes no key. `clear_active` unflags and writes no key. `get_active` returns the one flagged client, or `None`. The module docstring states the flag alone and the index that holds it. The `SystemStateRepository` import goes.
- `FakeClientRepository` does the same, and holds DR5. Its docstring states the refusal.
- Tests rewritten, not reseeded:
  - `test_fake_unit_of_work.py`'s `set_active`, `clear_active` and `get_active` tests (lines 540–607) are rewritten for the flag alone. The two fallback tests, `test_get_active_without_a_stored_id_falls_back_to_the_flagged_client` and `test_get_active_falls_back_when_the_stored_id_names_no_client`, are replaced by a test that `get_active` on a store seeded with two flagged clients raises `IntegrityError` (AC2.1; the real side is step 1's test).
  - Add a parametrized test that `set_active` moves the flag from one client to another, and onto the client already flagged, without raising (AC2.4).
  - `test_client_repository.py`: the key assertions (lines 115–122, 146–147, 157, 160) and the stale-key comments in `test_delete_active_client` go.
  - `test_clients_service.py`: the `system_state` seeds go, and `test_falls_back_to_the_flagged_client` is removed. The key assertions at `:223`, `:245` and `:259` go; each sits beside a flag assertion that stays. `test_deleting_the_active_client_clears_the_context` (`:211`) is rewritten without the key, and is AC2.2's `clients status` test.
  - `test_clients_commands.py`: the key assertions at :115 and :205 assert the flag through `get_active()` instead.
  - `test_notes_service.py`: add a test that after the active client is deleted, `create_note` stamps no client (AC2.2).

### Step 5 — Service stopped, `0002` applied to live

In this order:

1. `systemctl --user stop workmain-notify.service`, then `systemctl --user is-active workmain-notify.service`, expecting `inactive`.
2. `alembic current` on live, expecting `0001`.
3. Record `SELECT count(*) FROM clients WHERE is_active` and `SELECT count(*) FROM system_state WHERE key = 'active_client_id'`.
4. `alembic upgrade head`, then `alembic current`, expecting `0002`.
5. Record the same two counts again.

Step 5 runs straight after step 4's commit, and step 6 follows it, then `/closeout`, so the service is stopped for as short a time as the work allows. From step 4's commit until item 4 has run, Ray runs neither `clients set active <name>` nor `clients set active internal`: on `0001`, step 4's `set_active` writes only the flag, and a flag that disagrees with the key makes item 4 raise.

If item 4 raises, live stays at `0001` with nothing moved. Anvil stops and reports the message in chat, not in the results artifact, because it holds client names (`CLAUDE.md` § Client Reference). Ray settles the two stores, and item 4 runs again with his approval. The service stays stopped meanwhile.

The counts go in the results artifact as counts only. The service stays stopped until `/closeout`'s restart, so no old code runs against `0002`.

### Step 6 — Results artifact

`docs/dev/results/ACTIVE_CLIENT_RESULTS.md`, with the table AC1.2 reads.

### Authorization points

- **Step 5, item 1:** stopping `workmain-notify.service`, a change to a live service's run state other than the post-merge restart (`docs/standards/1-workflow.md` §1.4). It stays stopped until `/closeout`'s restart, so the T1–T6 triggers and Slack Socket Mode do not run in between.
- **Step 5, item 4:** applying revision `0002` to the live database (§1.4). It moves the active client into `clients.is_active` as DR6 states, deletes the `system_state` key `active_client_id`, replaces `idx_clients_is_active` with `uq_clients_one_active`, and rewrites two table comments.

Ray approves each when it is about to run.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every lookup of which client is active goes through `ClientRepository.get_active()`, and a read of `is_active` on a client already loaded reads the same column | `git grep -nE "[\"']active_client_id[\"']\|is_active\s*==\|is_active\s*=\s*True\|Client\.is_active" -- workmain scripts tests/mocks` returns hits only in `workmain/database/repositories/client_repository.py`, `workmain/database/models.py` and `workmain/database/migrations/versions/0002_active_client_flag.py` |
| AC1.2 | Every former lookup has been replaced by a call to `get_active()` | Ray reads the results artifact's table of every lookup in §2 and the call that replaced it |
| AC1.3 | Each lookup that changed resolves the active client from the flag alone, through its own entry path. `time_add` is left out: its read is deleted, not replaced | `pytest tests/test_email_recipients_client.py tests/test_email_service.py tests/test_meetings_track.py tests/test_slack_channel_config.py tests/test_report_generator.py tests/test_eod_workflow.py tests/test_compare_providers.py tests/test_action_executor.py tests/test_notes_service.py` passes, with, for each lookup in §2, a test that seeds a flagged client and no key and asserts that client's id is used; the results artifact names the test for each lookup |
| AC2.1 | The database refuses a second active client, and the fake refuses a store that holds one | `pytest tests/test_client_repository.py tests/test_fake_unit_of_work.py` passes, with a test that flushing a second flagged `Client` raises `IntegrityError`, and a test that the fake's `get_active` on a store with two flagged clients raises `IntegrityError` |
| AC2.2 | Deleting the active client leaves `clients status` and note creation on internal | `pytest tests/test_clients_service.py tests/test_notes_service.py` passes, with `test_deleting_the_active_client_clears_the_context`, which asserts that after `delete_client` of the active client `clients_service.get_status` reports internal, and a test that `notes_service.create_note` then stamps no client |
| AC2.3 | The revision moves live's key into the flag as DR6 states, and its downgrade writes the key back | `pytest tests/test_active_client_revision.py` passes, one test per DR6 case, including the two that raise and change neither store, and `move_flag_to_key`'s no-flag case |
| AC2.4 | `set_active` moves the flag between clients under the unique index | `pytest tests/test_fake_unit_of_work.py` passes, with a test that moves the flag from one client to another, and onto the client already flagged, on both kinds |
| AC3.1 | The project states where the active client is stored in one place | Ray reads the `clients` and `system_state` table comments as `0002` sets them, and `docs/ARCHITECTURE.md` §2's data line, which names the one lookup; and `grep -n 'The active client' docs/ARCHITECTURE.md` finds no §3 entry |
| AC4.1 | The full suite passes | a bare `pytest` reports `<n> passed, 0 failed, 0 skipped` |

Each criterion restates one of the issue's, corrected as study §7 states and Ray approved on 20261127. The issue's criteria need the same edit, made at close-out (`docs/standards/1-workflow.md` §1.2).

## 6. Test plan

- **Baseline before this work:** 1862 passed, 0 failed, 0 skipped (and 1 xfailed, 3 xpassed), from a bare `pytest` at `bc9e4ee`.
- **Expected after:** `<n>` passed, 0 failed, 0 skipped, where `<n>` is 1862 plus the tests added, less those removed. The results artifact lists each one.
- **Test files:**
  - `tests/test_active_client_revision.py` (new): the revision's data moves, on `db_session`.
  - `tests/test_client_repository.py`: the database's refusal; the key assertions removed.
  - `tests/test_fake_unit_of_work.py`: fake-against-real for the flag alone and the move between clients, and the fake's refusal.
  - `tests/test_clients_service.py`, `tests/test_notes_service.py`: AC2.2, on `fake_uow`.
  - The step 2 files: reseeded through the flag, the patches of the key's reader replaced, and the entry-path tests AC1.3 names.

## 7. Risks and rollback

- **Live has two flagged rows.** The repository allows that state today through a direct write, and the unique index cannot be built on it. With the key set, any flagged client other than the key's makes `move_key_to_flag` raise (DR6), so the upgrade stops before the index is built. With the key unset, it unflags every row, so the index builds. The counts recorded in step 5 show what the revision moved.
- **The flagged client changes on live.** Under DR6, a live key that is unset leaves no client flagged, so `clients status` reads internal after the upgrade where it showed the flagged client. Note writes were already internal in that state. Ray re-runs `clients set active` if he wants a client active.
- **The window between upgrade and restart.** The daemon loads code at start (`docs/standards/2-git.md` §2.6) and runs `dev` until `/closeout` restarts it. On `0002` its old code would find no key and write Slack captures as internal. Step 5 stops it first, so no old code runs on `0002`. While it is stopped, no trigger fires and no Slack message is received. From step 4's commit to the upgrade, the branch's `clients set active` writes only the flag. Step 5 holds those two commands for that period, and DR6's check makes the upgrade raise instead of reverting a switch the hold missed.
- **Rollback.** Steps 1–4 revert by commit. On live, `alembic downgrade 0001` restores the old index, the key from the flag and both comments, and code before step 4 works on that state. If the work stops after step 5's service stop and before close-out, the service is started again only after live is back at `0001` or the branch has merged. Starting it is Ray's, as an authorization point (§1.4).

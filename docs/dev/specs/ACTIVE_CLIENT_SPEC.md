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
- `clients_service.delete_client`'s `clear_active()` call before the delete. After step 3 it unflags a row the delete removes, so it does nothing and does no harm.
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
| Documents that state the key, outside history: `docs/ARCHITECTURE.md:134`, the §3 entry. `CHANGELOG.md:2166`–`2194` is history and stays. | `git grep -nE "active_client_id\|is_active" -- ':!docs/archive' ':!workmain' ':!tests' ':!scripts' ':!docs/dev/design'` |
| Suite at read: 1862 passed, 0 failed, 0 skipped; 1 xfailed, 3 xpassed. | bare `pytest`, `bc9e4ee` |

## 3. Design rules

- **DR1 — One store.** `clients.is_active` is where the active client is stored. Once step 3 is committed, nothing reads or writes the `system_state` key `active_client_id` except revision `0002`.
- **DR2 — One lookup.** Every lookup of which client is active calls `ClientRepository.get_active()`: `uow.clients.get_active()` in the unit-of-work form, `ClientRepository(session).get_active()` in the session-taking form (`docs/standards/4-database.md` §4.1). A read of `is_active` on a client already loaded reads that same store, and stays.
- **DR3 — The database holds it to one row.** A unique partial index, `uq_clients_one_active`, `ON clients (is_active) WHERE is_active`, refuses a second flagged row.
- **DR4 — Unflag before flag.** PostgreSQL checks a non-deferrable unique index row by row, so a single statement that unflags one row and flags another can fail on its order. Every write that moves the flag unflags every flagged row in one statement, then flags the target in a later one. That covers `set_active` and `move_key_to_flag`.
- **DR5 — The fake answers as the database does.** `FakeClientRepository` holds the flag alone, and every method that reads or writes the flag raises `sqlalchemy.exc.IntegrityError` when the store holds more than one flagged client, so a test that seeds a state the database refuses fails as it would there (`docs/standards/6-testing.md` §6.2).
- **DR6 — The key wins once.** `move_key_to_flag` flags the client the key names when the key parses as `SystemStateRepository.get_int` parses it and names an existing client, unflags every other, and deletes the key. When the key is absent, unparseable or names no client, it leaves no client flagged: `clients status` then changes from the flagged client it showed to internal, which is what note writes were already stamping. `move_flag_to_key` writes the key from the flagged client, or writes none when none is flagged.
- **DR7 — Read inside the scope.** A caller reads the returned client's `id`, `name` or `slack_channel` while its scope is open, and carries the plain value out (`docs/standards/4-database.md` §4.2).
- **DR8 — Signatures stay.** `set_active(client_id: int) -> Client`, `clear_active() -> None` and `get_active() -> Optional[Client]` keep their signatures and their exceptions. The only public symbols added are the revision's `move_key_to_flag` and `move_flag_to_key`, each taking a SQLAlchemy `Connection` and returning `None`.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Revision `0002` and the model's index | `workmain/database/migrations/versions/0002_active_client_flag.py`, `workmain/database/models.py`, `tests/test_active_client_revision.py`, `tests/test_client_repository.py` |
| 2 | Every lookup calls `get_active()` | `workmain/services/notes_service.py`, `workmain/services/email_service.py`, `workmain/cli/commands/email.py`, `workmain/cli/commands/meetings.py`, `workmain/cli/commands/reports.py`, `workmain/cli/commands/slack.py`, `workmain/cli/commands/time.py`, `workmain/workflows/eod_workflow.py`, `scripts/compare_providers.py`, and the tests listed in step 2 |
| 3 | The repository and its fake hold the flag alone | `workmain/database/repositories/client_repository.py`, `tests/mocks/fake_unit_of_work.py`, `tests/test_client_repository.py`, `tests/test_fake_unit_of_work.py`, `tests/test_clients_service.py`, `tests/test_clients_commands.py`, `tests/test_notes_service.py` |
| 4 | The architecture map | `docs/ARCHITECTURE.md` |
| 5 | Service stopped, `0002` applied to live | none (authorization points) |
| 6 | Results artifact | `docs/dev/results/ACTIVE_CLIENT_RESULTS.md` |

### Step 1 — Revision `0002` and the model's index

Written with `alembic revision -m "active client flag" --rev-id 0002` (§4.5); `down_revision` is `"0001"`. The suite stays green: the repository still writes both stores until step 3, and no test holds two flagged rows.

- `move_key_to_flag(connection)`: DR6 and DR4, in this order. Unflag every flagged row, flag the client the key names, delete the key.
- `move_flag_to_key(connection)`: DR6's reverse. Upsert the key with the flagged client's id when one is flagged.
- `upgrade()`, in order: `move_key_to_flag(op.get_bind())`; drop `idx_clients_is_active`; create `uq_clients_one_active` (DR3); set the comments below.
- `downgrade()`, in order: drop `uq_clients_one_active`; create `idx_clients_is_active` as the baseline has it (`0001_baseline.sql:912`); `move_flag_to_key(op.get_bind())`; restore both comments as the baseline has them (`:131`, `:551`). Nothing is destroyed, so it reverses rather than raises (§4.5).
- The `clients` comment becomes: `Client records. is_active=TRUE identifies the active client, and the unique partial index uq_clients_one_active allows one such row. NULL client_id on data records = internal/company work. The reserved keyword internal on clients set active clears context. A client named internal cannot be created (CHECK constraint + functional unique index on lower(name)).`
- The `system_state` comment becomes: `General-purpose KV store for WorkmAIn runtime state. String values only — repository layer handles type casting. Keys: notify_method, notify_enabled.`
- `Client` in `models.py` declares `uq_clients_one_active` in `__table_args__`, unique, with `postgresql_where` on `is_active`, in this commit.
- `tests/test_active_client_revision.py`, a `TestMoveKeyToFlag` class calling the functions on `db_session.connection()`. One test for each case: the key names a client other than the flagged one; the key is absent while a client is flagged; the key names no client; the key is unparseable; the key names the flagged client. Each asserts which client is flagged and that the key is gone. Plus one test that `move_flag_to_key` writes the flagged client's id.
- `tests/test_client_repository.py`: a test that flushing a second client with `is_active=True` raises `IntegrityError` (AC2.1).

### Step 2 — Every lookup calls `get_active()`

Each lookup in §2's session-form and unit-of-work rows replaces its key read with `get_active()` (DR2) and reads the id, name or channel inside its scope (DR7). The repository's `get_active` still reads the key, then the flag, so seeding the flag alone or both stores in agreement resolves the same client.

- `notes_service.create_note` stamps `uow.clients.get_active()`'s id, or `None`.
- `slack_set_channel` updates the active client by the id `get_active()` returned; `slack_status` and `_resolve_client_channel` read its name and channel.
- `time_add` loses its unused key read, and its `SystemStateRepository` import if nothing else uses it.
- The `SystemStateRepository` imports each edited function or module no longer uses are removed.
- Tests: each test that seeds the key to make a client active seeds the flag instead. It does this through `ClientRepository.set_active` or a `Client` row with `is_active=True` on `db_session`, or a flagged `clients` row in `fake_uow.store`. A test that clears the context calls `clear_active()` instead of deleting the key. The files are `test_action_executor.py`, `test_clockify_service.py` (`_seed_entry` reads `get_active()`), `test_email_recipients_client.py`, `test_email_service.py`, `test_meetings_track.py`, `test_notes_service.py`, `test_slack_channel_config.py`, `test_time_add.py` and `test_time_entry_service.py`, at the lines §2 lists. A test that seeds an unparseable key, such as `test_notes_service.py:70`, seeds no flagged client instead.

### Step 3 — The repository and its fake hold the flag alone

- `ClientRepository.set_active` unflags every flagged row in one bulk UPDATE, then flags the target in a later flush (DR4), and writes no key. `clear_active` unflags and writes no key. `get_active` returns the one flagged client, or `None`. The module docstring states the flag alone and the index that holds it. The `SystemStateRepository` import goes.
- `FakeClientRepository` does the same, and holds DR5. Its docstring states the refusal.
- Tests rewritten, not reseeded:
  - `test_fake_unit_of_work.py`'s `set_active`, `clear_active` and `get_active` tests (lines 540–607) are rewritten for the flag alone. The two fallback tests, `test_get_active_without_a_stored_id_falls_back_to_the_flagged_client` and `test_get_active_falls_back_when_the_stored_id_names_no_client`, are replaced by a parametrized test that a second flagged client raises `IntegrityError` on both kinds (AC2.1).
  - Add a parametrized test that `set_active` moves the flag from one client to another, and onto the client already flagged, without raising (AC2.4).
  - `test_client_repository.py`: the key assertions (lines 115–122, 146–147, 157, 160) and the stale-key comments in `test_delete_active_client` go.
  - `test_clients_service.py`: the `system_state` seeds go, and `test_falls_back_to_the_flagged_client` is removed. Add a test that after `delete_client` of the active client, `get_status` is internal (AC2.2).
  - `test_clients_commands.py`: the key assertions at :115 and :205 assert the flag through `get_active()` instead.
  - `test_notes_service.py`: add a test that after the active client is deleted, `create_note` stamps no client (AC2.2).

### Step 4 — The architecture map

In `docs/ARCHITECTURE.md`:

- §2 Data, replace `` - `workmain/database/repositories/` — one repository per table, named for it. `system_state_repository` is the key-value store. `` with `` - `workmain/database/repositories/` — one repository per table, named for it. `system_state_repository` is the key-value store. `client_repository`'s `get_active()` is the one lookup of the active client, which is stored as `clients.is_active` alone. ``
- §3, delete the paragraph `` **The active client — #255.** It is stored as `clients.is_active` and as `system_state.active_client_id`, and read three ways. ``

### Step 5 — Service stopped, `0002` applied to live

In this order:

1. `systemctl --user stop workmain-notify.service`, then `systemctl --user is-active workmain-notify.service`, expecting `inactive`.
2. `alembic current` on live, expecting `0001`.
3. Record `SELECT count(*) FROM clients WHERE is_active` and `SELECT count(*) FROM system_state WHERE key = 'active_client_id'`.
4. `alembic upgrade head`, then `alembic current`, expecting `0002`.
5. Record the same two counts again.

The counts go in the results artifact as counts only (`CLAUDE.md` § Client Reference). The service stays stopped until `/closeout`'s restart, so no old code runs against `0002`.

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
| AC1.3 | Each command whose lookup changed resolves the active client from the flag alone, through its own entry path | `pytest tests/test_email_recipients_client.py tests/test_email_service.py tests/test_meetings_track.py tests/test_slack_channel_config.py tests/test_time_add.py tests/test_action_executor.py tests/test_notes_service.py` passes, each seeding the active client through the flag only |
| AC2.1 | The database refuses a second active client, and the fake refuses it the same way | `pytest tests/test_client_repository.py tests/test_fake_unit_of_work.py` passes, with a test that a second flagged client raises `IntegrityError` on the real repository and on the fake |
| AC2.2 | Deleting the active client leaves `clients status` and note creation on internal | `pytest tests/test_clients_service.py tests/test_notes_service.py` passes, with a test that after `delete_client` of the active client `clients_service.get_status` reports internal, and one that `notes_service.create_note` stamps no client |
| AC2.3 | The revision moves live's key into the flag as DR6 states, and its downgrade writes the key back | `pytest tests/test_active_client_revision.py` passes, one test per DR6 case |
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
  - `tests/test_fake_unit_of_work.py`: fake-against-real for the flag alone, the refusal, and the move between clients.
  - `tests/test_clients_service.py`, `tests/test_notes_service.py`: AC2.2, on `fake_uow`.
  - The step 2 files: reseeded through the flag.

## 7. Risks and rollback

- **Live has two flagged rows.** The repository allows that state today through a direct write, and the unique index cannot be built on it. `move_key_to_flag` runs first and leaves at most one flagged row, so the index builds. The counts recorded in step 5 show what the revision moved.
- **The flagged client changes on live.** Under DR6, a live key that is absent or names no client leaves no client flagged, so `clients status` reads internal after the upgrade where it showed the flagged client. Note writes were already internal in that state. Ray re-runs `clients set active` if he wants a client active.
- **The window between upgrade and restart.** The daemon loads code at start (`docs/standards/2-git.md` §2.6) and runs `dev` until `/closeout` restarts it. On `0002` its old code would find no key and write Slack captures as internal. Step 5 stops it first, so no old code runs on `0002`. While it is stopped, no trigger fires and no Slack message is received. Before step 5, CLI commands run on this branch read the flag, which may name a different client from the key the daemon stamps; Ray holds application work until close-out (Decision Log).
- **Rollback.** Steps 1–4 revert by commit. On live, `alembic downgrade 0001` restores the old index, the key from the flag and both comments, and code before step 3 works on that state. If the work stops after step 5's service stop and before close-out, the service is started again only after live is back at `0001` or the branch has merged. Starting it is Ray's, as an authorization point (§1.4).

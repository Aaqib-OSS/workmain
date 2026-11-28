# The active client in one home — Design Study

**Status:** Active

**Kind:** Design study

**Author:** Spanner

**Date:** 20261127

**Read at:** `bc9e4ee`

**Originating item:** Issue #255

---

## 1. Purpose

The active client is stored as `clients.is_active` and as `system_state.active_client_id`, and readers pick one, the other, or both. This study decides which store survives, where the one reader function lives, and how live data moves to it. It is asked now because five conversion issues (#205, #208, #212, #214, #216) are blocked on it and would otherwise copy the key read into five more services. It also restates the issue, which was written on 20261102, before #266 replaced the numbered migrations and before the standards rewrite of 20261119–20261127.

## 2. Scope of the read

- Source: every hit of `git grep -nE "active_client|is_active|get_active\(|set_active|clear_active" -- workmain tests automation scripts`, and the functions holding each hit.
- Schema: `workmain/database/migrations/versions/0001_baseline.sql`, the `clients` and `system_state` tables, their comments, `idx_clients_is_active`, and every foreign key to `clients(id)`.
- Model and fake: `workmain/database/models.py` `Client`; `tests/mocks/fake_unit_of_work.py` `FakeClientRepository`, `FakeSystemStateRepository`.
- Checks: `automation/architecture_check.py` (reads `docs/ARCHITECTURE.md` §1–§3, so removing the §3 entry changes what it reports), `automation/session_param_check.py`, `.github/workflows/tests.yml` (builds the test schema with `alembic upgrade head`, so a new revision runs in CI).
- Issues: the issue's comments (one, 20261110, on #266), and §1.3's search by file for each file in §3 below. Results are F17.
- Left out: the live database. No live row was read; its current state is Q3's precondition and is checked at the migration step, under its authorization point.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) |
| --- | --- | --- |
| F1 | The `clients` comment names the flag as the identifier: "is_active=TRUE identifies the active client. Only one row may have is_active=TRUE at a time (repository-enforced)." The `system_state` comment lists `active_client_id` as a key. Both live in the baseline revision; `011_clients.sql` no longer exists (#266, issue comment 20261110). | `0001_baseline.sql:131`, `:551` |
| F2 | Nothing in the database holds the flag to one row: `idx_clients_is_active` is a plain partial index. | `0001_baseline.sql:912` |
| F3 | `system_state.active_client_id` is a string in a key-value table, so it cannot carry a foreign key. Deleting the client it names leaves it dangling. | `0001_baseline.sql:551`; `SystemStateRepository.get_int` |
| F4 | `ClientRepository.set_active` and `clear_active` write both stores; `get_active` reads the key, then falls back to the first flagged row. The fake copies all three. | `client_repository.py` `set_active`, `clear_active`, `get_active`; `fake_unit_of_work.py` `FakeClientRepository` |
| F5 | `clients_service.get_status` (`clients status`) resolves through `get_active` (key first, then flag). | `clients_service.py` `_status`, `get_status`, `set_active` |
| F6 | Not in the issue: `clients list`, `clients show`, and the delete guard read the flag through `Client.is_active`. With the key and flag on different clients, `clients list` marks one client and `clients status` names another. | `clients_service.py` `_row`, `get_client`, `preview_delete`, `delete_client`; `cli/commands/clients.py:27`, `:37` |
| F7 | Not in the issue: `delete_client` clears the active context only when the flag is set, so deleting the key's client while another is flagged leaves the key dangling, without `--force`. | `clients_service.py` `preview_delete`, `delete_client` |
| F8 | `notes_service.create_note` stamps the note with the key, read through `uow.system_state`. The issue's line `notes_service.py:78` is now `:113`. | `notes_service.py` `create_note` |
| F9 | Corrects the issue: `time_entry_service` no longer reads the key. `create_time_entry` and `create_paired_time_entry` take `client_id` from the note `create_note` wrote (commits `207e8a0`, `dcdae78`). Clockify pull import does the same (`tests/test_clockify_service.py` `test_s27_import_stamps_the_active_client`). | `time_entry_service.py` `create_time_entry`, `create_paired_time_entry` |
| F10 | Corrects the issue: a key naming a deleted client does not write notes as internal. `create_note` passes the dangling id to `notes.client_id`, which has a foreign key to `clients(id)`, so the insert fails. Only an unset key writes internal. | `notes_service.py` `create_note`; `0001_baseline.sql:1184` `notes_client_id_fkey` |
| F11 | Not in the issue: `slack set channel` with a dangling key raises `AttributeError`, because `ClientRepository.update` returns `None` and the command reads `client.name`. | `cli/commands/slack.py` `slack_set_channel` (line 324) |
| F12 | Session-taking readers of the key, all in code under ARCHITECTURE §3's #198 or #254 entries: `email_service._draft_recipients`; `cli/commands/email.py` `email_assign`, `email_unassign`; `meetings.py` `create`; `reports.py` `generate_report_impl`; `slack.py` `_resolve_client_channel`, `slack_status`, `slack_set_channel`; `time.py` `time_add`; `eod_workflow.py` the weekly-client guard at :884. | Lines 116, 481, 516, 201, 137, 119, 248, 315, 200, 884 |
| F13 | Not in the issue: `scripts/compare_providers.py` `_report_request` reads the key. The issue's checks search `workmain/` only. | `scripts/compare_providers.py:87` |
| F14 | `cli/interface.py`'s reader is gone (#206 closed). | `git grep` returns no hit |
| F15 | Tests that seed or read the key, which change with the store: `test_action_executor`, `test_client_repository`, `test_clients_commands`, `test_clients_service`, `test_clockify_service`, `test_email_recipients_client`, `test_email_service`, `test_fake_unit_of_work`, `test_meetings_track`, `test_notes_service`, `test_slack_channel_config`, `test_time_add`, `test_time_entry_service`. `test_fake_unit_of_work` asserts the fallback behaviour itself (lines 575–607). | the grep in §2 |
| F16 | `docs/ARCHITECTURE.md` §2 already names `clients_service.py` as owner of "the active client"; §3 carries the #255 entry with no "Covers" sentence, so the check reports nothing for it. | `ARCHITECTURE.md` §2 Application, §3 |
| F17 | §1.3 search by file: #251 (`clients_service.py`, `set_active` targeting), #219 (`client_repository.py`, fuzzy search), #205/#208/#212/#214/#216 (blocked by this issue), #254 (`eod_workflow.py`), #198, and others whose subject does not touch the active client. One `parked` issue: #300 (`time.py`, comma-delimited option parsing). | `gh issue list --search "\"<path>\" in:body"`, 20261127 |
| F18 | Suite at read: 1866 tests collected. | `pytest --collect-only -q` |
| F19 | Found 20261127, after the first read: `time add` reads the key into `active_client_id` and never uses it. Both of its paths call `time_entry_service.log_meeting_time` or `log_task_time`, which take the client from the note. | `cli/commands/time.py` `time_add` (line 200) |
| F20 | Found 20261127: `clients_service` reads `is_active` on a client it already holds, in `_row`, `get_client`, `preview_delete` and `delete_client`. That read does not ask which client is active. It reads one row's flag, which under Option B is the one store. | `clients_service.py` lines 79, 129, 160, 192 |

## 4. Governing rules and options

**Governing rules.**

- `docs/ARCHITECTURE.md` §1, One fact, one home. Option C (both stores, kept in step by a trigger) fails it and is dropped.
- `docs/ARCHITECTURE.md` §2: `clients_service.py` owns the active client; one repository per table.
- §4.3: all data access goes through a repository. §4.5: the schema changes through an Alembic revision, with the model in the same commit, and applying it to live is an authorization point (§1.4).
- §1.2: a contract change lists every call site across the whole repository, `scripts/` included.
- §6.2: a fake repository method is tested against the real one.

### Option A — the key survives

- **Approach:** drop `clients.is_active` and its index. Every reader resolves the key through `get_by_id`, and a dangling key reads as internal.
- **Pros:** the readers already read the key.
- **Cons:** a key-value string cannot carry a foreign key (F3), so a dangling id stays possible and every reader must handle it. `delete_client` must remember to clear it. The database cannot refuse a bad state; it can only be read around. `clients list` needs a second read to mark the row.

### Option B — the flag survives, and the database holds it to one row

- **Approach:** a revision replaces `idx_clients_is_active` with a unique partial index (`ON clients ((true)) WHERE is_active`), moves live's key into the flag (Q3), deletes the key, and rewrites both table comments. `ClientRepository.get_active` becomes one query on the flag; `set_active` and `clear_active` write only the flag. Every reader in F8, F12 and F13 calls the one function (Q2).
- **Pros:** the database refuses two active clients. Deleting the active client removes the row, so no dangling reference exists, and F7, F10 and F11 cannot happen. `clients list`, `show`, `status` and note writes read the same column. The `clients` comment already states it; only "repository-enforced" changes.
- **Cons:** a revision applied to live, and its data move. Thirteen test files reseed the active client through the flag (F15).

**Recommendation:** Option B. It is the only option in which the database refuses the divergent states instead of every reader working around them, which is what the issue's AC2 asks for, and §1's rule points to the column that carries a foreign-key-backed identity.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Which store survives? The problem is real: F6, F7, F10 and F11 each show two readers disagreeing, or a write failing, today. Recommended: Option B, the flag, with a unique partial index. | Decision: Option B. The flag survives, held to one row by a unique partial index (Ray, 20261127). |
| Q2 | Where is the one reader function? Real, because the readers sit in both forms (§4.1): `notes_service` holds an entered unit of work, while the readers in F12 and F13 hold a session. (a) `ClientRepository.get_active()`, reached as `uow.clients.get_active()` or `ClientRepository(session).get_active()`; `clients_service` keeps the use cases that set, clear and report it. (b) a `clients_service` function taking a `ClientRepository`, like `_status` does, so every reader asks the §2 owner; it adds a public service function with a repository parameter, a form §4.1 does not name. Recommended: (a). After Option B the lookup is one query with no business rule, data access is the repository's (§4.3), and both forms reach it with no new signature. Either way §2 states the owner in one line (the issue's AC3). | Decision: (a). `ClientRepository.get_active()` is the one reader; `clients_service` keeps the set, clear and status use cases (Ray, 20261127). |
| Q3 | When the revision runs, live's key and flag may disagree. Which wins? Real only if live has diverged; the revision checks. Recommended: the key, because note and time-entry writes have stamped it: the revision flags the client the key names if that client exists, unflags every other, and leaves none flagged when the key is unset or dangling. `downgrade()` writes the key back from the flag, so it is reversible. | Decision: the key wins (Ray, 20261127). |
| Q4 | #300 is parked on `workmain/cli/commands/time.py` (each command splits its comma-delimited options its own way). Fold it in or leave it parked? Real, and unrelated to the active client; folding it would add option-parsing changes to `time add` and other commands. Recommended: leave it parked. | Decision: leave #300 parked (Ray, 20261127). |

## 6. Disposition

- Promoted to:
- Superseded by:

## 7. Corrections to issue #255

The issue was written on 20261102. Ray approved body corrections 1–5 and criterion corrections 1–4 on 20261127. Criteria 1 and 2 are reworded below after his check of 20261127, and that rewording is pending his approval. On his approval Spanner edits the issue body; a criterion changed by the design is restated in the spec's §5 (§1.2).

**Body.**

1. **Structure.** §1.3 now says what an issue holds: Problem, Where, Found, Fix in mind, criteria. The body predates that rule. It gives line numbers where §1.3 asks for symbols, and cites no owner. Proposed: restate it in that form, with Where naming `clients_service.py` (ARCHITECTURE §2) and each symbol in F5–F13.
2. **Migration 011.** `011_clients.sql` is gone (#266). The comment now lives on live and in `versions/0001_baseline.sql`, and a change to it is an Alembic revision (§4.5). Ray's comment of 20261110 records this. The body and AC3 still cite "migration 011".
3. **Reader table.** It is stale. `time_entry_service` no longer reads the key (F9), and `cli/interface.py` is gone (F14). It leaves out `scripts/compare_providers.py` (F13) and the flag readers in `clients_service` (F6).
4. **The defect statement.** A key that names a deleted client makes note writes fail on `notes_client_id_fkey`; they are not written as internal (F10). The statement also misses `clients list` disagreeing with `clients status` (F6), the delete guard leaving a dangling key (F7), and the `slack set channel` crash (F11).
5. **Blocker sentence.** "This issue is blocked by #279" is history: #279 is closed. The fake-parity rule it carries is now §6.2.

**Acceptance criteria.**

1. **AC1's check cannot give its answer.** The pattern includes `get_active\(`, so every caller of the one function is a hit, whichever design is chosen (§1.2: "a criterion's check is one that can produce the answer the criterion states"). It also searches `workmain` only, which misses F13. A criterion that says every *reader* calls `get_active()` is false under Option B, because of F20, and no search can tell those row reads from a lookup. Proposed: "Every lookup of which client is active goes through `ClientRepository.get_active()`, and a read of `is_active` on a client already loaded reads the same column. Checked by `git grep -nE "active_client_id|is_active\s*==|is_active\s*=\s*True|Client\.is_active" -- workmain scripts tests/mocks` returning hits only in `client_repository.py` and the new revision, and by Ray's stated reading of the results artifact's table of every former lookup and the call that replaced it." `is_active\s*=\s*True` catches a `filter_by(is_active=True)` lookup, which the earlier pattern missed.
2. **AC2's states exist only while there are two stores.** Under Option B, the states it lists cannot be written. Every time-entry entry path takes its client from the note `create_note` writes (F9, F19), so a time-entry assertion only tests `create_note` again. Any new lookup in a time-entry path is a hit for AC1's check. Proposed: "The database refuses a second active client, and deleting the active client leaves `clients status` and note creation on internal. Checked by a repository test that a second flagged row raises `IntegrityError`, and a test that after the active client is deleted `clients_service.get_status` and `notes_service.create_note` both resolve internal."
3. **AC3.** Replace "migration 011's comments" with "the `clients` and `system_state` table comments as the new revision sets them".
4. **AC4.** State the §6 evidence form: "`pytest` reporting `<n> passed, 0 failed, 0 skipped`".

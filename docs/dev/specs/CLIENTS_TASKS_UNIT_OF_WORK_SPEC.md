# clients_service and tasks_service on the unit of work — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261116
**Branch:** `feature/issue-279-clients-tasks-unit-of-work` (from `dev`)
**Target release:** set by `/closeout`
**Originating item:** Issue #279
**Design study:** `../design/DESIGN_CLIENTS_TASKS_UNIT_OF_WORK.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261116 | Ray | Branch: `feature/*`. The work changes four application files (`workmain/services/clients_service.py`, `workmain/services/tasks_service.py`, `workmain/cli/commands/clients.py`, `workmain/cli/commands/tasks.py`), over `docs/standards/2-git.md` §2.2's `hotfix/*` limit of 3. | Branch field |
| 20261116 | Ray | Design study Q1: Option A. The recording renderer is `create_autospec(Renderer, instance=True)`, built by a `tests/conftest.py` fixture. | DR12; AC6.1 |
| 20261116 | Ray | Design study Q2–Q4: #265 narrowed to the `calendar` commands; #251 and #255 blocked by #279, with #251's first criterion moved to the end-to-end form; #219 told its literal-match tests go in this spec's contract classes. Done on GitHub 20261116. | No step here |
| 20261116 | Spanner | Issue criterion 6 restated. The issue's check, "every public method name of `Renderer` is a key of the recording renderer's own `__dict__`", tests a hand-written subclass, which Q1 did not choose. What the criterion is for is that no command test can fall through to real printing. The issue body needs the edit at close-out (`docs/standards/1-workflow.md` §1.2). | AC6.1 |
| 20261116 | Spanner | The fakes store rows as dicts and build a new sessionless model instance on each read. `FakeUnitOfWork`'s `copy.deepcopy` rollback raises on a store holding ORM instances (design study F5), so no other storage works. | DR5 |
| 20261116 | Spanner | Rows the faked methods never write (notes, meetings, task_status, and the six tables `count_linked_records` counts) are seeded on the fake side through one public function, `seed_row`. The issue fakes only the methods a converted service calls, which rules out faking `NotesRepository.create` and the other creating methods (design study F8). | DR6, DR13 |
| 20261116 | Spanner | The fakes match `%` and `_` literally, and no test puts either character in search text. #219 removes the wildcard behaviour, and `docs/standards/6-testing.md` §6.2 rule 8 forbids pinning a path an open issue removes (design study F10). | DR7, DR9 |
| 20261116 | Spanner | §5.6 gets both forms side by side, as `docs/standards/4-database.md` §4.1 states them. The calendar, clockify and cost commands still use the session-taking form until #280–#282. The preview sub-bullet changes because `clients delete` follows it. The outside-action sub-bullet is scoped to the session-taking form, because no unit-of-work form for an outside call exists yet (design study F17). | DR17; AC7.1 |
| 20261116 | Spanner | The parity test resolves annotations with `eval_str=True`. `notes_repo.py` lacks `from __future__ import annotations`, so without it no fake of `NotesRepository.get_by_id` written in `fake_unit_of_work.py` could compare equal (§2). The other ways were setting `__signature__` on the fake, which copies the real signature instead of checking it, and adding the future import to `notes_repo.py`, an application file this issue does not otherwise touch. | DR10; AC3.1 |
| 20261116 | Spanner | The census is 16 fake methods, not the issue's 15: `clients_service._not_found` calls `ClientRepository.find_by_name_fuzzy` (design study F3). | DR7; AC3.2 |

---

## 1. Scope

**In scope:**

- `workmain/services/clients_service.py` and `workmain/services/tasks_service.py`: every function moves from the session-taking form to the unit-of-work form (DR1–DR3).
- `workmain/cli/commands/clients.py` and `workmain/cli/commands/tasks.py`: each command builds a `UnitOfWork` per use-case call (DR4).
- `tests/mocks/fake_unit_of_work.py`: fakes of the 16 repository methods the two services call, and `seed_row` (DR5–DR11).
- `tests/conftest.py`: the `recording_renderer` fixture (DR12).
- Tests: `tests/test_fake_unit_of_work.py`, `tests/test_output.py`, `tests/test_clients_service.py`, `tests/test_clients_commands.py`, `tests/test_tasks_service.py`, `tests/test_tasks_commands.py` (new), and `tests/test_task_lifecycle.py` (DR13–DR16).
- `docs/standards/5-cli.md` §5.6: the unit-of-work form (DR17).

**Out of scope:**

- Any other service, command or caller. #280–#282 convert the remaining services that already have commands.
- Client targeting by name or ID, and the picker in `clients` commands: #251.
- The active client stored twice: #255. The fake reproduces today's two reads (DR7).
- Escaping `%` and `_` in substring searches: #219.
- Repositories' public `session` attribute: #283. A fake keeps no session.
- `clients_service.format_active_marker` and `format_yes_no`. They take no session and are not changed.
- `tests/test_task_lifecycle.py`'s `TaskStatusRepository` tests (`TestCreateActive` through `TestQueries`) and `TestTasksGroup`. The first set tests the repository. `TestTasksGroup` tests the group's help, a removed name, and the root group's wiring; none of these is a command's behaviour. Both stay as they are, except for DR16's added test.

## 2. Verified current state

Read on this branch at `82b7fd7`, which differs from `origin/dev` `3fff87a` only in `docs/dev/design/`.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Call sites of every `clients_service` and `tasks_service` function, found by `grep -rnE 'clients_service\|tasks_service' --include=*.py workmain tests automation scripts`. No `getattr`, and no function passed uncalled. | `workmain/cli/commands/clients.py:96`, `:114`, `:136`, `:161`, `:167`, `:195`, `:213`; `workmain/cli/commands/tasks.py:103`, `:122`, `:129`, `:152`, `:175`, `:198`; the tests in §1; `workmain/services/__init__.py:10`, `:13` (an import, not a call). `:27` and `:37` in `clients.py` pass `format_active_marker` and `format_yes_no`, which are out of scope. |
| Neither command group is run as a child process, so `CliRunner` is the only entry path. | `grep -rnE "['\"](tasks\|clients)['\"]" workmain/workflows workmain/utils/self_invoke.py workmain/daemon workmain/integrations workmain/orchestration` returns nothing |
| The session-taking functions: 7 in each service, `_task_for_note` included. | `python3 automation/session_param_check.py workmain/services/clients_service.py workmain/services/tasks_service.py` |
| The repository methods called. `ClientRepository`: `clear_active`, `count_linked_records`, `create`, `delete`, `find_by_name_fuzzy`, `get_active`, `get_by_id`, `get_by_name`, `list_all`, `set_active`. `TaskStatusRepository`: `count_filtered`, `get_by_note_id`, `get_filtered`, `set_completed`, `set_dismissed`. `NotesRepository`: `get_by_id`. | `workmain/services/clients_service.py:80-206`; `workmain/services/tasks_service.py:78-178` |
| Their real behaviour, which each fake reproduces. | `workmain/database/repositories/client_repository.py:48-200`; `task_status_repo.py:87-125`, `:176-270`; `notes_repo.py:113-123` |
| `ClientRepository.set_active`, `clear_active` and `get_active` write, delete and read `system_state.active_client_id` through `SystemStateRepository`. `set_int` stores `str(value)`. | `client_repository.py:172`, `:185`, `:194-200`; `system_state_repository.py:74-76` |
| `tasks_service` reads `ts.note`, `note.created_date`, `note.meeting.id` and `note.meeting.title`. `Note.created_date` is `Computed("(created_at::DATE)")`. | `tasks_service.py:47-55`, `:150-164`; `workmain/database/models.py:208-209`, `:213` `Note.meeting`; `:351` `TaskStatus.note` |
| `FakeUnitOfWork` snapshots its store with `copy.deepcopy`, which raises on a store holding ORM instances. | `tests/mocks/fake_unit_of_work.py` `FakeUnitOfWork.__enter__`; probe 20261116 (design study F5) |
| `TestFakeParity` checks every public function of every class in `FakeUnitOfWork.REPOSITORIES` against the real class with `inspect.signature`, so a new fake added there is covered with no change to which classes it walks. | `tests/test_fake_unit_of_work.py:165-178` |
| `client_repository.py`, `task_status_repo.py`, `system_state_repository.py` and `fake_unit_of_work.py` each have `from __future__ import annotations`; `notes_repo.py` does not. So `NotesRepository.get_by_id`'s return annotation is the object `Optional[Note]`, while a fake in `fake_unit_of_work.py` carries the string `'Optional[Note]'`, and `inspect.signature` compares the two unequal. With `eval_str=True` every public method of the four real repositories resolves, and `FakeSystemStateRepository`'s signatures still equal the real ones. | `grep -c '^from __future__ import annotations'` per file; probe 20261116 |
| `UnitOfWork.REPOSITORIES` names the attributes `clients`, `notes`, `task_status` and `system_state`. | `workmain/services/unit_of_work.py` `UnitOfWork.REPOSITORIES` |
| `UnitOfWork.__enter__` raises `RuntimeError` when entered twice, or inside an open `session_scope()` unless `record=True`. | `workmain/services/unit_of_work.py` `__enter__` |
| `Renderer`'s public methods are `cancelled`, `changed`, `collection`, `nothing_to_do`, `pick`, `record`, `report` and `warning`. `create_autospec(Renderer, instance=True)` passes `isinstance(obj, Renderer)`, the test `pass_renderer` makes, and refuses a call that does not match the real signature. | `workmain/cli/output.py:165-407`, `:410`; probe 20261116 (design study F13) |
| The only SQL-counting test of `TaskStatusRepository.get_filtered` is in the service test file. | `tests/test_tasks_service.py:87-108`; `grep -rln before_cursor_execute tests/` |
| §5.6 states the session-taking form in three places, and no other document states it. | `docs/standards/5-cli.md:99`, `:102`, `:104`; `grep -rnE "it owns\|in one scope\|in a new scope\|in its scope"` over `CLAUDE.md`, `docs/standards`, `docs/ARCHITECTURE.md`, `.claude`, the templates and `.github` |
| Both databases use collation `C.UTF-8`. There, `ORDER BY` on text gives Python's `sorted` order, and `lower()`/`ILIKE` fold case as `str.lower` does. | design study F9 |
| Baseline: `python3 automation/architecture_check.py` prints `New findings: 0` and `PASS`. `pytest --collect-only -q` collects 1707 tests. | Run 20261116 on `3fff87a` |

## 3. Design rules

### Services

- **DR1 — Every public function is a use case.** Its first parameter is `uow: UnitOfWork` (`workmain/services/unit_of_work.py`) in place of `session`. It enters the unit of work once with `with uow:`, and builds and returns its result inside the block (`docs/standards/4-database.md` §4.2). Every other parameter, return type, raised exception and message is unchanged. The functions:
  - `clients_service`: `list_clients(uow)`, `get_client(uow, identifier)`, `add_client(uow, name)`, `preview_delete(uow, identifier, force)`, `delete_client(uow, client_id)`, `get_status(uow)`, `set_active(uow, name)`.
  - `tasks_service`: `list_tasks(uow, status, search, created, limit)`, `list_today(uow, search, today)`, `find_tasks(uow, identifier)`, `get_task(uow, note_id)`, `complete_task(uow, note_id)`, `dismiss_task(uow, note_id)`.
- **DR2 — Operations.** `tasks_service._task_for_note(uow, note_id)` takes a unit of work already entered and never enters it. `set_active` returns the active-client status read inside its own `with uow:` block, through a private operation that `get_status` also uses. A use case never calls another use case, because the second `with uow:` would raise (design study F11). `_resolve` and `_not_found` keep taking a `ClientRepository`, now `uow.clients`.
- **DR3 — Repositories come from the unit of work.** The services use `uow.clients`, `uow.notes` and `uow.task_status`, and construct no repository. Neither module imports `sqlalchemy` or a repository class, except that `clients_service` may keep its import of `ClientRepository` for `RESERVED_NAME`. Each module docstring states the unit-of-work form in place of "Functions take a session".

### Commands

- **DR4 — A command builds a unit of work for each use-case call.** Each command in `clients.py` and `tasks.py` calls its service as `service.fn(UnitOfWork(), ...)` and renders the result. Neither module imports `get_db` or opens a `session_scope()`. `clients delete` calls `preview_delete` with one `UnitOfWork`, renders the preview, asks `click.confirm` unless `--force` is set, then calls `delete_client` with a new one. `tasks`' `_pick_task` calls `find_tasks` with its own. Views, options, arguments, docstrings and every renderer call are unchanged.

### Fakes (`tests/mocks/fake_unit_of_work.py`)

- **DR5 — Storage.** A fake repository is built on the fake unit of work's store, as `FakeSystemStateRepository` is. It keeps rows as dicts keyed by id, under `store['<table name>']`, a dict created on the first write. The table names are `clients`, `notes`, `meetings`, `task_status`, `projects`, `report_recipients`, `reports` and `time_entries`. A method that returns a model builds a new `Client`, `Note`, `Meeting` or `TaskStatus` from the row on every call, with no session, and never stores it.
- **DR6 — `seed_row(store: dict, table: str, **columns) -> int`.** Writes one row into `store[table]` and returns its id. When `id` is not given, it is one more than the table's highest id, or 1. Then it fills the defaults the database or model would fill, for the columns the fakes read:
  - `clients`: `is_active` `False`, `created_at` now (UTC-aware).
  - `notes`: `created_at` now, `created_date` set to `created_at.date()` (the derivation the computed column makes), `tags` `[]`, `content` `''`, and `meeting_id` and `client_id` `None`.
  - `task_status`: `status` `'active'`, `completed_at` and `forwarding_note_id` `None`, `created_at` and `updated_at` now.

  It adds no other defaults to any table. `FakeClientRepository.create` assigns its ids by the same rule.
- **DR7 — `FakeClientRepository(store)`**, with all 10 methods. Each takes the real method's arguments and gives the real method's answer, including its `ValueError` messages word for word:
  - `create` refuses the reserved name, then a case-insensitive duplicate, as the real method does, and writes `is_active False` and `created_at`.
  - `get_by_name` compares `name.strip().lower()` with the stored name lowered.
  - `find_by_name_fuzzy` returns the clients whose lowered name contains `name.strip().lower()`. `list_all` returns every client. Both order by name in Python's `sorted` order, which is the order of the databases' `C.UTF-8` collation. `%` and `_` match literally.
  - `delete` returns `False` for an unknown id. Otherwise it removes the row, sets `client_id` to `None` on every row of the six linked tables that held that id, as `ON DELETE SET NULL` does, and returns `True`.
  - `count_linked_records` counts rows by `client_id` in the six linked tables, with keys in the real method's order.
  - `set_active`, `clear_active` and `get_active` set `is_active` as the real ones do, and write, delete and read `active_client_id` through `FakeSystemStateRepository(store)`. When the key names no client, `get_active` falls back to the flagged client with the lowest id. SQL leaves that order unstated, so no test seeds two flagged clients.
- **DR8 — `FakeNotesRepository(store)`**, with `get_by_id`. It returns a `Note` built from the row, whose `meeting` is a `Meeting` (`id`, `title`) built from `store['meetings']` when `meeting_id` names a row there, and `None` otherwise.
- **DR9 — `FakeTaskStatusRepository(store)`**, with all 5 methods.
  - A returned `TaskStatus` carries the row's columns, and its `note` is built as DR8 builds one.
  - `get_filtered` and `count_filtered` take only task_status rows whose note row exists, as the real inner join does. They filter by `status` unless it is `None` or `'all'`. They filter by `search` as a case-insensitive substring of the note's content, with `%` and `_` literal. They filter by `date_filter` against the note's `created_date`.
  - `get_filtered` orders by the note's `created_at`, newest first, with a `None` first (PostgreSQL's `DESC` puts NULLs first). `limit` 0 means no limit.
  - `set_completed` and `set_dismissed` raise the real `ValueError` for a note with no row. Otherwise they set `status`, `completed_at` and `updated_at` as the real ones do, and return the task.
- **DR10 — Signatures.** Each fake method has the real method's parameter names, defaults and annotations, and a fake has no public method the real repository lacks. `TestFakeParity.test_fake_methods_exist_on_real_with_equal_signatures` compares `inspect.signature(..., eval_str=True)` on both sides, so an annotation written as a string in one module and as an object in the other compares by what it names (§2). `fake_unit_of_work.py` imports every name its annotations use.
- **DR11 — Registration.** `FakeUnitOfWork.REPOSITORIES` gains `'clients': FakeClientRepository`, `'notes': FakeNotesRepository` and `'task_status': FakeTaskStatusRepository`.

### Tests

- **DR12 — The recording renderer.** A `tests/conftest.py` fixture, `recording_renderer`, returns `create_autospec(Renderer, instance=True)`. Its `pick.side_effect` returns `page.rows[0]` when the page has rows and `None` otherwise, which is what the real `pick` returns without asking for one candidate or none. A test that needs another choice sets its own `side_effect`. A test reads what was rendered from the mock's recorded calls.
- **DR13 — Contract tests** go in `tests/test_fake_unit_of_work.py`, one class per fake repository: `TestClientContract`, `TestNotesContract` and `TestTaskStatusContract`. Each is parametrized over `kind` `'real'` and `'fake'`, as `TestSystemStateContract` is. Every one of the 16 methods has at least one test, and the behaviours named in DR7–DR9 each have one, `None`-first ordering excepted, since `Note.created_at` is never null in practice. On the real side a test builds the real repository on `db_session` and seeds the rows the faked methods never write through the repository that owns them, or as ORM models added to `db_session` where no repository creates them, as `tests/test_clients_service.py`'s `_seed_linked` does today. On the fake side it seeds through `seed_row`, and through `FakeClientRepository.create` for clients. No search text contains `%` or `_`.
- **DR14 — Service tests.** `tests/test_clients_service.py` and `tests/test_tasks_service.py` test each public function of DR1 with a `FakeUnitOfWork`, seeded through `seed_row` or the fake `create`, and no `db_session`. Each test asserts the result's fields or the exception raised. A test of a write also asserts the store and `committed`. Each existing test is replaced by a fake-unit-of-work test of the same behaviour, except as DR16 states.
- **DR15 — Command tests.** `tests/test_clients_commands.py` is rewritten, and `tests/test_tasks_commands.py` is new. Each command has one end-to-end test (`docs/standards/6-testing.md` §6.2): `clients add`, `list`, `show`, `delete`, `set active` and `status`, and `tasks list`, `today`, `show`, `complete` and `dismiss`. No flag of these commands calls a different service function.
  - Each test seeds through `db_session` and runs `CliRunner(mix_stderr=False).invoke(<group>, args, obj=recording_renderer)` with nothing patched. `clients delete` answers its prompt through `input=`.
  - Each test asserts the exit code, the values the renderer received, and, for a write, the row read back through `db_session`.
  - `tests/test_task_lifecycle.py` loses its command classes (`TestTasksListCommand`, `TestTasksTodayCommand`, `TestTasksShowCommand`, `TestTasksCompleteDismissCommand`) and the helpers only they use.
- **DR16 — The loading test moves.** `tests/test_tasks_service.py::TestListTasks::test_statement_count_does_not_grow_with_rows` becomes a test in `tests/test_task_lifecycle.py`'s `TestQueries`, in `docs/standards/6-testing.md` §6.2's Repository loading form. It calls `TaskStatusRepository(db_session).get_filtered` and reads `ts.note`'s columns on each row.

### Standards

- **DR17 — §5.6 text.** Step 5 makes these three replacements in `docs/standards/5-cli.md`, and nothing else.
  - `:99`, from "calls a function in `workmain/services/` inside a `session_scope()` it owns, closes the scope, and passes" to: "calls a function in `workmain/services/` in one of the two forms `docs/standards/4-database.md` §4.1 states, and passes". At the end of that bullet, after "with a view it declares as a module constant.", it adds: " In the **unit-of-work form** it builds a `UnitOfWork` (`workmain/services/unit_of_work.py`) for each use-case call and passes it in, and opens no `session_scope()`. In the **session-taking form**, while its service still takes a session, it calls the function inside a `session_scope()` it owns and closes the scope before rendering."
  - `:102`, from "  - A command whose service calls another system reads" to "  - In the session-taking form, a command whose service calls another system reads".
  - `:104`, from "calls the service's preview function in one scope and closes it, then renders the preview." to "calls the service's preview function with a `UnitOfWork` of its own, or in a scope it then closes, and renders the preview." In the same bullet, from "On yes it calls the service's apply function in a new scope and renders its result;" to "On yes it calls the service's apply function with a new `UnitOfWork`, or in a new scope, and renders its result;".

Anything an implementer meets that these rules do not decide is a departure: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The three fake repositories, `seed_row`, their registration in `FakeUnitOfWork.REPOSITORIES`, the parity test's `eval_str=True`, and the contract tests (DR5–DR11, DR13). No service changes. | `tests/mocks/fake_unit_of_work.py`, `tests/test_fake_unit_of_work.py` |
| 2 | The `recording_renderer` fixture, and `TestRecordingRenderer` in `tests/test_output.py` (DR12, AC6.1). | `tests/conftest.py`, `tests/test_output.py` |
| 3 | `clients_service` converted, its commands updated in the same step, and its service and command tests replaced (DR1–DR4, DR14, DR15). | `workmain/services/clients_service.py`, `workmain/cli/commands/clients.py`, `tests/test_clients_service.py`, `tests/test_clients_commands.py` |
| 4 | `tasks_service` converted, its commands updated in the same step, its service tests replaced, its command tests moved to the new file, and the loading test moved (DR1–DR4, DR14–DR16). | `workmain/services/tasks_service.py`, `workmain/cli/commands/tasks.py`, `tests/test_tasks_service.py`, `tests/test_tasks_commands.py`, `tests/test_task_lifecycle.py` |
| 5 | §5.6's unit-of-work form (DR17). | `docs/standards/5-cli.md` |
| 6 | The results artifact. Its §4 Decisions table is joined by three tables: each converted public function with its service tests (AC2.1), each faked method with its contract tests (AC3.2), and each replaced test with the test that replaced it. AC2.1, AC3.2 and AC7.1 are recorded `Not met`, `Awaiting Ray`. | `docs/dev/results/CLIENTS_TASKS_UNIT_OF_WORK_RESULTS.md` |

Steps 3 and 4 change service signatures and update the only callers (§2, first row) in the same step, so each step's commit leaves the suite green (`docs/standards/1-workflow.md` §1.4).

**Owners.** Nothing here adds an application module, public class, public function or table. The changed functions belong to `workmain/services/clients_service.py` and `workmain/services/tasks_service.py`, and the commands to `workmain/cli/commands/<group>.py` (`docs/ARCHITECTURE.md` section 2). The fakes, `seed_row` and the fixture are test files, placed by `docs/standards/7-file-placement.md` §7 and `docs/standards/6-testing.md` §6.2 Repository fake.

### Authorization points

None. No migration, GitHub deletion, merge to `main`, force-push or service run-state change.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No function in `clients_service` or `tasks_service` takes a session | `python3 automation/session_param_check.py workmain/services/clients_service.py workmain/services/tasks_service.py` printing nothing and exiting 0 |
| AC2.1 | Every public function of DR1 is tested at the service with a fake unit of work, and no service test of either module needs the database | `pytest tests/test_clients_service.py tests/test_tasks_service.py` passing; `grep -n db_session tests/test_clients_service.py tests/test_tasks_service.py` returning nothing; and a stated reading by Ray of the results artifact's table pairing each of the 13 functions with its tests |
| AC3.1 | Every fake repository method exists on the real repository with an equal signature, annotations compared by what they name | `pytest tests/test_fake_unit_of_work.py::TestFakeParity` passing, with `FakeUnitOfWork.REPOSITORIES` holding `clients`, `notes`, `task_status` and `system_state`, and its signature test comparing with `eval_str=True` (DR10) |
| AC3.2 | Each of the 16 repository methods the converted services call has a fake that answers as the real method does | `pytest tests/test_fake_unit_of_work.py::TestClientContract tests/test_fake_unit_of_work.py::TestNotesContract tests/test_fake_unit_of_work.py::TestTaskStatusContract` passing, each test run for both `real` and `fake`; and a stated reading by Ray of the results artifact's table pairing each of the 16 methods with its contract tests |
| AC4.1 | Every `clients` and `tasks` command builds a unit of work and passes it in, and none calls a use case inside a `session_scope()` it holds open. CliRunner is the only entry path (§2) | `pytest tests/test_clients_commands.py tests/test_tasks_commands.py` passing, one test per command of DR15, with nothing patched. A use case entered inside an open `session_scope()` raises in `UnitOfWork.__enter__`, and a session-taking call fails on the converted signature. Also `grep -nE 'get_db\|session_scope\|patch' workmain/cli/commands/clients.py workmain/cli/commands/tasks.py tests/test_clients_commands.py tests/test_tasks_commands.py` returning nothing |
| AC5.1 | The architecture check reports no new finding | `python3 automation/architecture_check.py` printing `New findings: 0` |
| AC6.1 | Every public method of `Renderer`, including any added later, records its call on the recording renderer and prints nothing, so a command test cannot fall through to real printing. This restates issue criterion 6 (Decision Log) | `pytest tests/test_output.py::TestRecordingRenderer` passing. Its test calls each public method name of `Renderer`, found with `inspect` at run time, on the fixture's renderer with arguments bound to that method's signature (`None` for each, except an empty `Page` as `pick`'s `page`, which DR12's `side_effect` reads). It asserts that `capsys` captured nothing on stdout or stderr and that the call is in `mock_calls`. |
| AC7.1 | `docs/standards/5-cli.md` §5.6 states the unit-of-work form: the command builds a `UnitOfWork` for each use-case call and passes it to a use case that enters it, and a command asking before it writes previews and applies with separate units of work | A stated reading by Ray of §5.6's converted-command bullet and its preview and outside-action sub-bullets |
| AC8.1 | The full suite passes | `pytest` reporting 0 failed |
| AC8.2 | `TaskStatusRepository.get_filtered` still loads each row's note with it | `pytest tests/test_task_lifecycle.py::TestQueries` passing, including DR16's test |

## 6. Test plan

- **Baseline before this work:** 1707 tests collected at `3fff87a`. Anvil records the full run in the form `<passed> passed, <failed> failed, <skipped> skipped` (`docs/standards/6-testing.md` §6) before step 1.
- **Expected after:** 0 failed, and no skip added. Anvil derives and records the counts.
- `tests/test_fake_unit_of_work.py`: `TestClientContract`, `TestNotesContract`, `TestTaskStatusContract` (DR13). `TestFakeParity` covers the new fakes unchanged.
- `tests/test_output.py`: `TestRecordingRenderer` (AC6.1).
- `tests/test_clients_service.py`, `tests/test_tasks_service.py`: rewritten on the fake (DR14). Behaviour only the database shows is covered by contract tests: unlinking on delete, and the `is_active` fallback in `get_active`.
- `tests/test_clients_commands.py` rewritten, and `tests/test_tasks_commands.py` new (DR15).
- `tests/test_task_lifecycle.py`: command classes removed (DR15), loading test added (DR16).

## 7. Risks and rollback

- **A fake that answers differently from the SQL in a case no contract test covers** lets a service test pass while production differs. The contract tests cover each behaviour DR7–DR9 names. The cases left uncovered on purpose are `%`/`_` (#219) and two flagged clients (DR7).
- **A command test that seeds through `db_session` and runs a command whose unit of work opens its own session.** The issue's probe of 20261116 shows the unit of work sees the seeded rows, even rows only flushed, and finishes first, the last-in, first-out order `docs/standards/6-testing.md` §6.1 requires.
- **Rollback:** each step is one commit and is reverted on its own. Steps 3 and 4 each revert a service, its commands and its tests together. Step 1's fakes are used only from step 3 on.

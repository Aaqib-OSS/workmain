# Unit of Work — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261114
**Branch:** `hotfix/issue-258-unit-of-work` (from `main`)
**Target release:** set by `/closeout`
**Originating item:** Issue #258
**Design study:** `../design/DESIGN_UNIT_OF_WORK.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261113 | Ray | For a converted service the use case owns its transaction: the caller builds a unit of work and passes it in, the use case enters it, and it has no public `commit()`. This replaces, for converted services only, the rule issue #96 set in `docs/standards/4-database.md` §4.1 that the code opening a scope owns it. Answers the design study's draft position (§4, "The transaction belongs to the use case"). | DR4, DR5, DR11 |
| 20261113 | Ray | Design study Q1: the unit of work lives in `workmain/services/unit_of_work.py`, in the application layer. | DR3, DR12 |
| 20261113 | Ray | Design study Q2: the real unit of work holds every repository. | DR3 |
| 20261113 | Ray | Design study Q3: #258 ships a fake of `SystemStateRepository` only, over one shared in-memory store. | DR7, DR8 |
| 20261113 | Ray | Design study Q4: a fake is kept faithful by name-and-signature parity plus behaviour tests run against both the fake and the real repository. | DR9, DR10, DR13 |
| 20261113 | Ray | Design study Q5: `docs/standards/4-database.md` §4.1 states the unit of work, with six points, and an outside-action record is made by the outside-call dependency the caller passes in, never by a unit of work the use case builds. | DR11 |
| 20261113 | Ray | Added to scope: the re-entry guard, the `record` scope parameter, and the open-scope check (design study §4, Added to #258's scope, items 1–3). | DR1, DR2, DR4, DR5 |
| 20261114 | Ray | Added to scope: `automation/session_param_check.py`, with `--exclude`, `<path>::<function>`, and `--package` resolving imports inside functions (design study §4, item 4). | DR14 |
| 20261114 | Spanner | The home of Q4's rule for writing a fake is `docs/standards/6-testing.md` §6.2, beside the Service rule that already names the fake unit of work. Without it the next fake (#279–#282) would follow a rule stated only in an archived study, which `docs/standards/1-workflow.md` §1.5 forbids citing as the basis for a decision. | DR13 |
| 20261114 | Spanner | The open-scope tests must open a bare `session_scope()`, because the check exists for commands that still hold one (DR2). A test that opens it only through a unit of work could pass with the scope state set by the unit of work instead of by `session_scope()`, which would miss exactly that case. `docs/standards/6-testing.md` §6.1 forbids `get_db()` in a test except in `tests/test_database_isolation.py`. Proposed: §6.1 also names `tests/test_unit_of_work.py`, for tests of the scope state and the unit of work. | Approved, Ray 20261114: `tests/test_unit_of_work.py` may call `get_db()` to open a `session_scope()`, for tests of the scope state and the unit of work. DR13, Step 1. |
| 20261114 | Spanner | Misuse raises the built-in `RuntimeError`, not a new class: no surface catches it, and `workmain/services/exceptions.py` holds errors raised to surfaces (`docs/ARCHITECTURE.md` section 2). | DR4, DR5 |
| 20261114 | Ray | Branch: `hotfix/*` stands. The work changes 2 application files (`workmain/database/connection.py`, `workmain/services/unit_of_work.py`), within the limit of 3, and has one root cause: services build their repositories from a session. The session-parameter check is bundled, not a separate concern, because it checks for the form this issue introduces (`docs/standards/2-git.md` §2.2). | Branch field; §4 |
| 20261114 | Ray | AC6–AC10 are added to issue #258's body before Caliper's review, not at close-out: they are added scope, not criteria the design made wrong, so `docs/standards/1-workflow.md` §1.2's close-out edit does not apply to them. Criterion 1's rewording stays a close-out edit. | §5 |
| 20261114 | Ray | Finding: every repository keeps its session in a public `.session` attribute, so "the unit of work exposes no session" (DR3) holds only by convention; AC7.1's test reads `uow.system_state.session`. Outside this spec's scope. | **Not fixed here** (`docs/standards/1-workflow.md` §1.2). Proposed to Ray as an issue; awaiting his decision. If it lands, AC7.1's test reads the scope another way there. |

---

## 1. Scope

**In scope:**

- `workmain/database/connection.py`: the scope state `session_scope()` sets and the function that reads it (DR1, DR2).
- `workmain/services/unit_of_work.py`, new: `UnitOfWork` (DR3–DR6).
- `tests/mocks/fake_unit_of_work.py`, new: `FakeUnitOfWork` and `FakeSystemStateRepository` (DR7, DR8); `tests/mocks/__init__.py` docstring (DR8).
- `automation/session_param_check.py` and `automation/session_param_check_test.py`, new (DR14).
- `docs/ARCHITECTURE.md` sections 1 and 2 (DR12); `docs/standards/4-database.md` §4.1 (DR11); `docs/standards/6-testing.md` §6.1 and §6.2 (DR13).
- Tests: `tests/test_unit_of_work.py` and `tests/test_fake_unit_of_work.py`, new (§6).

**Out of scope:**

- Converting any service, command or caller. Issue #258 says existing services are not converted here; #278, #279–#282, the open #198 command-group children, #254, #261 and #262 convert them.
- A fake of any repository but `SystemStateRepository` (Q3). A fake goes with the service that uses it.
- A unit-of-work form for a savepoint or a session-taking helper (design study F8): the converting issue's.
- The outside-call dependency that records an AI call's cost: #262 and the first conversion that calls a provider (Q5).
- The 12 mid-scope `session.commit()` calls (design study F20): each goes with the issue that converts its command.

## 2. Verified current state

Read on `hotfix/issue-258-unit-of-work`, which differs from `origin/main` `e84f093` only in `docs/dev/design/`.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `session_scope()` gets a session, yields it, commits on normal exit, rolls back on an `Exception` and closes in a `finally`. | `workmain/database/connection.py:73-90` `DatabaseConnection.session_scope` |
| `record_scope()` wraps `session_scope()` and sets `lock_timeout`, so anything `session_scope()` does, `record_scope()` does. | `workmain/database/connection.py:93-104` `record_scope`; `RECORD_LOCK_TIMEOUT = '5s'` at `:21` |
| One `DatabaseConnection` per process, reached through `get_db()`. | `workmain/database/connection.py:115` `db`, `:118` `get_db` |
| The test fixture binds `SessionLocal` to the test's transaction, so a session any code opens through `get_db()` joins it. | `tests/conftest.py:137-146` `_isolated_database` |
| A test may not call `get_db()`, except in `tests/test_database_isolation.py`. | `docs/standards/6-testing.md` §6.1, lines 28 and 33 |
| The 12 repositories, each constructed as `Repository(session)`, and the table each owns: `AiCostRepository` (`ai_costs`), `ClientRepository` (`clients`), `EmailRepository` (`recipients`, `report_recipients`), `GDriveRepository` (`gdrive_uploads`), `MeetingsRepository` (`meetings`), `NotesRepository` (`notes`), `NotificationConfigRepository` (notification keys in `system_state`), `ReportsRepository` (`reports`), `ScheduleExceptionRepository` (`schedule_exceptions`), `SystemStateRepository` (`system_state`), `TaskStatusRepository` (`task_status`), `TimeEntriesRepository` (`time_entries`). | `grep -n "def __init__" workmain/database/repositories/`; `__tablename__` in `workmain/database/models.py`; `session.query(<Model>)` per repository |
| `SystemStateRepository` has seven public methods: `get(key) -> Optional[str]`, `set(key, value) -> None` (upsert), `delete(key) -> bool`, `get_bool(key, default=False) -> bool` (`'true'` case-insensitive after strip), `set_bool(key, value)` (`'true'`/`'false'`), `get_int(key, default=None) -> Optional[int]` (default when absent or unparseable), `set_int(key, value)` (stored as `str`). | `workmain/database/repositories/system_state_repository.py:22-76` |
| No `UnitOfWork` and no `unit_of_work` module exist; the only matches are two test class names. | `grep -rnE 'UnitOfWork\|unit_of_work' workmain tests automation --include=*.py`: `tests/test_time_add.py:202` `TestTimeAddUnitOfWork`, `tests/test_notes_log.py:194` `TestNotesLogUnitOfWork` |
| **Call sites of `session_scope()`** (DR1 adds a side effect to it): 122 in 20 files outside `connection.py`. None reads the scope state, because nothing exists to read it until `UnitOfWork` (DR4); their behaviour is unchanged. Tests that replace `get_db()` or `session_scope` with a mock (`tests/test_calendar.py:183`, `tests/test_clients_commands.py:165`, `tests/test_eod_task_matching.py:217`, `tests/test_gdrive.py:241`, `tests/test_orchestration.py:348`) never reach the scope state and never enter a unit of work. | `grep -rnE "session_scope\(" workmain --include=*.py` excluding `connection.py`; `grep -rnE "session_scope" tests/*.py` |
| Threads: `workmain/integrations/slack/slack_eod.py:344` and `workmain/integrations/slack/socket_client.py:129`, `:142` start threads. A Python 3.12 thread starts with a fresh context, so a `ContextVar` set in one thread is unset in another. | the cited lines; Python 3.12 `threading.Thread` runs its target in a new empty context |
| `automation/architecture_check.py` places a module by map section 1's Packages column and requires a map section 2 line for each module; `workmain/services/` is covered whole; a surface may import the application layer. | `automation/architecture_check.py` `read_layers`, `layer_of`, `check_layers`, `check_ownership`; baseline run prints `PASS` |
| Text this spec changes: map section 1 Surfaces row's Rule ("a surface owns its session through `workmain/database/connection.py`"), map section 2 `connection.py` line ("`get_db()` and `session_scope()`, the only way to get a session."), §4.1 bullets "The code that opens a scope owns its unit of work" and "The owner commits before it waits", §6.2 Service bullet. | `docs/ARCHITECTURE.md:15`, `:86`; `docs/standards/4-database.md:16`, `:17`; `docs/standards/6-testing.md:70` |
| Session-taking functions in `workmain/services/` today: 41. | AST walk for a parameter named `session` or annotated `Session` (design study F26) |
| `workmain/workflows/eod_workflow.py` imports `ScheduleService` only inside functions. | `workmain/workflows/eod_workflow.py:505`, `:727` |
| Baseline suite: 1635 passed, 0 failed, 0 skipped. | `CHANGELOG.md:22` |

## 3. Design rules

- **DR1 — `session_scope()` records that it is open.** `workmain/database/connection.py` gains a module-level `contextvars.ContextVar[bool]` with default `False`. `session_scope()` sets it to `True` once it has a session, before it yields, and resets it with the token `set()` returned, in a `finally` that runs after the session is closed. A reset by token restores the value from before this scope, so a scope opened inside another leaves `True` behind when it closes, and an `Exception`, `SystemExit` or `KeyboardInterrupt` leaving the block clears it as a normal exit does. `record_scope()` gets the same behaviour by wrapping `session_scope()`, and needs no change.
- **DR2 — One function reads it.** `connection.py` adds `def scope_open() -> bool`, returning the variable's value on the calling thread. Owner: `workmain/database/connection.py` (DR12). Nothing else reads or sets the variable.
- **DR3 — `UnitOfWork` holds every repository.** `workmain/services/unit_of_work.py` defines `class UnitOfWork`, owner `workmain/services/unit_of_work.py` (DR12).
  - `REPOSITORIES` is a class attribute mapping each attribute name to its repository class, one entry per repository in §2: `ai_costs`, `clients`, `email`, `gdrive_uploads`, `meetings`, `notes`, `notification_config`, `reports`, `schedule_exceptions`, `system_state`, `task_status`, `time_entries`.
  - On entry, each is built from the unit of work's session as `cls(session)` and set as an attribute of that name. On exit, every one is removed, so a repository used after exit raises `AttributeError`.
  - It exposes no session, and has no public `commit()`, `rollback()` or `begin_nested()`.
- **DR4 — It is entered once, and only outside an open `session_scope()`.** `__init__(self, record: bool = False)`. `__enter__` returns the unit of work, and checks two things before opening anything:
  - **Re-entry guard:** it raises `RuntimeError` when this instance has been entered before, whether or not it has exited.
  - **Open-scope check:** when `record` is `False`, it raises `RuntimeError` when `scope_open()` is `True`. Because the unit of work's own scope is a `session_scope()`, this also catches a unit of work entered inside another one: a use case nested in another on a fresh unit of work, which the re-entry guard cannot see. A `record=True` unit of work does not check it.
  - An `__enter__` that raises leaves the instance unentered and opens no session. Each message names the rule broken.
- **DR5 — Its exit is `session_scope()`'s.** With `record=False` it opens `get_db().session_scope()`; with `record=True`, `get_db().record_scope()`. `__exit__` hands the exit to that scope: a normal exit commits; an `Exception` rolls back and propagates; a `BaseException` that is not an `Exception` closes the session without commit or rollback (`docs/standards/4-database.md` §4.1). It never suppresses an exception.
- **DR6 — No caller in `workmain/` changes.** No command, service, workflow or daemon module builds or receives a `UnitOfWork` in this spec. Its only entry path is construction in a test.
- **DR7 — `FakeUnitOfWork` stands in for it.** `tests/mocks/fake_unit_of_work.py` defines `class FakeUnitOfWork`, with `__init__(self, record: bool = False, store: Optional[dict] = None)`.
  - `store` is the in-memory database: a dict keyed by table name, shared by every fake repository a fake unit of work builds (design study F12). A test that passes one store to several fake units of work sees each one's committed writes in the next. With no store given, it starts empty.
  - `REPOSITORIES` maps attribute names to fake repository classes, the same names as DR3: `system_state` → `FakeSystemStateRepository`. They are built from the store on entry and removed on exit.
  - The re-entry guard of DR4, with the same message. It has no open-scope check: there is no scope to check.
  - On entry it keeps a copy of the store. A normal exit sets `committed = True`. An `Exception` restores the copy, sets `rolled_back = True` and propagates. Any other `BaseException` restores the copy, as the real unit of work discards its uncommitted writes, sets neither flag and propagates. `committed` and `rolled_back` start `False`.
  - It holds no session and needs none: a test of a fake takes no `db_session`.
- **DR8 — `FakeSystemStateRepository` answers as the real one does.** `__init__(self, store: dict)`, holding its rows in `store["system_state"]`, a dict of key to value created on first use. It has the seven public methods of §2 with the same names, parameters, defaults and results; whether it reuses the real class's derived methods is the implementer's. `tests/mocks/__init__.py`'s docstring becomes one sentence that names no module: fakes that tests use in place of external services.
- **DR9 — A fake has nothing the real one lacks.** A test asserts that every name in `FakeUnitOfWork.REPOSITORIES` is in `UnitOfWork.REPOSITORIES`, and that every public method of each fake repository class, `__init__` aside, exists on the real class it stands for with an equal `inspect.signature`.
- **DR10 — A fake method's behaviour is tested against both.** Each `FakeSystemStateRepository` method is covered by tests in one class parametrized over the real repository on `db_session` and the fake, so the same assertions run against each and a fake that answers differently from the SQL fails.
- **DR11 — §4.1 states the unit of work.** `docs/standards/4-database.md` §4.1 states, in this order and in addition to its current content:
  1. Two forms side by side. The **session-taking form**: the code that opens a `session_scope()` owns it, and code handed the session never commits it (the current bullets, which stay and apply to that form only). The **unit-of-work form**: a caller builds a `UnitOfWork` (`workmain/services/unit_of_work.py`) and passes it to a use case; the use case enters it with `with uow:`, and on exit it commits after a normal return and rolls back on an `Exception`. It has no public `commit()`.
  2. A use case enters a unit of work. An operation takes one already entered, and never enters or commits it.
  3. Workflows, orchestration and the daemon call use cases: they build one unit of work per call and never enter one themselves. A use case never builds a unit of work; only its caller does.
  4. The wait rule, for the unit-of-work form: a use case holds no write across an outside call.
  5. A use case that decides not to go ahead raises, so a normal return always means its writes are wanted.
  6. A use case is not called inside an open `session_scope()`, except on a `UnitOfWork(record=True)` under §4.3's conditions for an outside-action record; `UnitOfWork.__enter__` raises otherwise. A use case that makes an outside call receives the outside-call dependency from its caller, and that dependency makes its own §4.3 record; the use case never builds a unit of work for it.
  - The §4.1 code example gains the unit-of-work form beside the existing one.
- **DR12 — The map names the owners.** In `docs/ARCHITECTURE.md`:
  - Section 1, Surfaces row, Rule column: "a surface owns its session through `workmain/database/connection.py`" becomes "a surface builds a unit of work (`workmain/services/unit_of_work.py`) and passes it to a use case, or, while it calls a service that still takes a session, owns that session through `workmain/database/connection.py`". The Packages column is unchanged.
  - Section 2, Application, after the `exceptions.py` line: "- `workmain/services/unit_of_work.py` — the unit of work: the transaction a use case enters, and the repositories it holds."
  - Section 2, Data, the `connection.py` line becomes: "- `workmain/database/connection.py` — `get_db()`, `session_scope()` and `record_scope()`, the only way to get a session, and `scope_open()`, whether a `session_scope()` is open on the calling thread."
- **DR13 — §6.1 and §6.2 state how a fake is tested.**
  - §6.2, Service bullet, after its last sentence: the fake unit of work is `tests/mocks/fake_unit_of_work.py`'s `FakeUnitOfWork`.
  - §6.2 gains a bullet after Service, **Repository fake**: a fake repository goes in `tests/mocks/fake_unit_of_work.py` with the service that first needs it, and fakes only the methods its services call. A test asserts that each fake method exists on the real repository with an equal signature, and each fake method's behaviour tests run in one class parametrized over the real repository on `db_session` and the fake.
  - §6.1, the `tests/test_database_isolation.py` bullet, gains `tests/test_unit_of_work.py`: its tests may call `get_db()` to open a `session_scope()`, because they test the scope state and the unit of work.
- **DR14 — One script lists session parameters.** `automation/session_param_check.py`, owner `automation/` (`docs/standards/7-file-placement.md` §7; the map covers the application only).
  - A session parameter is one named `session`, or one whose annotation's source text contains `Session`. It is found on any function or method, at any depth.
  - Arguments: one or more module paths, each optionally narrowed as `<path>::<name>` to the functions and methods of that name; or `--package <dir>`, which resolves every import of a `workmain/services/` module made anywhere in the package's modules, at module level or inside a function (`import workmain.services.x`, `from workmain.services.x import y`, `from workmain.services import x`), and checks those modules whole; and `--exclude <path>`, repeatable, which leaves a module out.
  - Output: one line per finding, `<path>:<line> <name>`, sorted by path and line. Exit `0` when there are none, `1` when there are any, `2` on a usage error or a path that does not exist.

Anything a step meets that these rules do not decide is a departure: stop as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

Each step ends with a commit and leaves the suite green.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | **The scope state.** DR1, DR2. DR13's §6.1 sentence. `TestScopeState` in `tests/test_unit_of_work.py` (§6). | `workmain/database/connection.py`, `docs/standards/6-testing.md`, `tests/test_unit_of_work.py` |
| 2 | **The unit of work.** DR3–DR6, and DR12's three map changes in the same commit, so `automation/architecture_check.py` finds the new module owned. The remaining classes of `tests/test_unit_of_work.py` (§6). | `workmain/services/unit_of_work.py`, `docs/ARCHITECTURE.md`, `tests/test_unit_of_work.py` |
| 3 | **The fake.** DR7–DR10. `tests/test_fake_unit_of_work.py` (§6). | `tests/mocks/fake_unit_of_work.py`, `tests/mocks/__init__.py`, `tests/test_fake_unit_of_work.py` |
| 4 | **The session-parameter check.** DR14, with its tests. | `automation/session_param_check.py`, `automation/session_param_check_test.py` |
| 5 | **The standards.** DR11, and DR13's two §6.2 changes. | `docs/standards/4-database.md`, `docs/standards/6-testing.md` |
| 6 | **Results artifact**, `docs/dev/results/UNIT_OF_WORK_RESULTS.md`. | `docs/dev/results/UNIT_OF_WORK_RESULTS.md` |

Application files changed: `workmain/database/connection.py` and `workmain/services/unit_of_work.py`, within `hotfix/*`'s limit (`docs/standards/2-git.md` §2.2).

### Authorization points

None. No migration, no GitHub object deletion, no merge to `main`, no force-push, no change to a live service's run state.

## 5. Acceptance criteria

Issue #258's criteria are AC1–AC5. AC6–AC10 are the scope Ray added (Decision Log, 20261113 and 20261114), carried in the issue body as its criteria 6–10. At close-out the issue body's criterion 1 is edited to read "holds the repositories and its transaction", not "the commit": there is no public `commit()` (DR3; `docs/standards/1-workflow.md` §1.2).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The application has a unit of work that holds every repository and its transaction, and exposes neither a session nor a public commit | `pytest tests/test_unit_of_work.py::TestUnitOfWork` passing, with tests that each `REPOSITORIES` entry is an attribute built on the unit of work's session while it is entered and absent after, and that it has no `session`, `commit`, `rollback` or `begin_nested` attribute |
| AC1.2 | The unit of work's owner, and the new reader of the scope state, are named in the map, and a surface's rule says how it reaches a use case | A stated reading by Ray of `docs/ARCHITECTURE.md` section 1's Surfaces row and section 2's `unit_of_work.py` and `connection.py` lines, for whether each names the module that owns the thing it lists |
| AC2.1 | A fake unit of work in `tests/` keeps rows in memory and can stand in for the real one: what a repository is given it returns, and a normal exit is recorded as a commit | `pytest tests/test_fake_unit_of_work.py::TestFakeUnitOfWork` passing, with no test in that class taking `db_session` |
| AC2.2 | The fake discards a failed unit of work's writes, as the real one does | A `TestFakeUnitOfWork` test that writes, raises inside the fake, and finds the store as it was, `rolled_back` true and `committed` false |
| AC2.3 | The fake has nothing the real one lacks | `pytest tests/test_fake_unit_of_work.py::TestFakeParity` passing (DR9) |
| AC2.4 | The fake system-state repository answers as the real one does | `pytest tests/test_fake_unit_of_work.py::TestSystemStateContract` passing, every test running once with the real repository and once with the fake (DR10) |
| AC3.1 | The real unit of work commits through its session on a normal exit | A `tests/test_unit_of_work.py` test that writes through `uow.system_state`, exits normally, and reads the row through `db_session` |
| AC3.2 | The real unit of work rolls back on an exception and lets it propagate | A test that writes, raises inside the unit of work, sees the exception outside it, and finds no row through `db_session` |
| AC3.3 | The real unit of work discards its writes when a `BaseException` that is not an `Exception` leaves it | A test that writes, raises `KeyboardInterrupt` inside it, catches it outside, and finds no row through `db_session` |
| AC4.1 | `architecture_check` reports no new finding | `python3 automation/architecture_check.py` printing `New findings: 0` |
| AC5.1 | The full suite passes | `pytest` reporting 0 failed |
| AC6.1 | A unit of work cannot be entered twice, nested or after it has exited, and a refused entry opens no session | `pytest tests/test_unit_of_work.py::TestReentryGuard` and the guard tests in `TestFakeUnitOfWork` passing: entering an entered instance raises, entering an exited one raises, and an instance refused by the open-scope check enters once the scope has closed |
| AC7.1 | A record unit of work runs on `record_scope()`, and the default one on `session_scope()` | `pytest tests/test_unit_of_work.py::TestRecordUnitOfWork` passing: inside `UnitOfWork(record=True)`, `SHOW lock_timeout` executed on a repository's session (`uow.system_state.session`) returns `RECORD_LOCK_TIMEOUT`; inside `UnitOfWork()` it returns the server default, not `RECORD_LOCK_TIMEOUT` |
| AC8.1 | No unit of work on `session_scope()` is entered inside an open `session_scope()`, on either path that reaches one: a caller's bare `session_scope()`, and another unit of work | `pytest tests/test_unit_of_work.py::TestOpenScopeCheck` passing: entering inside an open `get_db().session_scope()` raises; entering inside an entered `UnitOfWork()` raises; entering after the scope has closed does not; entering `UnitOfWork(record=True)` inside an open scope does not |
| AC8.2 | The scope state is set exactly while a `session_scope()` is open, on its own thread, however the scope exits | `pytest tests/test_unit_of_work.py::TestScopeState` passing: `scope_open()` is true inside `session_scope()` and `record_scope()`, false before and after; a nested scope leaves it true when it closes; it is false after an `Exception` and after a `KeyboardInterrupt` leaves the scope; it is false on another thread while a scope is open on this one |
| AC9.1 | The session-parameter check finds every session parameter in the modules it is given, and none it is not | `pytest automation/session_param_check_test.py` passing, covering: a parameter named `session`, one annotated `Session`, a method's; `<path>::<name>`; `--exclude`; `--package` resolving a module-level import and an import inside a function; exit `0`, `1` and `2` |
| AC9.2 | The check sees today's session-taking services | `python3 automation/session_param_check.py workmain/services/*.py --exclude workmain/services/unit_of_work.py` exiting `1` and printing the 41 functions the design study's F26 walk counts, and `--package workmain/workflows` including `workmain/services/schedule_service.py:36 __init__`, reached only through `eod_workflow.py`'s function-level imports |
| AC10.1 | `docs/standards/4-database.md` §4.1 states the unit-of-work form so that a converting author needs nothing else to call a use case correctly | A stated reading by Ray of §4.1 for the six points DR11 lists |
| AC10.2 | `docs/standards/6-testing.md` §6.2 tells a test author where the fake unit of work is and how a fake repository is written and tested | A stated reading by Ray of §6.2's Service and Repository fake bullets |

## 6. Test plan

- **Baseline before this work:** 1635 passed, 0 failed, 0 skipped (`CHANGELOG.md:22`).
- **Expected after:** 1635 plus the new tests below, 0 failed, 0 skipped. `pytest automation/` is a separate suite (`docs/standards/6-testing.md` §6) and is reported separately.
- `tests/test_unit_of_work.py`:
  - `TestScopeState` (Step 1): true inside `session_scope()`; true inside `record_scope()`; false before and after; a nested scope restores true; false after an `Exception`; false after a `KeyboardInterrupt`; false on another thread, which only calls `scope_open()` and does no database work (`docs/standards/6-testing.md` §6.1 keeps database work on the test's thread).
  - `TestUnitOfWork` (Step 2): every `REPOSITORIES` entry built on the unit of work's session while entered; absent after exit; no session or commit attribute; commit on a normal exit; rollback on an `Exception`, which propagates; writes discarded on a `KeyboardInterrupt`.
  - `TestReentryGuard` (Step 2): entered twice raises; entered after exit raises; refused by the open-scope check, then entered after the scope closes.
  - `TestOpenScopeCheck` (Step 2): inside a bare `session_scope()` raises; inside an entered `UnitOfWork()` raises; after the scope closes enters; `record=True` inside an open scope enters.
  - `TestRecordUnitOfWork` (Step 2): `lock_timeout` is `RECORD_LOCK_TIMEOUT` inside `UnitOfWork(record=True)` and is not inside `UnitOfWork()` (AC7.1), in two separate tests: under the fixture a unit of work's commit releases a savepoint, and `SET LOCAL` outlives a released savepoint until the test's transaction ends, so a second unit of work in the same test would read the first's setting. A record's survival of a later failure is not tested here: under the fixture a record committed inside another session's open transaction is discarded by that rollback (`docs/standards/6-testing.md` §6.1), and the record path's survival is tested at the function that writes it, by the issue that converts one.
- `tests/test_fake_unit_of_work.py` (Step 3):
  - `TestFakeUnitOfWork`, no `db_session`: a value set through `uow.system_state` is returned by it; a normal exit sets `committed`; an `Exception` restores the store and sets `rolled_back`; a `KeyboardInterrupt` restores the store and sets neither; one store shared by two fake units of work carries the first's committed write to the second; the re-entry guard's two cases.
  - `TestFakeParity`: DR9's two assertions.
  - `TestSystemStateContract`, parametrized over real and fake: each of the seven methods, including `get` of an absent key, `set` overwriting, `delete` of a present and an absent key, `get_bool` of `'True '`, of another value and of an absent key with a default, and `get_int` of an unparseable value and of an absent key with a default.
- `automation/session_param_check_test.py` (Step 4): AC9.1's cases, each on a module written to `tmp_path`.

## 7. Risks and rollback

- **The scope state is left set after a scope closes.** Every later unit of work on that thread would then be refused. DR1's reset by token in a `finally` prevents it, and AC8.2 checks each way out. Blast radius while no caller builds a unit of work: tests only.
- **A scope opened in one thread and closed in another** would make the token reset raise. No `session_scope()` crosses threads today: each is a `with` block on one thread.
- **A fake that drifts from the real repository** passes service tests the real code would fail. DR9 and DR10 catch drift in the methods faked; a method not faked raises `AttributeError` in the test.
- **Rollback:** each step is one commit; reverting Steps 5, 4, 3, 2, 1 in that order removes the change. No schema, no data and no caller depends on it until #278 and #279–#282 land.

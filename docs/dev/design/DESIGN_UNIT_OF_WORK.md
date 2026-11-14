# Unit of Work — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261113
**Originating item:** Issue #258

---

## 1. Purpose

Every service function in `workmain/services/` takes a SQLAlchemy `Session` and builds the repositories it needs from it, so a test of a service needs a real database session. Issue #258 adds a unit of work: one object a service receives, holding its repositories and its transaction, with a real form wrapping a session and a fake form in `tests/` holding repositories in memory. Services converted under #198 from #206 on take it; existing services are not converted here. This study measures what the unit of work must fit and sets out the choices whose answers change the spec. Ray answered Q1–Q7 and added scope on 20261113 (§4, §5).

## 2. Scope of the read

Read at `origin/main` `e84f093`, 20261113:

- `docs/ARCHITECTURE.md` sections 1–3; `automation/architecture_check.py` (`read_layers`, `layer_of`, `check_layers`, `check_ownership`), and a run of it.
- `docs/standards/` §4.1–§4.3, §6.1, §6.2, §3.8, §7.
- `workmain/database/connection.py`, `workmain/database/models.py` imports, every `workmain/database/repositories/*.py` constructor and public-method count, `ClientRepository` and `SystemStateRepository` in full.
- Every module in `workmain/services/`: its session use, the repositories it builds, and every `return` that is not its function's last statement.
- Every call site of `notes_service.create_note`, `time_entry_service.create_time_entry`, `create_paired_time_entry` and `link_condensed_note`; every `session.commit()` and `session_scope(` outside `workmain/database/connection.py`; every service call from `workmain/orchestration/`, `workmain/workflows/`, `workmain/daemon/` and `workmain/ai/`.
- `workmain/ai/note_condenser.py` `condense_meeting`.
- `workmain/cli/interface.py` `status` and `workmain/cli/commands/clients.py`, as the shape of a command that calls a service.
- `tests/conftest.py` `_isolated_database` and `db_session`; `tests/mocks/`.
- Issues #198 and its children, #206, #254, #261 and #262: bodies and criteria.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | Every service function takes a `Session` and builds repositories from it; none commits, rolls back or opens a session, except the outside-action records in F7. The command that opens the scope owns it. | `workmain/services/clients_service.py:4` "none opens, commits or rolls back a session"; `workmain/services/calendar_service.py:6-7`; `workmain/cli/commands/clients.py:95` `with get_db().session_scope() as session:`; `docs/standards/4-database.md` §4.1 "The code that opens a scope owns its unit of work … Code it hands the session to … never commits it" | High |
| F2 | §4.1 already uses "unit of work" for the scope its opener owns, and permits the opener to commit inside it (commit before it waits). A service handed the session never commits. | `docs/standards/4-database.md` §4.1, bullets 2 and 3 | High |
| F3 | §6.2 already states: "A service that takes a unit of work is tested with a fake one, and its test needs no `db_session`." No standard says how a unit of work is opened or where its fake lives. | `docs/standards/6-testing.md` §6.2, Service; `docs/standards/4-database.md` §4.1 example opens `session_scope()` only | Medium |
| F4 | #206's first criterion has the command call a service "inside a unit of work it owns (#258)"; its third tests services with "a fake unit of work". Under the service-owned transaction (§4) the command builds the unit of work and the service enters it, so the first criterion's wording no longer matches. | Issue #206 body, ACs 1 and 3 | Medium |
| F5 | A surface may import from the Data layer only `workmain/database/connection.py`; the checker hard-codes that one exception. A new module elsewhere under `workmain/database/` that a command imports is a new finding. | `docs/ARCHITECTURE.md` section 1, Surfaces and Data rows; `automation/architecture_check.py` `check_layers`: `src == "Surfaces" and dst == "Data" and not target.endswith("database/connection.py")` | High |
| F6 | A new module under `workmain/database/` that is not `connection.py`, `models.py` or under `repositories/` matches no section 1 Data path, so `layer_of` returns `None` and the layer check skips it. `workmain/services/` is covered whole. | `docs/ARCHITECTURE.md` section 1 Data row lists three paths; `automation/architecture_check.py` `layer_of`, `check_layers` `if src_i is None: continue` | Medium |
| F7 | Two services open their own session for an outside-action record, through `get_db().record_scope()`, outside the caller's scope by design. At `workmain/services/clockify_service.py:476-487` that record is a paired write: `create_note` then `create_paired_time_entry` on the record session, so a converted `create_note` needs a unit of work over `record_scope()` there. | `workmain/services/ai_cost_service.py:56`, `workmain/services/clockify_service.py:60`, `:476-487`; `docs/standards/4-database.md` §4.3 | High |
| F8 | Some services use the session for more than building repositories: a savepoint (`session.begin_nested()`), and helpers in `workmain/utils/ics_parser.py` that take the session (a known deficiency, #159). A unit of work that exposes only repositories has no form for either. | `workmain/services/ai_cost_service.py:94`; `workmain/services/calendar_service.py:231`, `:284`; `docs/ARCHITECTURE.md` section 3, "Code in `workmain/utils/` that a layer owns" | Medium |
| F9 | 19 modules outside `workmain/services/` import from it. `workmain/cli/output.py` imports only `exceptions` and `results` types; the other 18 call services. `ScheduleService` is a class that takes the session in `__init__`, a third form beside session-taking functions. F24 maps the non-CLI callers to the issues that cover them. | `grep -rnE "from workmain.services(\.\| import)" workmain` excluding `workmain/services/`; `workmain/cli/output.py:37-38`; `workmain/services/schedule_service.py:33-39` | Low |
| F10 | All 12 repositories take exactly `(session)` in `__init__`, so a unit of work can build every one from its session the same way. Public methods per repository range from 3 (`notification_repository.py`) to 29 (`meetings_repo.py`); 142 in all. | `grep -n "def __init__" workmain/database/repositories/`; `grep -cE '^    def [a-z]'` per file | Medium |
| F11 | Repository methods carry SQL semantics a fake has to reproduce: case-insensitive match (`ClientRepository.get_by_name` uses `func.lower`), substring search (`find_by_name_fuzzy`), ordering (`list_all` orders by name), and PostgreSQL array operators (§4.4). A fake that differs answers a service test differently from production, and nothing today would show it. | `workmain/database/repositories/client_repository.py:73-89`; `docs/standards/4-database.md` §4.4 | High |
| F12 | Repositories reach across tables inside one session: `ClientRepository.set_active` and `clear_active` write `system_state` through `SystemStateRepository(self.session)`, and `get_active` reads it. Fake repositories that each keep a private store cannot reproduce that; they need one shared store. | `workmain/database/repositories/client_repository.py:149-198` | High |
| F13 | Repositories return ORM model instances, whose ids and Python-side defaults the session fills on flush. A model built without a session is a plain object with `id = None`; a fake that stores it must assign the id itself. `SystemStateRepository` queries the `SystemState` model and returns plain `str`/`int`/`bool` values. | `workmain/database/models.py:51-63` `Client`; `workmain/database/repositories/system_state_repository.py:22-76` | Medium |
| F14 | `workmain/database/models.py` declares its own `declarative_base()` and no repository imports `connection.py`, so a module that imports `connection.py` and the repositories has no import cycle. | `workmain/database/models.py:32`; `grep -rn "connection import" workmain/database/` finds only `migrations/env.py` | Low |
| F15 | `tests/conftest.py` binds `DatabaseConnection.SessionLocal` to the test's transaction, so a unit of work that opens its session through `get_db().session_scope()` or `record_scope()` joins it with no change to the fixture. A test that holds `db_session` and then enters a unit of work finishes the unit of work first, the order §6.1 requires. | `tests/conftest.py:137-146` `_isolated_database`; `docs/standards/6-testing.md` §6.1 "Sessions sharing the connection must finish last-in, first-out" | Low |
| F16 | #206 needs, for `status`, `SystemStateRepository.get_int` and `ClientRepository.get_by_id` and `list_all`, as the command reads them today. #206's own spec may change which it calls. | `workmain/cli/interface.py:127-131` | Low |
| F17 | `tests/mocks/` is the §7 home for "Fakes for external services, never test files". It holds one module today, `stub_providers.py`. | `docs/standards/7-file-placement.md` §7; `tests/mocks/__init__.py` | Low |
| F18 | Baseline: `python3 automation/architecture_check.py` passes with no new finding; `pytest --collect-only -q` collects 1635 tests. | Run 20261113 on `e84f093` | Low |
| F19 | The same atomic grouping is composed by hand at several call sites. Note plus paired time entry: `workmain/cli/commands/meetings.py:707`/`:714`, `workmain/cli/commands/notes.py:356`/`:363`, `workmain/cli/commands/time.py:288`/`:296`, `workmain/services/clockify_service.py:477`/`:480`. Condensed note plus `link_condensed_note`, which repoints the meeting's entry on that date or creates one: `workmain/cli/commands/meetings.py:885`/`:894`, `workmain/cli/commands/notes.py:674`/`:683`. `create_time_entry` is called from the CLI (`workmain/cli/commands/time.py:307`) and from Slack (`workmain/orchestration/action_executor.py:111`). Each caller decides which writes commit together. | the cited lines; `workmain/services/time_entry_service.py:130-167` `link_condensed_note` | High |
| F20 | 12 `session.commit()` calls sit mid-scope outside `workmain/database/connection.py`: `meetings.py` 3, `notes.py` 2, `reports.py` 1, `time.py` 2, `eod_workflow.py` 4. They fall in three kinds. **Redundant** (the scope commits on exit and only a print or `return` follows): `workmain/cli/commands/reports.py:446`, `workmain/workflows/eod_workflow.py:1064`. **One item's decision inside a loop of prompts**: `workmain/cli/commands/meetings.py:1234` (after its confirm), `workmain/workflows/eod_workflow.py:622`, `:627`, `:833`. **Right before a prompt for a separate, optional step**: `workmain/cli/commands/meetings.py:981`, `:1222`, `workmain/cli/commands/notes.py:340`, `:658`, `workmain/cli/commands/time.py:333`, `:349`. | `grep -rnE "\bsession\.commit\(\)" workmain` excluding `connection.py`; `workmain/workflows/eod_workflow.py:595`, `:800` (the loops), `:996` (the scope holding `:1064`) | Medium |
| F21 | 122 `session_scope(` call sites in 20 files outside `workmain/database/connection.py`. | `grep -rnE "session_scope\(" workmain --include=*.py`, excluding `connection.py` | Low |
| F22 | 35 `return` statements in `workmain/services/` are not their function's last statement. None returns normally after a partial write: each comes before the function's first write (`clockify_service.apply_pull:447`, `:450`; `notes_service.apply_cf_hook_on_tag_update:31`; `schedule_service.is_working_day:44`; `ai_cost_service.link_report:92`), after a write its own scope already rolled back (`apply_pull:456`, `:490`; `ai_cost_service.record_reply:75`), after a write its own scope completed (`apply_pull:464`), after the function's only write (`time_entry_service.link_condensed_note:157`), or in a function that does not write. `ai_cost_service.py:98` is its function's last statement, after a write its savepoint rolled back. | AST walk of `workmain/services/*.py` for `Return` nodes other than the function body's last statement | Medium |
| F23 | `NoteCondenser.condense_meeting` reads the meeting and its notes, calls `provider_manager.generate`, then writes `condensed_summary` and flushes, all on the caller's session. Its own write comes after the call; the info-only path writes with no call. | `workmain/ai/note_condenser.py:148-180` | Medium |
| F24 | The non-CLI callers and the issue that covers each: `workmain/orchestration/action_executor.py:111`, `:150` (`create_time_entry`, `create_note`) — #254 names `ActionExecutor` as a command handler but no #254 criterion converts its service calls; `workmain/workflows/eod_workflow.py:506`, `:728` (`ScheduleService`), `:1098` (`email_service.save_draft`) — #254; `workmain/daemon/daemon.py`, `scheduler.py`, `inspection_engine.py` (`ScheduleService`) — #261, not a #198 child; `workmain/ai/provider_manager.py:210` (`record_reply`), `workmain/ai/report_generator.py:192` (`link_report`) — #262, not a #198 child. None of #254, #261 or #262 has a criterion about a unit of work. | the cited lines; issue bodies of #254, #261, #262 | Medium |
| F25 | Of the twelve call sites Q6 would move (a paired call such as `:356`/`:363` counted once), eleven sit inside an open `session_scope()`; three of those have written since the scope's last commit. A use case moved there opens a second session on a second connection while the caller's is open. Where the caller holds an uncommitted write on a row the use case locks, each waits on the other with no timeout, the hang `record_scope()`'s `lock_timeout` exists to turn into an error. Where the caller reads after the use case returns, its session may not see the use case's committed rows until it refreshes. **No write since the last commit:** `workmain/cli/commands/notes.py:320` (scope `:264`, reads only), `:356`/`:363` (commit `:340`, prompts only), `workmain/cli/commands/meetings.py:707`/`:714` (scope `:626`, reads only), `workmain/cli/commands/time.py:288`/`:296` and `:307` (scope `:198`, reads only), `:336` (commit `:333`, prompts only), `workmain/orchestration/action_executor.py:111`, `:150` (inside `begin_nested()` at `:72`, in the scope its caller opens at `workmain/daemon/daemon.py:492` or `workmain/integrations/slack/slack_eod.py:468`; nothing written before the handler). **Written since the last commit:** `workmain/cli/commands/notes.py:636` (scope `:519`; earlier iterations of the loop at `:627` wrote their notes and carry-forward task rows), `:674`/`:683` (commit `:658`; `condense_meeting` at `:668` then updated the meeting's `condensed_summary` and `condensed_at`), `workmain/cli/commands/meetings.py:885`/`:894` (scope `:826`, no commit; `condense_meeting` at `:864` updated the meeting the same way). **Not inside a caller's scope:** `workmain/services/clockify_service.py:477`/`:480`, which `workmain/cli/commands/clockify.py:168` calls after the classifying scope at `:163` has closed. In the three written cases the use case inserts rows that reference the updated meeting; PostgreSQL's key-share lock on that reference does not conflict with an update of non-key columns, so none waits today, but a use case that updated the meeting row would. `link_condensed_note` takes the caller's `Meeting` model (`:683`, `:894`), which a use case on its own session would receive across a session boundary (§4.2). **pytest cannot show any of this:** under F15 every session in a test shares one connection and one transaction, so the second session sees the first's uncommitted writes and never waits on its locks. | the cited lines; `workmain/database/connection.py:98-100` `record_scope`; `tests/conftest.py:137-146` | High |
| F26 | 29 of the 41 session-taking functions in `workmain/services/` belong to services whose command-group conversions closed before the unit of work existed, so no open issue converts them: `calendar_service` 8 (#203), `clients_service` 7 (#204), `tasks_service` 7 (#58), `clockify_service` 4 (#202: `get_status`, `plan_push`, `plan_entry_push`, `classify`), `ai_cost_service` 3 (#201: `cost_summary`, `condensation_costs`, `report_costs`). They call 31 repository methods across five repositories. `calendar_service` reaches two session-taking helpers in `workmain/utils/ics_parser.py` (F8) that #159 moves; `clockify_service.plan_entry_push` is called at `workmain/cli/commands/time.py:354` inside `time add`'s open scope. | AST walk of `workmain/services/*.py` for a parameter named `session` or annotated `Session`; repository calls per service by AST; `gh issue view` of #58, #159, #201–#204 | High |

## 4. Options

### The transaction belongs to the use case

Ray, 20261113, reversing this study's first draft, which had the opener commit and the service never do so (§4.1 as written, F1, F2). For a converted service:

- The command builds the unit of work and passes it in. A use-case service enters it with `with uow:`. On exit it commits after a normal return and rolls back on an `Exception`, the rule `session_scope()` follows. It has no public `commit()`.
- Why: the same atomic grouping is composed by hand at several call sites (F19). Under command ownership each caller decides which writes go together; under use-case ownership one use case decides once for every surface.
- Not a reason: test strength. With no public `commit()`, "committed" means "returned normally" under either model.

§4.1 changes to state this (Q5).

### Settled by an existing rule

Each is the answer a written rule gives. Ray can reverse any of them.

- **It opens its session through `get_db().session_scope()`, or `record_scope()` when told to.** §4.1: application code opens a session only through those. It is then inside the test transaction with no fixture change (F15).
- **It exposes repositories, not its session.** §4.3: all data access goes through a repository. A service that needs a savepoint or a session-taking helper (F8) is a question for the issue that converts it.
- **The fake goes in `tests/mocks/`.** §7 (F17): it is a fake of an external service, the database, and not a test file.

### Added to #258's scope

Ray, 20261113. None is in the issue's criteria; the issue body is edited at close-out to carry them (`docs/standards/1-workflow.md` §1.2).

1. **Re-entry guard.** `__enter__` raises if the unit of work is already entered or has been used. Without it a nested or reused unit of work silently drops writes: the inner scope replaces the outer one's session, and the outer scope never exits. Tested against the real unit of work.
2. **Scope parameter.** The unit of work wraps `session_scope()` by default and `record_scope()` when told to. Without it the Clockify pull path (F7) has nothing to pass to a converted `create_note`. Savepoints (F8) stay with the converting issue.
3. **Open-scope check.** The check on Q5's sixth point. pytest under F15 cannot show a second session waiting or reading stale (F25), so the check is on the call, not its effect.
   - `session_scope()` sets a context variable while it is open, and resets it with its token in a `finally`, so `SystemExit` and `KeyboardInterrupt`, which skip its commit and rollback (§4.1), clear it too.
   - `UnitOfWork.__enter__` on `session_scope()` raises when the variable is set. A record-scope unit of work does not check it.
   - Because the unit of work wraps `session_scope()`, an entered unit of work sets the variable itself, so the check also catches a use case nested in another on a fresh unit of work: the gap the re-entry guard cannot see (Q5, third point).
   - It fails in production as in tests: every test that drives a command into a use case inside its scope fails whatever the data, and the daemon and Slack paths fail loudly rather than hang. A static check for a use-case call lexically inside a `with … session_scope()` block was set aside: it misses a call made through a helper, and that miss is silent.
   - Tests: a use case entered inside an open `session_scope()` raises; entered after the scope closes, it does not; the variable is clear after the scope exits by an `Exception` and by a `BaseException`.
4. **Session-parameter check** (Ray, 20261114). A script in `automation/` that lists every function or method taking a session parameter, so the criteria that retire the session-taking form (Q7) share one check instead of each carrying its own one-line walk. A session parameter is one named `session` or annotated with `Session`.
   - It takes paths to service modules, or `--package <dir>`, a package whose imports of `workmain/services/` it resolves itself. It prints one line per function or method found, as `<path>:<line> <name>`, and exits non-zero when it finds any.
   - `--exclude <path>` leaves a module out, for #198's criterion on `workmain/services/unit_of_work.py`; `<path>::<function>` narrows a path to named functions, for #262's criterion on only the functions it adds or changes and for the issues that convert part of `clockify_service` and `ai_cost_service`. Proposed by Spanner, approved by Ray, 20261114.
   - `--package` resolves imports inside functions as well as at module level: `workmain/workflows/eod_workflow.py` imports `ScheduleService` only inside functions (`:505`, `:727`). Ray, 20261114.
   - Its name in the issue criteria is `automation/session_param_check.py`, with its tests in `automation/session_param_check_test.py` (`docs/standards/7-file-placement.md` §7). The tests cover: a parameter named `session` and one annotated `Session` are both found; a method's is found; `--exclude` and `<path>::<function>` narrow the set; `--package` resolves a module-level import and an import inside a function; the exit status is non-zero exactly when something is found.

### Q1 — Where it lives and who owns it

The map names no owner today; the spec names one with Ray's approval (issue #258, Direction). A new module under `workmain/database/` other than `connection.py` is not an option: a command importing it is a new checker finding (F5), and the checker cannot place it in a layer (F6).

#### Option A — `workmain/database/connection.py`, Data layer

- **Approach:** a `UnitOfWork` class beside `session_scope()`; one line in map section 2.
- **Pros:** surfaces already reach data only through this module (F5); no import cycle (F14).
- **Cons:** with the transaction owned by the use case, the unit of work is the application layer's transaction boundary, not a data-access helper; `connection.py` grows from session factory to session plus every repository.

#### Option B — `workmain/services/unit_of_work.py`, Application layer

- **Approach:** a new module with a line under Application in map section 2. Section 1's Surfaces rule ("a surface owns its session through `workmain/database/connection.py`") is reworded for a surface that builds a unit of work and passes it to a use case.
- **Pros:** the use case that owns the transaction and the object it owns sit in one layer, where the source pattern (*Architecture Patterns with Python*, Ch. 6) puts it. The checker passes: `workmain/services/` is covered whole, and a surface may import the application layer.
- **Cons:** map sections 1 and 2 both change.

**Recommendation:** Option B. It follows from the transaction belonging to the use case.

### Q2 — What the real unit of work holds

#### Option A — every repository

- **Approach:** one attribute per repository, named for its table (`uow.clients`, `uow.system_state`, …), each built from the session (F10).
- **Pros:** fixed once; no converting issue edits the unit of work to add a repository.
- **Cons:** the fake holds fewer than the real one until conversions add theirs (Q3). An attribute the fake lacks raises `AttributeError` in the test.

#### Option B — only the repositories a converted service uses

- **Approach:** start with what #258's fake covers; each converting issue adds the real and fake attribute together.
- **Pros:** real and fake always hold the same set.
- **Cons:** every #198 child edits the unit of work as well as `tests/`.

**Recommendation:** Option A. The real side is trivial and complete; the fake grows with need, and Q4's parity check confines it to what the real one has.

### Q3 — Which fake repositories ship with #258

Criterion 2 needs at least one fake repository ("what a repository is given is returned by it").

#### Option A — `SystemStateRepository` only

- **Approach:** a fake of all 7 of its methods, over the one shared in-memory store F12 requires.
- **Pros:** key-value over plain values (F13), no query semantics (F11): the fake can be shown equal to the real one completely. It is the store `ClientRepository` writes into, so later fakes build on it.
- **Cons:** #206 adds the `ClientRepository` fake it needs.

#### Option B — what #206's `status` reads today

- **Approach:** `SystemStateRepository.get_int`, `ClientRepository.get_by_id` and `list_all` (F16).
- **Pros:** #206 needs no fake work of its own.
- **Cons:** designs to a spec not yet written, and brings in ORM-model ids (F13) and ordering (F11) before Q4's rule is settled on the simple case.

**Recommendation:** Option A. #258 builds the infrastructure on the one repository it can prove faithful; a fake of a repository a service uses goes with the service.

### Q4 — How a fake is kept faithful

What it is for: F11 — a service test passes against a fake that answers differently from the SQL, and the defect reaches production unseen.

#### Option A — parity of names and signatures only

- **Approach:** a test that each fake repository's public methods are a subset of the real one's with the same signatures, and that the fake unit of work's attributes are a subset of the real one's. The form #206 sets for its recording renderer.
- **Pros:** cheap and mechanical.
- **Cons:** says nothing about what a method returns.

#### Option B — parity, plus shared behaviour tests

- **Approach:** Option A, and each faked method's tests run against both the real repository (with `db_session`) and the fake, through one parametrized test class.
- **Pros:** a fake that differs from SQL fails. Each later fake inherits the form.
- **Cons:** every fake method carries a test against the database as well.

#### Option C — none

- **Cons:** F11 stands.

**Recommendation:** Option B. The unit of work exists to move behaviour tests off the database; Option B is what makes the move lose nothing.

### Q5 — What §4.1 states

#### Option A — §4.1 states the unit of work, in #258

- **Approach:** §4.1 states:
  - the session-taking form and the unit-of-work form side by side;
  - a use case enters a unit of work; an operation takes one already entered and never enters or commits it;
  - workflows, orchestration and the daemon call use cases: they build one unit of work per call and never enter one themselves. A use case never builds a unit of work; only its caller does, so one use case never calls another on a unit of work of its own, which the re-entry guard cannot see and the open-scope check catches (Added to #258's scope, item 3);
  - the wait rule, narrowed: a use case holds no write across an outside call (F20, F23);
  - a use case that decides not to go ahead raises, so a normal return always means its writes are wanted (F22);
  - a use case is not called inside an open `session_scope()`, except on a `record_scope()` unit of work under §4.3's existing conditions. Reasoning: a second session beside an open one can wait forever on the first's locks and reads around its uncommitted writes (F25). §4.3 already allows exactly one second session beside an open one, the outside-action record, because it is written immediately after the action and never writes or references a row the open transaction has written; a record-scope unit of work under those same conditions carries the same guarantee, and its `lock_timeout` turns any wait into an error. No other condition carries it: "the caller has not written since its last commit" holds at eight of F25's sites today, but nothing keeps it true when the command changes, and the stale read after the call remains.
- **Pros:** §6.2 already names the unit of work (F3); every converting author reads the rule, not a precedent.
- **Cons:** a standards edit the issue did not list.

**The outside-action record.** An outside-action record is written while a use case runs: `condense_meeting` calls `provider_manager.generate`, which records its cost through `record_scope()` (`workmain/ai/provider_manager.py:210`). Ray, 20261113: the third point holds without exception. A use case that makes an outside call receives the outside-call dependency from its caller (the provider manager, per #198's testing-review decision 2), and that dependency makes its own §4.3 record. The use case never builds a unit of work, its caller passes nothing extra, and a test passes a stub that records nothing (`tests/mocks/stub_providers.py`). Reasoning: a §4.3 record is not part of the use case's transaction by design; passing it with the dependency keeps it out of the use case without exposing it to every caller. The shape of the dependency and its recording belong to #262 and the first conversion that calls a provider. Two forms considered first were set aside: a caller passing a second, record-scope unit of work exposes the record to every caller of such a use case, and a carve-out letting a use case build one on `record_scope()` makes the third point a rule with an exception.

**Checking the sixth point** is the open-scope check, item 3 under Added to #258's scope.

#### Option B — no; #206 states it when it first uses one

- **Cons:** until then §6.2 refers to a mechanism no standard defines, and the reversal above has no home.

**Recommendation:** Option A.

### Q6 — Converting the note and time-entry write family

Converting `create_note` and `create_paired_time_entry` (and with them `create_time_entry` and `link_condensed_note`, F19) cuts across command groups: they are called from the meetings, notes and time groups (#208, #209, #216), from `clockify_service.apply_pull` (F7) and from `ActionExecutor` (F24). Under §4 they become operations, and the groupings F19 lists become use cases that enter the unit of work.

#### Option A — a separate #198 child, sequenced before #208, #209 and #216

- **Approach:** one issue converts the family to operations, adds the use cases F19's groupings need, and moves every caller onto them: the three command groups' call sites, `apply_pull` (on a `record_scope()` unit of work) and `ActionExecutor`.
- **Pros:** no command-group conversion carries the change or two signatures; the write path (`CLAUDE.md` § Note Write-Path Convergence) changes once, in one spec, against one census.
- **Cons:** it edits three unconverted command groups' call sites, which #208, #209 and #216 then convert again in their own terms. Each moved call site that sits inside an open scope, eleven of twelve (F25), is restructured so the use case runs outside the command's scope: the command closes its scope before the call and opens a new one for anything it reads after, it hands the use case ids rather than its own models (`link_condensed_note`'s `Meeting`), and the three that have written since their last commit either commit before the call or move that write (the condensation) into the use case. `ActionExecutor`'s two calls run inside the scope its callers open at `workmain/daemon/daemon.py:492` and `workmain/integrations/slack/slack_eod.py:468`, around the whole of `execute`, so the move reaches scopes #261 and #254 also change: those two callers stop opening a scope around `execute`, and `ActionExecutor` opens one for each handler that still takes a session and builds a unit of work for each that calls a use case (Q5, third point). Sequencing: the child is opened with #254 and #261 in its `blocking` field (`docs/standards/1-workflow.md` §1.3), so both start from the restructured scopes and neither edits those lines while the child does; its position on the board is Ray's (§1.6).

#### Option B — the first of #208, #209 and #216 on the board carries it

- **Approach:** that issue converts the family and every caller across all three groups, `apply_pull` and `ActionExecutor`.
- **Pros:** no new issue.
- **Cons:** one command-group issue edits the other two groups and two non-CLI modules; its scope depends on board order, and a reorder moves the work.

A third form, a unit-of-work signature beside the session one until the last group converts, is dropped: it keeps two write paths for one write, which § Note Write-Path Convergence exists to prevent.

**Recommendation:** Option A, as Ray proposed. The restructuring F25 adds does not change it: Option B moves the same eleven call sites, so the cost is the same under both. It strengthens A, which restructures them once, against one census, in an issue whose scope is that work.

### Q7 — Where the criterion retiring the session-taking form lives

No issue converts the non-CLI callers onto a unit of work (F24), and #261 and #262 are not #198 children.

#### Option A — on #198, with each caller's issue converting its own call sites

- **Approach:** #198 gains the criterion "no function or class in `workmain/services/` takes a `Session`", checked by an AST walk of `workmain/services/`. Each issue that owns a non-CLI caller gains a criterion that its call sites pass a unit of work: #254 for `eod_workflow.py`, #261 for the daemon, #262 for `provider_manager.py` and `report_generator.py`; `ActionExecutor`'s calls go with Q6. #261 and #262 are linked as blocking #198.
- **Pros:** the property is #198's, and it is checked once, where the last conversion lands; each caller is converted by the issue that already changes that code.
- **Cons:** four issue bodies change, and #198, which "does no work of its own", carries a criterion.

#### Option B — a last #198 child that converts what remains and retires the form

- **Pros:** one issue with a spec and a branch holds the retirement.
- **Cons:** its scope is whatever the others left, unknown until they close; callers end up converted by an issue other than the one that changes their code.

**Recommendation:** Option A.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Does the unit of work live in `workmain/database/connection.py` (Data layer) or `workmain/services/unit_of_work.py` (Application layer)? | Ray, 20261113: Option B, `workmain/services/unit_of_work.py`. It follows from the transaction belonging to the use case (§4). |
| Q2 | Does the real unit of work hold every repository from the start, or only those a converted service uses, added per conversion? | Ray, 20261113: Option A, every repository. |
| Q3 | Does #258 ship a fake of `SystemStateRepository` only, or of what #206's `status` reads today? | Ray, 20261113: Option A, a fake of `SystemStateRepository` only, over one shared in-memory store (F12). |
| Q4 | Is a fake kept faithful by name and signature parity only, by parity plus behaviour tests run against both the fake and the real repository, or not at all? | Ray, 20261113: Option B, parity plus behaviour tests run against both. |
| Q5 | Does #258 state the unit of work in `docs/standards/4-database.md` §4.1, or is that left to #206? | Ray, 20261113: Option A, with all six points as Q5 Option A lists them, including the third point's "a use case never builds a unit of work; only its caller does". The outside-action record is made by the outside-call dependency the caller passes in (Q5, The outside-action record). The sixth point is checked by the open-scope check, added to #258's scope. |
| Q6 | Is the note and time-entry write family converted by a separate #198 child sequenced before #208, #209 and #216, or by the first of those three on the board? | Ray, 20261113: Option A, a separate #198 child sequenced before #208, #209 and #216, opened with #254 and #261 in its `blocking` field. |
| Q7 | Does the criterion retiring the session-taking form live on #198, with each non-CLI caller's issue converting its own call sites, or on a last #198 child? | Ray, 20261113: Option A, on #198, with each non-CLI caller's issue converting its own call sites. Ray, 20261114: the services F26 lists are converted by four #198 children, split by what each waits on, each blocking #198 and blocked by #258: #279 `clients_service` and `tasks_service`; #280 the cost-report reads, also blocked by #262; #281 four `clockify_service` functions, also blocked by #278 and blocking #216, so #216 starts from the converted `plan_entry_push`; #282 `calendar_service`, also blocked by #159. #262 is narrowed to the functions it adds or changes. The reversal wording is fixed in #198 and every open child. #261 and #262 block #198. The criteria call the session-parameter check (Added to #258's scope, item 4). |

## 6. Disposition

- Promoted to: `../specs/UNIT_OF_WORK_SPEC.md`; issues #278 (Q6), #279, #280, #281 and #282 (Q7)
- Superseded by:

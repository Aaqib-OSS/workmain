# Unit of Work — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261113
**Originating item:** Issue #258

---

## 1. Purpose

Every service function in `workmain/services/` takes a SQLAlchemy `Session` and builds the repositories it needs from it, so a test of a service needs a real database session. Issue #258 adds a unit of work: one object a service receives, holding its repositories and the commit, with a real form wrapping a session and a fake form in `tests/` holding repositories in memory. Services converted under #198 from #206 on take it; existing services are not converted here. This study measures what the unit of work must fit, and sets out the choices whose answers change the spec: where it lives and who owns it in `docs/ARCHITECTURE.md`, what it holds, which fake repositories ship with it, and how a fake is kept faithful to the repository it replaces.

## 2. Scope of the read

Read at `origin/main` `e84f093`, 20261113:

- `docs/ARCHITECTURE.md` sections 1–3; `automation/architecture_check.py` (`read_layers`, `layer_of`, `check_layers`, `check_ownership`), and a run of it.
- `docs/standards/` §4.1–§4.3, §6.1, §6.2, §3.8, §7.
- `workmain/database/connection.py`, `workmain/database/models.py` imports, every `workmain/database/repositories/*.py` constructor and public-method count, `ClientRepository` and `SystemStateRepository` in full.
- Every module in `workmain/services/`: its session use and the repositories it builds.
- `workmain/cli/interface.py` `status` and `workmain/cli/commands/clients.py`, as the shape of a command that calls a service.
- `tests/conftest.py` `_isolated_database` and `db_session`; `tests/mocks/`.
- Issues #198 and #206.

Not read: the workflow, orchestration and daemon callers of services beyond counting them (F9); they are the converting issues' census, not this one's.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | Every service function takes a `Session` and builds repositories from it; none commits, rolls back or opens a session, except the outside-action records in F7. The command that opens the scope owns it. | `workmain/services/clients_service.py:4` "none opens, commits or rolls back a session"; `workmain/services/calendar_service.py:6-7`; `workmain/cli/commands/clients.py:95` `with get_db().session_scope() as session:`; `docs/standards/4-database.md` §4.1 "The code that opens a scope owns its unit of work … Code it hands the session to … never commits it" | High |
| F2 | §4.1 already uses "unit of work" for the scope its opener owns, and permits the opener to commit inside it (commit before it waits). A service handed the session never commits. | `docs/standards/4-database.md` §4.1, bullets 2 and 3 | High |
| F3 | §6.2 already states the rule the issue builds toward: "A service that takes a unit of work is tested with a fake one, and its test needs no `db_session`." No standard says how an owner opens a unit of work or where its fake lives. | `docs/standards/6-testing.md` §6.2, Service; `docs/standards/4-database.md` §4.1 example opens `session_scope()` only | Medium |
| F4 | #206's criteria already fix the ownership split: the command "calls a service in `workmain/services/` inside a unit of work it owns (#258)", and its service tests use "a fake unit of work". | Issue #206 body, ACs 1 and 3 | High |
| F5 | A surface may import from the Data layer only `workmain/database/connection.py`; the checker hard-codes that one exception. A new module elsewhere under `workmain/database/` that a command imports is a new finding. `workmain/database/connection.py` is not in a Data-layer path the check would miss: section 1 lists it by name. | `docs/ARCHITECTURE.md` section 1, Surfaces and Data rows; `automation/architecture_check.py` `check_layers`: `src == "Surfaces" and dst == "Data" and not target.endswith("database/connection.py")` | High |
| F6 | A new module under `workmain/database/` that is not `connection.py`, `models.py` or under `repositories/` matches no section 1 Data path, so `layer_of` returns `None` and the layer check skips it entirely. `workmain/services/` is covered whole. | `docs/ARCHITECTURE.md` section 1 Data row lists three paths; `automation/architecture_check.py` `layer_of`, `check_layers` `if src_i is None: continue` | Medium |
| F7 | Two services open their own session for an outside-action record, through `get_db().record_scope()`, outside the caller's scope by design. A unit of work wrapping the caller's session does not cover these; a service converted with such a write still reaches the database in its test. | `workmain/services/ai_cost_service.py:56`, `workmain/services/clockify_service.py:60`, `:476`; `docs/standards/4-database.md` §4.3 "A write that records an outside action commits on its own" | Medium |
| F8 | Some services use the session for more than building repositories: a savepoint (`session.begin_nested()`), and helpers in `workmain/utils/ics_parser.py` that take the session (a known deficiency, #159). A unit of work that exposes only repositories has no form for either. | `workmain/services/ai_cost_service.py:94`; `workmain/services/calendar_service.py:231`, `:284`; `docs/ARCHITECTURE.md` section 3, "Code in `workmain/utils/` that a layer owns" | Medium |
| F9 | Services are reached from 19 modules outside `workmain/services/`: CLI commands, `workmain/cli/output.py`, the orchestration and workflow modules, the daemon, and two AI modules. Converting a service to take a unit of work changes every one of its call sites; that census belongs to each converting issue. | `grep -rnE "from workmain.services(\.| import)" workmain` excluding `workmain/services/` | Low |
| F10 | All 12 repositories take exactly `(session)` in `__init__`, so a unit of work can build every one from its session the same way. Public methods per repository range from 3 (`notification_repository.py`) to 29 (`meetings_repo.py`); 142 in all. | `grep -n "def __init__" workmain/database/repositories/`; `grep -cE '^    def [a-z]'` per file | Medium |
| F11 | Repository methods carry SQL semantics a fake has to reproduce: case-insensitive match (`ClientRepository.get_by_name` uses `func.lower`), substring search (`find_by_name_fuzzy`), ordering (`list_all` orders by name), and PostgreSQL array operators (§4.4). A fake that differs answers a service test differently from production, and nothing today would show it. | `workmain/database/repositories/client_repository.py:73-89`; `docs/standards/4-database.md` §4.4 | High |
| F12 | Repositories reach across tables inside one session: `ClientRepository.set_active` and `clear_active` write `system_state` through `SystemStateRepository(self.session)`, and `get_active` reads it. Fake repositories that each keep a private store cannot reproduce that; they need one shared store. | `workmain/database/repositories/client_repository.py:149-198` | High |
| F13 | Repositories return ORM model instances, whose ids and Python-side defaults the database session fills on flush. A model built without a session is a plain object with `id = None`; a fake that stores it must assign the id itself. `SystemStateRepository` returns plain `str`/`int`/`bool` and holds no model. | `workmain/database/models.py:51-63` `Client`; `workmain/database/repositories/system_state_repository.py:22-76` | Medium |
| F14 | `workmain/database/models.py` declares its own `declarative_base()` and no repository imports `connection.py`, so `connection.py` can import the repositories without a cycle. | `workmain/database/models.py:32`; `grep -rn "connection import" workmain/database/` finds only `migrations/env.py` | Low |
| F15 | `tests/conftest.py` binds `DatabaseConnection.SessionLocal` to the test's transaction, so a unit of work that opens its session through `get_db().session_scope()` joins it with no change to the fixture. A test that holds `db_session` and then opens a unit of work finishes the unit of work first, which is the order §6.1 requires. | `tests/conftest.py:137-146` `_isolated_database`; `docs/standards/6-testing.md` §6.1 "Sessions sharing the connection must finish last-in, first-out" | Low |
| F16 | #206 needs, for `status`, `SystemStateRepository.get_int` and `ClientRepository.get_by_id` and `list_all`, as the command reads them today. #206's own spec may change which it calls. | `workmain/cli/interface.py:127-131` | Low |
| F17 | `tests/mocks/` is the §7 home for "Fakes for external services, never test files". It holds one module today, `stub_providers.py`. | `docs/standards/7-file-placement.md` §7; `tests/mocks/__init__.py` | Low |
| F18 | Baseline: `python3 automation/architecture_check.py` passes with no new finding; `pytest --collect-only -q` collects 1635 tests. | Run 20261113 on `e84f093` | Low |

## 4. Options

### Settled by an existing rule

These are not open; each is the answer a written rule gives. Ray can reverse any of them.

- **The opener commits; the service never does.** §4.1 (F1, F2): the code that opens the scope owns it and may commit before it waits; code it hands the session to never commits or rolls back. The unit of work therefore has `commit()` and `rollback()` for its owner, and commits on normal exit and rolls back on an `Exception`, as `session_scope()` does. A service handed it calls neither. The textbook form, where the service calls `uow.commit()`, contradicts §4.1 and is not taken.
- **It opens its session through `get_db().session_scope()`.** §4.1: application code opens a session only that way. It is then inside the test transaction with no fixture change (F15).
- **It exposes repositories, not its session.** §4.3: all data access goes through a repository. A service that needs a savepoint or a session-taking helper (F8) is a question for the issue that converts it.
- **Outside-action records stay outside it.** §4.3 requires them in a session of their own. How a converted service with such a write is tested without a database (F7) is the converting issue's question, as #198 already leaves "how a service receives" a provider manager to the first conversion that needs one.
- **The fake goes in `tests/mocks/`.** §7 (F17): it is a fake of an external service, the database, and not a test file.

### Q1 — Where it lives and who owns it

The map names no owner today; the spec names one with Ray's approval (issue #258, Direction). A new module under `workmain/database/` other than `connection.py` is not an option: a command importing it is a new checker finding (F5), and the checker cannot place it in a layer at all (F6). Fixing both changes map section 1 and `automation/architecture_check.py` for a result the option below reaches with neither.

#### Option A — `workmain/database/connection.py`, Data layer

- **Approach:** a `UnitOfWork` class beside `session_scope()`. Map section 2's `connection.py` line becomes "`get_db()`, `session_scope()` and the unit of work, the only ways to get a session".
- **Pros:** the unit of work is database access with no business decision, which is the Data layer's definition. A surface already reaches data only through this module (F5), so that rule and the checker are unchanged. No import cycle (F14).
- **Cons:** `connection.py` imports every repository module and its job grows from session factory to session-plus-repositories.

#### Option B — `workmain/services/unit_of_work.py`, Application layer

- **Approach:** a new module; map section 2 gets a line under Application. The Surfaces rule in section 1 ("a surface owns its session through `workmain/database/connection.py`") is reworded for converted commands.
- **Pros:** `connection.py` stays a session factory. It is where the source pattern (*Architecture Patterns with Python*, Ch. 6) puts it. The checker passes (services is covered whole; a surface may import the application layer).
- **Cons:** puts a module that makes no business decision in the layer defined by business decisions. Two section 1 rules change, not one line in section 2.

**Recommendation:** Option A. It places the unit of work in the layer its job belongs to, through the one door surfaces already use, and changes a single map line.

### Q2 — What the real unit of work holds

#### Option A — every repository

- **Approach:** one attribute per repository, named for its table (`uow.clients`, `uow.system_state`, …), each built from the session (F10).
- **Pros:** fixed once; no converting issue edits the Data layer to add a repository.
- **Cons:** the fake holds fewer than the real one until conversions add theirs (Q3), so "the fake can stand in for the real one" holds only for the repositories a fake exists for. An attribute the fake lacks raises `AttributeError` in the test, which is loud.

#### Option B — only the repositories a converted service uses

- **Approach:** start with the repositories #258's fake covers; each converting issue adds the real and fake attribute together.
- **Pros:** real and fake always hold the same set.
- **Cons:** every conversion edits `connection.py` (or the Q1 home) as well as `tests/`; a mechanical change spread across every #198 child.

**Recommendation:** Option A. The real side is trivial and complete; the fake grows with need, and Q4's parity check confines it to what the real one has.

### Q3 — Which fake repositories ship with #258

Criterion 2 needs at least one fake repository ("what a repository is given is returned by it").

#### Option A — `SystemStateRepository` only

- **Approach:** a fake of all 7 of its methods, over the shared in-memory store F12 requires.
- **Pros:** key-value over strings, no ORM model (F13), no query semantics (F11): the fake's behaviour can be shown equal to the real one completely. It is the store `ClientRepository` writes into, so it is the base any later fake builds on.
- **Cons:** #206 still adds the `ClientRepository` fake it needs.

#### Option B — what #206's `status` reads today

- **Approach:** `SystemStateRepository.get_int`, `ClientRepository.get_by_id` and `list_all` (F16).
- **Pros:** #206 needs no fake work of its own.
- **Cons:** designs to a spec not yet written; #206's design may call other methods. Brings in ORM-model ids (F13) and ordering semantics (F11) before the fidelity rule (Q4) is settled on the simple case.

**Recommendation:** Option A. #258 builds the infrastructure on the one repository it can prove faithful; a fake of a repository a service uses goes with the service.

### Q4 — How a fake is kept faithful

Not named in the issue, so raised before it is specified. What it is for: F11 — a service test passes against a fake that answers differently from the SQL, and the defect reaches production unseen. Without a check, "tested at the service with a fake" proves less than the `db_session` test it replaces.

#### Option A — parity of names and signatures only

- **Approach:** a test that each fake repository's public methods are a subset of the real one's, with the same signatures, and that the fake unit of work's attributes are a subset of the real one's. The same form #206 sets for its recording renderer.
- **Pros:** cheap, mechanical, catches a fake method the real one lacks or calls differently.
- **Cons:** says nothing about what a method returns.

#### Option B — parity, plus shared behaviour tests

- **Approach:** Option A, and each faked method's tests run against both the real repository (with `db_session`) and the fake, through one parametrized test class.
- **Pros:** a fake that differs from SQL fails. Each later fake inherits the form.
- **Cons:** every fake method carries a test against the database as well; a conversion's fake work roughly doubles.

#### Option C — none

- **Approach:** fakes are trusted as written.
- **Cons:** F11 stands.

**Recommendation:** Option B. The unit of work exists to move behaviour tests off the database; Option B is what makes the move lose nothing.

### Q5 — Whether §4.1 states how the owner opens a unit of work

#### Option A — yes, in #258

- **Approach:** §4.1 states that a command calling a service that takes a unit of work opens it, through the Q1 home, in place of `session_scope()`, and that the §4.1 ownership rules apply to it unchanged. §7 is unchanged (the fake fits `tests/mocks/`).
- **Pros:** §6.2 already names the unit of work (F3); #206's author then reads the rule, not a precedent.
- **Cons:** a standards edit the issue did not list.

#### Option B — no; #206 states it when it first uses one

- **Pros:** #258 changes no standard.
- **Cons:** for the life of #258's merge to #206's, a standard (§6.2) refers to a mechanism no standard defines.

**Recommendation:** Option A. It adds no new rule: it states how the existing §4.1 rule applies to the new object.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Does the unit of work live in `workmain/database/connection.py` (Data layer, one map section 2 line) or `workmain/services/unit_of_work.py` (Application layer, map section 1 and 2 changes)? | |
| Q2 | Does the real unit of work hold every repository from the start, or only those a converted service uses, added per conversion? | |
| Q3 | Does #258 ship a fake of `SystemStateRepository` only, or of what #206's `status` reads today? | |
| Q4 | Is a fake kept faithful by name and signature parity only, by parity plus behaviour tests run against both the fake and the real repository, or not at all? | |
| Q5 | Does #258 state in `docs/standards/4-database.md` §4.1 how the owner opens a unit of work, or is that left to #206? | |

## 6. Disposition

- Promoted to:
- Superseded by:

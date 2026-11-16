# Top-Level Commands — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261116
**Originating item:** Issue #206

---

## 1. Purpose

Issue #206 converts `workmain status`, `workmain today` and `workmain init` (`workmain/cli/interface.py`) to the direction #198 states. A command builds a unit of work and passes it to a use case in `workmain/services/`, which enters it. The command then hands the result to `workmain/cli/output.py`, and behaviour is tested at the service. This study measures the three commands and the infrastructure their tests run on, at `origin/main` `91102e0`, and asks Ray the questions whose answers change the spec.

**The first attempt is not a source.** A first study and spec for this issue are kept only at the tag `archive/issue-206-attempt-1`. They were written before the test database (#257), the unit of work (#258) and the shared `Summary` result (#259) existed, and the spec was never approved. Every finding below was measured again here. Every earlier ruling of Ray's was examined again against the code as it stands: it is decided here on a ground that stands without that attempt, or it is asked again.

## 2. Scope of the read

Read: `workmain/cli/interface.py`; `workmain/cli/output.py`; `workmain/services/clients_service.py`, `results.py` and `unit_of_work.py`; `ClientRepository`, `SystemStateRepository` and `workmain/database/connection.py` `scope_open`; `tests/conftest.py`; `tests/mocks/fake_unit_of_work.py` and `tests/test_fake_unit_of_work.py`; `tests/test_cli_conventions.py`; `tests/test_clients_commands.py`, read as the current command-test form; `docs/ARCHITECTURE.md`; `docs/standards/` §1, §2, §3, §4, §5 and §6; issues #198, #222, #255, #256 and #279; #258's archived spec and study, for whether they addressed §5.6; and Click 8.1.7's `Context.ensure_object` and `find_object`. `automation/architecture_check.py` was run.

Probed: a throwaway test in `tests/`, run once under the `_isolated_database` fixture and then deleted (F17).

Not read: the other command groups, beyond the grep for callers in F14, and `eod`, which moved to #254 (issue body).

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The issue's census still holds. `init` and `today` print fixed Rich lines. `status` opens a `session_scope()`, reads the `active_client_id` key, the client it names and the number of clients, and prints a title, an active-client line, a 45-row table, and footer lines. The module imports Rich and two repositories, and holds a module `Console`. | `interface.py:11-16`, `59`; `init` `105-116`; `status` `119-194`; `today` `197-270` | — |
| F2 | `status` decides on whether the client's *name* is truthy, not on whether a client was found: `if active_client_name:` and `active_client_name or "Internal"`. A client named `""` prints as internal. | `interface.py:132-137`, `183` | Low |
| F3 | `status` finds the active client through the key, then `get_by_id`. `clients status` uses `ClientRepository.get_active`, which falls back to the first client with `is_active` set when the key finds none. The two disagree when the key is unset or names a deleted client while another client is still flagged. #255 owns that divergence and lists `status` as one of its call sites. | `interface.py:129-130`; `client_repository.py:188-200`; `clients_service.get_status` `182-189`; #255 body | Owned by #255 |
| F4 | `docs/ARCHITECTURE.md` §2 names `workmain/services/clients_service.py` as the owner of "client records, the active client, and client counts". These are the only values `status` reads at run time. The map names no status or overview service. | `docs/ARCHITECTURE.md` §2 Application | — |
| F5 | No surface builds a unit of work yet: `git grep -nE 'UnitOfWork\(' -- workmain/` finds only `unit_of_work.py`. `status` will be the first command to build one. `clients_service` still takes a session until #279. `docs/standards/4-database.md` §4.1 states the two forms side by side. | grep; `clients_service.py:97-206`; §4.1 | — |
| F6 | `FakeUnitOfWork.REPOSITORIES` holds only `system_state`. The use case calls `clients.get_by_id` and `clients.list_all`, so it needs a fake `ClientRepository`. §6.2 requires a parity test for each fake method, and behaviour tests run against both the fake and the real repository on `db_session`. Those tests need rows on both sides. The `system_state` contract tests seed through the repository's own `set`. The real `ClientRepository.create` validates the name and refuses a duplicate, so a fake `create` that the contract tests seed through has to match that, as does `get_by_name`, which `create` calls. #279 lists `get_by_id` and `list_all` among the 9 methods it fakes, so whatever this issue fakes, #279 no longer has to. | `fake_unit_of_work.py:80-82`; `test_fake_unit_of_work.py:171`, `182-250`; `client_repository.py` `create`; #279 body | Cost |
| F7 | `Renderer`'s public methods are `changed`, `cancelled`, `nothing_to_do`, `warning`, `collection`, `pick`, `report` and `record`. None of them prints fixed text. Every method that prints content takes a view declared as a module constant: `CollectionView`, `RecordView` or `ReportView`. A `ReportView` with no sections and `totals_when_empty=True` prints a `Summary`: `clients status` already does, through `STATUS`. | `output.py:47-111`, `165-411`; `clients.py:59-68` | — |
| F8 | `Summary` holds totals and filters and no rows. The issue says `status` returns a `Summary`. 43 of `status`'s 45 rows are fixed text. Two carry a run-time value: `├─ Active Context` holds the client's name, and `└─ Clients Configured` holds the count. §5.6 has a converted command build no rows and format no values. So under a `Summary`, those two values cannot stay inside fixed rows. That conflicts with the issue's "Output changes only where §5.6 says so": §5.6 gives `output.py` the layout, but not a change of content. | `results.py:27-39`; `interface.py:143-189`, `186`, `189`; `docs/standards/5-cli.md` §5.6; issue body | Q1 |
| F9 | No recording renderer exists in `tests/`, and no command test takes §6.2's form yet: nothing patched, the real service run. `tests/test_clients_commands.py:46-57` patches the service and passes `Mock(spec=Renderer)`. `cli` calls `ctx.ensure_object(Renderer)`, and `pass_renderer` is `make_pass_decorator(Renderer, ensure=True)`. Click 8.1.7 finds the object with `isinstance`. The probe (F17) confirmed that a plain object passed as `obj` is replaced by a real `Renderer`, which prints, while a `Renderer` subclass and `Mock(spec=Renderer)` reach the command. A subclass inherits every public method, so the issue's check ("a test comparing the recording renderer's public methods with `Renderer`'s") passes even when the subclass overrides none and prints for real. | `interface.py:102`; `output.py` `pass_renderer`; Click `Context.find_object`; F17 | Spec restates the criterion |
| F10 | `init` is in `EXISTING_EXCEPTIONS`, and `TOP_LEVEL` permits only `eod`, `status` and `today`. #198 says each conversion settles its group's names: it renames, approves the name as a verb, or keeps it with a stated reason, and removes the name from that list. `init` is not a standard verb, and §5.1 permits a top-level command only for an orchestration workflow. | `tests/test_cli_conventions.py:39-40`, `52`; `docs/standards/5-cli.md` §5.1, §5.3; #198 body | Q2 |
| F11 | None of the three docstrings has the `Examples:` block that §5.6 requires. | `interface.py:107`, `121`, `199`; §5.6 | Decided by rule (§5) |
| F12 | §5.6's converted-command bullet states one form only: the command "calls a function in `workmain/services/` inside a `session_scope()` it owns, closes the scope, and passes the service's result". It states neither the unit-of-work form that §4.1 and `docs/ARCHITECTURE.md` §1 now describe, nor a converted command that calls no service, as `init` and `today` will. #258's spec and study did not amend §5.6. `status` will be the first command the bullet does not describe. | §5.6; §4.1; `docs/ARCHITECTURE.md` §1 Surfaces; `docs/archive/specs/UNIT_OF_WORK_SPEC.md`, `docs/archive/design/DESIGN_UNIT_OF_WORK.md` | Q3 |
| F13 | `status` and `today` print `date.today()` as `%A, %B %d, %Y`. The renderer formats a `date` as `%Y-%m-%d`. §5.6 gives the layout to `output.py`. | `interface.py:122`, `200`; `output.py:118-126` | Decided by rule (§5) |
| F14 | No code runs these three commands or reads their output: `run_workmain` is called with `time today`, and with no top-level command. Their stdout is not a contract, and their exit codes and streams do not change. | `git grep` over `workmain/`, `automation/`, `scripts/`, `deploy/`; `eod_workflow.py:364` | — |
| F15 | Three open issues cite the first attempt. #222 cites "#206's design study Q4". #255 cites its Q3 B. #256 names `tests/test_status_service.py`, `tests/test_top_level_commands.py::TestTopLevelCommands::test_status_renders_after_its_scope_closes`, and a command test with "service and render calls patched". That is the pre-#258 form, which current §6.2 replaces. | #222, #255, #256 bodies | Edited at close-out |
| F16 | `status`'s `Database ✓ Connected` row is fixed text, not a check. #256 replaces it. | `interface.py:143` | — |
| F17 | The test database supports §6.2's end-to-end command test. Probed under `_isolated_database` (throwaway test, deleted), all three held:<ul><li>A client seeded and set active through `db_session` and committed was printed by `status` run through `CliRunner` (exit 0).</li><li>A `UnitOfWork` entered inside a test saw a client that `db_session` had only flushed, because every session shares the test's one connection (`docs/standards/6-testing.md` §6.1).</li><li>`scope_open()` is false for `db_session`, so the unit of work's open-scope guard does not refuse a test.</li></ul> | probe output; `tests/conftest.py:118-180`; `connection.py:134-144` | — |
| F18 | Reading a client's attribute after `with uow:` exits raised `DetachedInstanceError` in the probe, as §4.2 states. The use case reads the name, ID and count while the unit of work is open, and returns plain values. | probe output; `docs/standards/4-database.md` §4.2 | — |
| F19 | The issue's first criterion says each of the three commands "builds a unit of work (#258), passes it to a use case". The same issue, under "Also in scope", says `init` and `today` "call no service". The criterion cannot hold for `init` and `today` as written. | issue body | Spec restates the criterion |
| F20 | `automation/architecture_check.py` passes at baseline: 0 new findings, with 36 covered by the unconverted-commands entry for #198. | run output | — |

**Application files the work touches:** `workmain/cli/interface.py`, `workmain/cli/output.py` (the fixed-text view, §5) and `workmain/services/clients_service.py` (F4). That is three, inside `docs/standards/2-git.md` §2.2's `hotfix/*` limit. A fourth escalates the work to `feature/*`.

## 4. Options

### Q1 — what `status` returns

The issue states two things that cannot both hold (F8): `status` returns a `Summary`, and output changes only where §5.6 says so. One of them gives way. Both options are interim, because #256 replaces everything `status` reports.

#### Option A — a result with the rows

- **Approach:** The use case returns the totals and a `Page` of the 45 component rows, building the two value-bearing rows itself. `STATUS` is a `ReportView` with one section. Over 30 lines, the rows print as a list (§5.6 layout). Ray chose this form on the first attempt (A1, 20261102), before `Summary` existed.
- **Pros:** Only the layout changes, which §5.6 permits. Every row keeps its value.
- **Cons:** The result is not a `Summary`. 43 rows of fixed text pass through a service as if it decided them, though the issue says only the lookup moves. The service test pins 45 rows that #256 removes.

#### Option B — a `Summary` for what is decided, fixed text for the rest

- **Approach:** The use case returns a `Summary` whose totals are the active client's name, its ID and the client count. `STATUS` is a `ReportView` with no sections, as `clients status` uses. The 45 rows and the footer are fixed text, declared in `interface.py`. The two value-bearing rows drop their values (`✓ clients set active`, `Clients configured`). The totals lines printed above them carry the same two values, so nothing is lost from the output.
- **Pros:** The service returns only what it decides, in the shape the issue states. Its test pins the lookup and the count, and nothing #256 removes. It reuses a pattern already in the code.
- **Cons:** Two rows change text, which §5.6 does not sanction. The issue's "Output changes only where §5.6 says so" yields for those two rows.

**Recommendation:** B. A puts fixed text into a service, and that is the defect #198 is removing. B's content change loses no value, because each one prints in the totals above.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The issue says `status` returns a `Summary`, and also that output changes only where §5.6 says so. Two of `status`'s fixed rows carry a run-time value, so the two cannot both hold (F8). Does `status` return a result holding the 45 rows, with only the layout changing (Option A)? Or does it return a `Summary`, with the fixed rows dropping the two values that the totals lines above them already print (Option B, recommended)? | |
| Q2 | `init` is neither a standard verb nor an orchestration command, and #198 has each conversion settle its name (F10). Approve `init` as a verb with a stated reason (recommended: it is the conventional first-run command, and renaming it breaks what users know)? Rename it? Or remove the command, which prints only reference text? Removing it is a change of scope. | |
| Q3 | §5.6's converted-command bullet states only the session-taking form, and #258 did not amend it (F12). Is it amended in this issue, with the text in the spec for your approval (recommended: `status` is the first command it would not describe)? Or is it carried to an issue of its own? | |

**Decided by rule.** Ray can reverse any of these. Each rests on the ground stated, not on the first attempt.

- **Where `status` gets the active client (F3):** the key, then `get_by_id`, unchanged. The issue states that "a conversion moves each decision into a service without changing it", and that "defects in what a command decides stay with the issues that own them". `clients_service.get_status` gives a different answer in the divergent state, which is #255's. This agrees with Ray's earlier ruling, recorded in #255's body. The service tests use only states in which every lookup agrees, because a test of the divergent state pins behaviour #255 changes (§6.2 rule 8).
- **The name-based decision (F2)** moves unchanged, on the same ground.
- **Where the use case lives (F4):** `clients_service`, the map's owner of the active client and client counts, as a function that takes a unit of work (§4.1). It returns plain values read inside the unit of work (F18).
- **How fixed text reaches the renderer (F7):** a new view type for fixed text in `workmain/cli/output.py`, which the map makes the owner of "every terminal rendering: views, `Renderer`". It has a `Renderer` method that takes it. Every `Renderer` method that prints content takes a declared view, and a `ReportView` would need a result with filters and totals that fixed text does not have. This agrees with Ray's earlier ruling, which #222 cites. #222 covers every view type `output.py` defines when its spec is written.
- **F11:** each command gets an `Examples:` block (§5.6).
- **F13:** the renderer formats the date (§5.6).
- **F9:** the recording renderer subclasses `Renderer`, so it passes Click's `isinstance` lookup, and goes in `tests/mocks/` beside `FakeUnitOfWork` (§7). The spec restates the parity criterion: every public method of `Renderer` is defined in the recording renderer's own class body, so a renderer that inherits a method fails.
- **F19:** the spec restates the first criterion: `status` builds a unit of work and passes it to its use case, and `init` and `today` call no service and open no session.
- **F15:** the bodies of #222, #255 and #256 are corrected at close-out, against what this issue ships.

## 6. Disposition

- Promoted to:
- Superseded by:

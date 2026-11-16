# Top-Level Commands — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261116
**Originating item:** Issue #206

---

## 1. Purpose

Issue #206 converts `workmain status`, `workmain today` and `workmain init` (`workmain/cli/interface.py`) to the direction #198 states. A command builds a unit of work and passes it to a use case in `workmain/services/`, which enters it. The command then hands the result to `workmain/cli/output.py`, and behaviour is tested at the service. This study re-measures the three commands on `origin/main` `91102e0`, records what has changed since the first attempt, and asks Ray the questions whose answers change the spec.

**The first attempt.** A first study and spec for this issue are kept only at the tag `archive/issue-206-attempt-1`. The spec was never approved, and neither artifact is on `main`. Since then #257 (the test database), #258 (the unit of work) and #259 (the shared `Summary` result) have closed, and the issue body was rewritten for the unit-of-work direction. Three rulings Ray made on the first study are cited by other open issues: Q3 B by #255, Q4 A by #222, and A1 by #256. Q3 B and Q4 A are unaffected by what has changed since, and this study carries them in §5. A1 is affected (finding F8), and Q1 asks about it again.

## 2. Scope of the read

Read: `workmain/cli/interface.py`; `workmain/cli/output.py`; `workmain/services/clients_service.py`, `results.py` and `unit_of_work.py`; `ClientRepository` and `SystemStateRepository`; `tests/mocks/fake_unit_of_work.py`; `tests/test_cli_conventions.py`; `tests/test_clients_commands.py`, read as the current command-test form; `docs/ARCHITECTURE.md`; `docs/standards/` §1, §2, §3, §4, §5 and §6; issues #198, #222, #255, #256 and #279; Click 8.1.7's `Context.ensure_object` and `find_object`.

Not read: the other command groups, beyond the grep in F14 for callers of these three commands, and `eod`, which moved to #254 (issue body).

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The issue's census still holds. `init` and `today` print fixed Rich lines. `status` opens a `session_scope()`, reads the active client and the number of clients, and prints a title, an active-client line, a 45-row table, and footer lines. The module imports Rich and the two repositories, and holds a module `Console`. | `interface.py:11-16`, `59`; `init` `105-116`; `status` `119-194`; `today` `197-270` | — |
| F2 | `status` decides on whether the client's *name* is truthy, not on whether a client was found: `if active_client_name:` and `active_client_name or "Internal"`. A client named `""` prints as internal. A conversion moves this decision without changing it (issue body). | `interface.py:132-137`, `183` | Low |
| F3 | `status` finds the active client with the `active_client_id` key, then `get_by_id`. `clients status` uses `ClientRepository.get_active`, which falls back to the first client with `is_active` set. The two disagree when the key is unset or names a deleted client while another client is still flagged. That divergence belongs to #255. | `interface.py:129-130`; `client_repository.py:188-200`; `clients_service.get_status` `182-189` | Owned by #255 |
| F4 | `docs/ARCHITECTURE.md` §2 names `workmain/services/clients_service.py` as the owner of "client records, the active client, and client counts". These are the only two values `status` reads at run time. The map names no status or overview service. The first attempt's `status_service.py` was a Spanner decision, not Ray's, and had no owner in the map. | `docs/ARCHITECTURE.md` §2 Application | Decided by rule (§5) |
| F5 | No surface builds a unit of work yet: `git grep -nE 'UnitOfWork\(' -- workmain/` finds only `unit_of_work.py`. `status` will be the first command to build one and the first use case a command calls. `clients_service` still takes a session until #279. `docs/standards/4-database.md` §4.1 allows the two forms side by side. | grep; `clients_service.py:97-206`; §4.1 | — |
| F6 | `FakeUnitOfWork.REPOSITORIES` holds only `system_state`. `status`'s use case calls `clients.get_by_id` and `clients.list_all`, so it needs a fake `ClientRepository` with those two methods. Each needs the signature-parity test and the behaviour tests run against both the fake and the real repository that `docs/standards/6-testing.md` §6.2 sets. #279 lists both methods among the 9 it fakes. Done here, they leave #279 seven. | `fake_unit_of_work.py:80-82`; `tests/test_fake_unit_of_work.py:171`, `182-250`; #279 body | — |
| F7 | `Renderer`'s public methods are `changed`, `cancelled`, `nothing_to_do`, `warning`, `collection`, `pick`, `report` and `record`. None of them prints fixed text. A `ReportView` with no sections and `totals_when_empty=True` prints a `Summary`: `clients status` already does, through `STATUS`. | `output.py:165-411`; `clients.py:59-68` | — |
| F8 | `Summary` holds totals and filters and no rows. The issue says `status` returns a `Summary`, but A1 puts the 45 component rows in a `ReportView` section, which reads a `Page` from the result. The two cannot both hold. 43 rows are fixed text. Two carry a run-time value: `├─ Active Context` holds the client's name and `└─ Clients Configured` holds the count. | `results.py:27-39`; `interface.py:143-189`, `186`, `189`; issue body "Also in scope" | Q1 |
| F9 | No recording renderer exists in `tests/`, and no command test yet takes §6.2's form: nothing patched, the real service run. `tests/test_clients_commands.py:46-57` patches the service and passes `Mock(spec=Renderer)`. `cli` calls `ctx.ensure_object(Renderer)`, and `pass_renderer` is `make_pass_decorator(Renderer, ensure=True)`. Click 8.1.7 finds the object with `isinstance`, and replaces an `obj` that is not a `Renderer` with a real `Renderer()`, which prints. So the recording renderer must pass `isinstance(_, Renderer)`. If it subclasses `Renderer`, it inherits every public method, and the issue's check ("a test comparing the recording renderer's public methods with `Renderer`'s") passes even when it overrides none, so it cannot fail. The spec restates that criterion under `docs/standards/1-workflow.md` §1.2. | `interface.py:102`; `output.py` `pass_renderer`; Click `Context.find_object` | Spec restates the criterion |
| F10 | `init` is in `EXISTING_EXCEPTIONS`. `TOP_LEVEL` permits only `eod`, `status` and `today`. #198 says each conversion decides its group's names: it renames, approves the name as a verb, or keeps it with a stated reason, and removes the name from that list. `init` is not a standard verb, and §5.1 permits a top-level command only for an orchestration workflow. | `tests/test_cli_conventions.py:39-40`, `52`; `docs/standards/5-cli.md` §5.1, §5.3; #198 body | Q2 |
| F11 | None of the three docstrings has the `Examples:` block that §5.6 requires. | `interface.py:107`, `121`, `199`; `docs/standards/5-cli.md` §5.6 | Decided by rule (§5) |
| F12 | §5.6's converted-command bullet states only the session-taking form: the command "calls a function in `workmain/services/` inside a `session_scope()` it owns". It does not state the unit-of-work form that §4.1 and `docs/ARCHITECTURE.md` §1 describe, or a converted command that calls no service, as `init` and `today` do. Under the issue's direction, `status` will be the first converted command that matches neither the bullet's wording nor any example of it. | `docs/standards/5-cli.md` §5.6; §4.1; `docs/ARCHITECTURE.md` §1 Surfaces | Q3 |
| F13 | `status` and `today` print `date.today()` as `%A, %B %d, %Y`. The renderer formats a `date` as `%Y-%m-%d`. §5.6 makes the layout `output.py`'s, so the date printed through the renderer changes format. | `interface.py:122`, `200`; `output.py:118-126` | Decided by rule (§5) |
| F14 | No code runs these three commands or reads their output. `run_workmain` is called with `time today` and with no top-level command. Their stdout is therefore not a contract, and their exit codes and streams do not change. | `git grep` over `workmain/`, `automation/`, `scripts/`, `deploy/`; `eod_workflow.py:364` | — |
| F15 | Three open issues cite the first attempt. #222 cites "#206's design study Q4". #255 cites Q3 B. #256 names `tests/test_status_service.py`, the command test `tests/test_top_level_commands.py::TestTopLevelCommands::test_status_renders_after_its_scope_closes`, and a command test with "service and render calls patched". That is the pre-#258 form, which current §6.2 replaces. | #222, #255, #256 bodies | Edited at close-out |
| F16 | `status`'s `Database ✓ Connected` row is fixed text, not a check. It is carried over unchanged, and #256 replaces it. | `interface.py:143` | — |

**Application files the work touches:** `workmain/cli/interface.py`, `workmain/cli/output.py` (the view type for fixed text, from Q4 A) and `workmain/services/clients_service.py` (F4). That is three, inside `docs/standards/2-git.md` §2.2's `hotfix/*` limit. A fourth escalates the work to `feature/*`.

## 4. Options

Q1 is the only question with options. Both options carry Q4 A: fixed text goes through a new view for fixed text, which the first attempt called `GuideView`. Both are interim, because #256 replaces everything `status` reports.

### Option A — A1 as ruled, 20261102

- **Approach:** The use case returns the active client and the count as totals, with the 45 component rows as a `Page`, and builds the two value-bearing rows itself. `STATUS` is a `ReportView` with one section. Over 30 lines, the rows print as a list of about 135 lines. The footer is a guide.
- **Pros:** Ray has already ruled it. Every row keeps its value.
- **Cons:** The result is not a `Summary`, which the rewritten issue body states. 43 rows of fixed text go through a service as if the service decided them, but the issue says only the lookup moves into a service. The service test then pins 45 fixed rows that #256 removes.

### Option B — `Summary` for the decision, a guide for the fixed rows

- **Approach:** The use case returns `Summary` with the totals: active client name, ID and count. `STATUS` is a `ReportView` with no sections that prints those totals, as `clients status` does. The 45 component rows and the footer are fixed text in a guide constant in `interface.py`. The two value-bearing rows lose their values (`✓ clients set active`, `Clients configured`), because the totals lines print those values just above.
- **Pros:** The service returns only what it decides, in the shape the issue states. The service test pins the lookup and the count and nothing #256 removes. Both questions are settled by one view type, and the pattern is one the code already has.
- **Cons:** The two rows change text. The table prints as guide lines. Output changes under either option.

**Recommendation:** B. It is the shape the issue now states, and it keeps what the service decides apart from fixed text. With A, the service and its test carry 43 rows that nothing decides.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The issue says `status` returns a `Summary`, but A1 puts the 45 component rows in the service result (F8). Does `status` keep A1 (Option A), or return a `Summary` with the fixed rows as a guide (Option B, recommended)? | |
| Q2 | `init` is neither a standard verb nor an orchestration command, and #198 has each conversion settle its name (F10). Approve `init` as a verb with a stated reason (recommended: the conventional first-run command, and renaming breaks what users know)? Rename it? Or remove the command, which prints only stale text? Removal is a scope change for Ray. | |
| Q3 | §5.6's converted-command bullet states only the session-taking form (F12). Is it amended in this issue, with the text in the spec for your approval (recommended: `status` is the first command it would mis-describe)? Or is it carried to an issue of its own? | |
| Q4 | Carried: where `status` gets the active client. | Ray, 20261030 (first attempt, Q3): **B**. The key, then `get_by_id`, moved unchanged. #255 replaces the lookup. Service tests use only states in which every lookup agrees. |
| Q5 | Carried: how fixed text reaches the renderer. | Ray, 20261102 (first attempt, Q4): **A**. A new view type for fixed text. #222 covers every view type `output.py` defines. |

**Decided by rule** (Ray can reverse any of these):

- **F4:** the use case goes in `clients_service`, the map's owner, as a function that takes a unit of work. A second lookup beside `get_status` puts both lookups #255 replaces in one module.
- **F11:** each command gets an `Examples:` block (§5.6).
- **F13:** the renderer formats the date (§5.6).
- **F9:** the recording renderer goes in `tests/mocks/`, beside `FakeUnitOfWork` (§7). The spec restates the parity criterion so that a renderer that overrides none of the methods fails it.
- **F15:** the issue bodies of #222, #255 and #256 are corrected at close-out, against what this issue ships.

## 6. Disposition

- Promoted to:
- Superseded by:

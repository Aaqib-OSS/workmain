# Shared Status Result — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261114
**Originating item:** Issue #259

---

## 1. Purpose

`workmain/services/calendar_service.py` and `workmain/services/clients_service.py` each declare a result that holds only `filters` and `totals`, and each declares a totals type named `StatusTotals`. `docs/ARCHITECTURE.md` section 1, Result types, requires one generic type in `workmain/services/results.py` for a result shape several services share, and names unique to their domain for a domain's own types. Ray set the direction on 20261102 (option A of the architecture map decisions): one generic "filters plus totals" result beside `Page`, which both services return, and a renamed totals type in each service. This study measures what the change reaches and sets out the two names the spec needs.

## 2. Scope of the read

Read on `origin/main` at `2897bcf`, 20261114:

- `workmain/services/results.py` in full. `workmain/services/calendar_service.py` and `workmain/services/clients_service.py`: the result dataclasses, `get_status`, and `set_active`.
- Every class under `workmain/` that has a `filters` or `totals` field, found by an AST walk of every module. Every class name defined more than once under `workmain/`, found the same way.
- Every reference in the repository to `StatusTotals`, `CalendarStatus` and `ClientStatus` (`git grep -nw`). Every call to `get_status(` and `set_active(` in `workmain/`, `tests/`, `automation/` and `scripts/`, each confirmed by what the call is made on.
- `workmain/cli/output.py`: `ReportView`, `Renderer.report` and `_report_body`. `workmain/cli/commands/calendar.py` and `workmain/cli/commands/clients.py`: `STATUS` and every command that renders it.
- `tests/test_calendar.py`, `tests/test_clients_commands.py`, `tests/test_calendar_service.py`, `tests/test_clients_service.py` (the status and active tests), and the `report` tests in `tests/test_output.py`.
- `automation/architecture_check.py` `check_duplicates` and `read_deficiencies`, and a run of it. `docs/ARCHITECTURE.md` sections 1–3.
- Open issues searched by `StatusTotals`, `CalendarStatus`, `ClientStatus`, `results.py`, `get_status` and `filters plus totals`. Read #206, #279 and #282.

Not read: other services' result types beyond their field names. Any service whose results add sections, rows or warnings to `filters` and `totals` is a different shape (F2).

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | Each service declares a totals type named `StatusTotals` and a result holding only `filters` and `totals`. `StatusTotals` is the only class name defined twice under `workmain/`. | `workmain/services/calendar_service.py:65` `StatusTotals(events: int, last_import: Optional[date], live_sync: str)`, `:72` `CalendarStatus(filters: Filters, totals: StatusTotals)`; `workmain/services/clients_service.py:69` `StatusTotals(client: str, client_id: Optional[int])`, `:77` `ClientStatus(filters, totals: StatusTotals)`; AST walk of `workmain/` | High |
| F2 | The census matches the issue: `CalendarStatus` and `ClientStatus` are the only classes whose fields are exactly `filters` and `totals`. Seven other results carry `filters` and `totals` plus sections, rows, warnings or a question, so they are a different shape and are not part of this change. | AST walk: `ai_cost_service.CostReport`, `calendar_service.ImportPreview`, `calendar_service.ImportResult`, `clients_service.DeletePreview`, `clockify_service.PushResult`, `clockify_service.PullResult` each add fields; `results.Page` is `rows, total, filters` | Medium |
| F3 | `Page` is the precedent in `results.py`: a frozen generic dataclass with `filters: Tuple[Tuple[str, object], ...] = ()` as its last field, with the type written out and not aliased. `calendar_service` has its own module alias `Filters` for the same type, which its other results also use. | `workmain/services/results.py:12-24` `Page`; `workmain/services/calendar_service.py:33` `Filters = Tuple[Tuple[str, object], ...]` | Low |
| F4 | Both constructors pass `filters=()`. Calendar builds its result by position: `CalendarStatus((), StatusTotals(...))`. Clients builds it by keyword. | `workmain/services/calendar_service.py:175-177`; `workmain/services/clients_service.py:194-197` | Low |
| F5 | `Renderer.report` reads a result only by attribute name. It takes `result: Any`, reads `result.filters` and the attribute `ReportView.totals_field` names, which is `"totals"` in both `STATUS` views. A generic with fields named `filters` and `totals` needs no change in `workmain/cli/`. | `workmain/cli/output.py:333` `report(self, view, result: Any, ...)`, `:355-358` `_report_body`; `workmain/cli/commands/calendar.py:49-59` `STATUS`; `workmain/cli/commands/clients.py:59-68` `STATUS` | High |
| F6 | Three commands render a status result, not two. `clients set active` renders `clients_service.set_active`'s `ClientStatus` through the same `STATUS` view as `clients status`. The issue's third criterion names `calendar status` and `clients status` only. | `workmain/cli/commands/calendar.py:151-152`; `workmain/cli/commands/clients.py:195-196` (`set active`), `:213-214` (`status`); `workmain/services/clients_service.py:200` `set_active(...) -> ClientStatus` | High |
| F7 | The issue's third criterion is checked by the command tests, and those tests cannot show the property. `test_c2_status`, `test_c5_status` and `test_c6_set_active` patch the service function and the renderer, and assert only that `renderer.report` was called with `STATUS` and the mock's return value. They pass whatever the result type renders as. No test renders either `STATUS` view through a real `Renderer`. The `report` tests in `tests/test_output.py` render synthetic views and results built in that file. | `tests/test_calendar.py:84-89` `test_c2_status`; `tests/test_clients_commands.py:102-115` `test_c5_status`, `test_c6_set_active`; `tests/test_output.py:320-448` (`REPORT`, `_result`) | High |
| F8 | The service tests that build these types are in `tests/test_clients_service.py`, which constructs `clients_service.StatusTotals` at lines 220, 234, 246, 260, 271, 283 and 290. `tests/test_calendar_service.py` `TestStatus` reads `status.filters` and `status.totals.<field>` and names no type. No reference in `automation/` or `scripts/`. | `git grep -nw` of the three names; `tests/test_calendar_service.py:118-135` | Medium |
| F9 | The old names also appear in `docs/archive/specs/CALENDAR_COMMANDS_SPEC.md:113` and `docs/archive/specs/CLIENTS_COMMANDS_SPEC.md:101-103` and `:239`. These are historical records and stay as written (`docs/standards/1-workflow.md` §1.5). | `git grep -nw` | Low |
| F10 | The deficiency entry is the map's section 3 "Per-service status types — #259", whose Covers sentence names both service modules. The check reports one finding under it, and `New findings: 0`. Once the duplicate class name is gone and the entry is deleted, the check has nothing to report there. | `docs/ARCHITECTURE.md:141`; `automation/architecture_check.py` `check_duplicates`, `read_deficiencies`; run output "Per-service status types — #259: 1", "New findings: 0" | Medium |
| F11 | #206 depends on this work: its `status` command "returns the shared filters-plus-totals result that #259 adds to `workmain/services/results.py`", and #259 is linked as blocking #206. The generic's name is therefore a contract a third service will use. | Issue #206 body, Also in scope; `gh api .../issues/259/dependencies/blocking` → `#206 open` | Medium |
| F12 | #279 and #282 change the parameters of these same `get_status` and `set_active` functions (a session becomes a unit of work), not their return types. They don't overlap with this change's design. Whichever merges second rebases onto the other. | Issues #279 and #282, "What this issue converts" | Low |
| F13 | The change touches three application files: `workmain/services/results.py`, `workmain/services/calendar_service.py` and `workmain/services/clients_service.py`. That is within the `hotfix/*` limit (`docs/standards/2-git.md` §2.2). Tests and `docs/ARCHITECTURE.md` are companions. | F5, F8 | Low |
| F14 | Suite baseline on this branch: `1708 passed`. | `pytest -q`, 20261114 | Low |

## 4. Options

### Where the generic's fields go

Two rules settle the field order and default, so this isn't an open question. The generic follows the `Page` precedent in the same module (F3): a frozen dataclass, generic over its totals type, with `totals: T` first and `filters: Tuple[Tuple[str, object], ...] = ()` last, the type written out as `Page` writes it. Calendar's positional construction (F4) changes with it. `calendar_service`'s own `Filters` alias stays, because its other results still use it.

### What the issue's third criterion is checked by

A rule settles this too: `docs/standards/1-workflow.md` §1.2, that a criterion's check must be able to produce the answer it states, and that a criterion verifying changed behaviour covers every entry path. The command tests can't show that output is unchanged (F7), and the criterion leaves out `clients set active` (F6). The spec restates the criterion in its §5 for all three commands. The check is a rendering test for each `STATUS` view: it hands a result built from the service types to a real `Renderer` and asserts the exact text printed. It is written and passing before the types change, and passes unchanged afterwards apart from the renamed types. The issue body's edit is made at close-out.

### Q1 — the generic's name

- **Option A — `Summary[T]`.** It names the shape, a result with no rows, only totals and the filters behind them, and not the one use it has today. No class or model under `workmain/` uses the name.
  - **Pros:** reads correctly for #206's `status` and for any later status-like result. It pairs with `Page` as the second shape in `results.py`.
  - **Cons:** "summary" is also a word for AI-generated report text elsewhere in the project. No class carries that name, but the word is in prose.
- **Option B — `Status[T]`.** It names the use: every current and planned caller is a `get_status`.
  - **Pros:** matches the function names that return it.
  - **Cons:** the map rule is about a shared shape, not a shared use. A non-status result with this shape would have to adopt a misleading name or add a second generic. It also collides in reading with the `TaskStatus` model (`workmain/database/models.py:327`), the status fields on models, and spec `**Status:**` vocabulary.
- **Option C — `Totals[T]`.** It names the content.
  - **Cons:** every totals type in the project is already `<Something>Totals`, so `Totals[CalendarStatusTotals]` reads as totals inside totals, and the wrapper is easily mistaken for the inner type.

**Recommendation:** Option A, `Summary[T]`. The map's rule is stated as a shared shape, and `Summary` is the only candidate that names the shape without colliding with an existing type naming idiom.

### Q2 — the two totals types' names

The map requires names unique to the domain. The project's idiom is `<role>Totals` (`PreviewTotals`, `ImportTotals`, `LinkedTotals`, `PushTotals`, `PullTotals`, `CostTotals`).

- **Option A — `CalendarStatusTotals` and `ClientStatusTotals`.** Domain prefix plus the existing name.
  - **Pros:** the smallest rename. Each name still says what produces it (`get_status`), and both follow the idiom.
- **Option B — names by content: `OutlookImportTotals` and `ActiveClientTotals`.**
  - **Pros:** says what the numbers are.
  - **Cons:** `clients_service.set_active` also returns the client type, so "active" fits there. But the calendar totals include `live_sync`, which isn't an import figure, so `OutlookImportTotals` misdescribes one of its three fields.

**Recommendation:** Option A. It is the rename the direction asks for and nothing more, and Option B's calendar name is inaccurate.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | What is the generic "filters plus totals" result in `workmain/services/results.py` named, given that #206's `status` will also return it: `Summary[T]`, `Status[T]` or `Totals[T]`? | |
| Q2 | What are the two renamed totals types named: `CalendarStatusTotals` and `ClientStatusTotals`, or `OutlookImportTotals` and `ActiveClientTotals`? | |

## 6. Disposition

- Promoted to:
- Superseded by:

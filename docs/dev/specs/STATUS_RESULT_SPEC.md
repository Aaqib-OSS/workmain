# Shared Status Result — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261114
**Branch:** `hotfix/issue-259-status-result` (from `main`)
**Target release:** set by `/closeout`
**Originating item:** Issue #259
**Design study:** `../design/DESIGN_STATUS_RESULT.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261102 | Ray | Direction for #259, architecture map decisions option A: one generic "filters plus totals" result in `workmain/services/results.py` beside `Page`, returned by both services, with each service's totals type renamed to a name unique to its domain. | Adopted; DR1, DR3. |
| 20261114 | Ray | Branch type: `hotfix/*`. | Adopted; header. |
| 20261114 | Ray | Design study Q1: the generic is `Summary[T]`. | Adopted; DR1, Step 1. |
| 20261114 | Ray | Design study Q2: the totals types are `CalendarStatusTotals` and `ClientStatusTotals`. | Adopted; DR3, Steps 1 and 2. |
| 20261114 | Ray | Design study Q1 and Q2: `CalendarStatus`, `ClientStatus` and both `StatusTotals` are deleted, not kept as aliases. | Adopted; DR2, AC1.1. |
| 20261114 | Ray | Step 1's fail-first run would fail with an `ImportError` at collection, not an `AssertionError` from `test_s5_status`, if the test imports `Summary` before `results.py` defines it. | Adopted; Step 1 adds `Summary` before the assertion, and the fail-first runs in Steps 1 and 2, AC1.2 and §6 require an `AssertionError`. |
| 20261114 | Spanner | `Summary`'s fields follow `Page`, the precedent in the same module (design study F3): `totals: T` first, `filters` last, defaulting to `()`. | Adopted; DR4. |
| 20261114 | Spanner | The issue's third criterion is checked by command tests that mock the service and the renderer, so they can't show output unchanged (design study F7). The criterion also leaves out `clients set active` (F6). Restated in §5 as AC3.1–AC3.3 under `docs/standards/1-workflow.md` §1.2. A test rendering the real views is ruled out by `docs/standards/6-testing.md` §6.2. The issue body's edit is made at close-out. | Adopted; §5. |
| 20261114 | Caliper | 3, Spec defect, blocking: Step 1.4 renames `StatusTotals` to `CalendarStatusTotals`, and DR3 says the type "changes only in name" and keeps its "docstring meaning". The calendar class has no docstring, though. `pyproject.toml` selects D101 for `workmain/**`, and `ruff check --select D101 workmain/services/calendar_service.py` reports `D101 Missing docstring in public class` at `:65 class StatusTotals`. The rename changes that line, so `automation/style_check.py` flags it, and the post-implementation review turns that into an I6 finding. Anvil has to guess between two options: add a docstring, which DR3 seems to forbid, or leave the violation. (A related trap: if Step 1.1 is read as copying the *form* of `Page`'s docstring, it fails D213, because `ruff check workmain/services/results.py` reports D213 on `Page`.) | Accepted. Verified: ruff reports D101 at `workmain/services/calendar_service.py:65` and D213 at `workmain/services/results.py:13`. DR3 now changes the totals types in name and docstring only: their fields stay as they are, and `CalendarStatusTotals` gains a class docstring. Step 1.1 requires `Summary`'s docstring to pass D205 and D213 rather than copy `Page`'s layout. §4 requires every changed line to pass `automation/style_check.py`. |
| 20261114 | Caliper | 1, Spec defect, non-blocking: AC3.2's criterion is a property of running code (what the three functions return). Its check still includes "a stated reading by Ray" of a test diff. `docs/standards/1-workflow.md` §1.2 allows a Ray reading only "where a criterion is a property of a document rather than of running code". A mechanical check exists. For example, `diff <(git show origin/main:tests/test_clients_service.py \| sed 's/StatusTotals/ClientStatusTotals/') tests/test_clients_service.py` should show only the added import and `assert type(status) is Summary` lines, and the same for `tests/test_calendar_service.py` without the `sed`. | Accepted. AC3.2 is checked by the AC3.2 command in §5, which diffs both files against the merge base and fails on any line except the three Steps 1 and 2 add. Tried on this branch before the change: it flags every unrenamed `StatusTotals` line, so it can return both answers. Steps 1.2 and 2.1 fix the import as one line of its own, so the command can match it. |
| 20261114 | Caliper | 7, Spec defect, non-blocking: AC3.2 claims `set_active` returns "the same `filters`", but no service test asserts `filters` on `set_active`'s result. `test_s17_sets_the_active_client_by_name` and `test_s18_internal_clears_the_context` assert only `status.totals`. `test_s20_reports_the_active_client` asserts `status.filters == ()` for `get_status` alone (`tests/test_clients_service.py:228-246`, `:275-276`). A `set_active` that returned `Summary(totals, filters=(...))` would pass every listed check. Step 2.3 does fix the build ("`set_active` still returns `get_status(session)`"), but the criterion's check can't see a departure from it. | Accepted. Step 2.1 adds `assert status.filters == ()` to `test_s17_sets_the_active_client_by_name`, and the AC3.2 command allows that line. |
| 20261114 | Caliper | 7, Spec defect, non-blocking: AC2.2's property is "No class name is defined twice under `workmain/`". Its check, `New findings: 0` with no `#259` line, can't see every form of that. `main()` in `automation/architecture_check.py` files each finding under the first map section 3 entry whose Covers pattern matches the duplicate's first defining module. So a duplicate first defined under `workmain/cli/` (#198), `workmain/daemon/` (#261) or another covered path is counted under that entry as known, not as new. Either the property needs narrowing to what the check proves, or the check needs to run `check_duplicates` on its own and require it to return nothing. | Accepted, second form. Verified in `main()`: a finding is filed under the first entry whose Covers pattern matches its path. AC2.2 now adds the AC2.2 command in §5, which runs `check_duplicates` on its own and exits 1 when anything is returned. Tried on this branch before the change: it returns the `StatusTotals` pair and exits 1. |
| 20261114 | Caliper | 2, Spec defect, non-blocking: two pieces of §2 evidence don't match what they cite. (a) The call-site row says `git grep -nE "['\"](get_status\|set_active)['\"]"` "matches only the command tests' patch keys … and `tests/test_clockify.py`'s". Run over the whole repository, it also matches `docs/archive/specs/CLIENTS_COMMANDS_SPEC.md:260`. (b) The command-test row cites `tests/test_clients_commands.py:102-115` for `test_c5_status` and `test_c6_set_active`, but `test_c6_set_active`'s `renderer.report.assert_called_once_with` is at `:116`. | Accepted, both verified. (a) The row now names the search's scope and the archived spec's table row, which is a historical record and not a caller. (b) The range is now `:102-116`. |
| 20261114 | Caliper | Pass at dc930c4, full: 28 items checked, 1 blocking, 4 non-blocking. | n/a |
| 20261114 | Caliper | 3, Spec defect, non-blocking: Step 2.3 ends "No assertion changes beyond those step 1 adds." Inside Step 2, "step 1" can mean Step 2's own item 1 or the spec's Step 1. Step 1 adds no assertion to `tests/test_clients_service.py`, and Step 2.3 itself adds none, so either reading leads to the same build. But the sentence uses the name of a defined step to mean a sub-item. Every other in-step reference spells out what it means (Step 1.3: "on that line"; Step 2's opening: "`Summary` exists from Step 1"). | Accepted. Step 2.3 now reads "beyond those item 1 of this step adds". |
| 20261114 | Caliper | Pass at c9afd97, changes since dc930c4: 22 items checked, 0 blocking, 1 non-blocking. | n/a |
| 20261114 | Caliper (post-implementation) | No findings. | n/a |

---

## 1. Scope

**In scope:**

- `workmain/services/results.py`: add `Summary`.
- `workmain/services/calendar_service.py`: rename `StatusTotals` to `CalendarStatusTotals`, delete `CalendarStatus`, and have `get_status` return `Summary[CalendarStatusTotals]`.
- `workmain/services/clients_service.py`: rename `StatusTotals` to `ClientStatusTotals`, delete `ClientStatus`, and have `get_status` and `set_active` return `Summary[ClientStatusTotals]`.
- `tests/test_calendar_service.py` and `tests/test_clients_service.py`: the renamed types, an assertion of the result's type, and an assertion of `set_active`'s `filters`.
- `docs/ARCHITECTURE.md` section 3: delete the "Per-service status types — #259" entry.

**Out of scope:**

- `workmain/cli/`: no change (DR5). `Renderer.report` and both `STATUS` views read the result by attribute name, and the attribute names don't change (§2).
- The seven results that carry `filters` and `totals` plus other fields (design study F2). They are a different shape.
- `calendar_service`'s module alias `Filters`, which its other results still use.
- Converting either service to the unit of work (#279, #282) and #206's `status`, which will return `Summary` once this ships.
- `docs/archive/specs/CALENDAR_COMMANDS_SPEC.md` and `docs/archive/specs/CLIENTS_COMMANDS_SPEC.md`, which name the old types and stay as written (`docs/standards/1-workflow.md` §1.5).
- `docs/ARCHITECTURE.md` section 1, Result types. Its rule already states this design and stays as written.

## 2. Verified current state

Read on `origin/main` at `2897bcf`, 20261114.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `results.py` holds one type, `Page`: a frozen generic dataclass whose last field is `filters: Tuple[Tuple[str, object], ...] = ()`. Its module docstring is "Result types shared by service-layer collection queries." | `workmain/services/results.py:1-24` |
| Calendar's totals and result: `StatusTotals(events: int, last_import: Optional[date], live_sync: str)` and `CalendarStatus(filters: Filters, totals: StatusTotals)`. `get_status(session: Session) -> CalendarStatus` builds `CalendarStatus((), StatusTotals(count, latest.date() if latest else None, LIVE_SYNC))`. | `workmain/services/calendar_service.py:64-74`, `:172-177` |
| Clients' totals and result: `StatusTotals(client: str, client_id: Optional[int])` and `ClientStatus(filters: Tuple[Tuple[str, object], ...], totals: StatusTotals)`. `get_status(session) -> ClientStatus` returns `ClientStatus(filters=(), totals=totals)`. `set_active(session, name) -> ClientStatus` returns `get_status(session)`. | `workmain/services/clients_service.py:68-81`, `:190-214` |
| `Renderer.report` takes `result: Any`. `_report_body` reads `result.filters`, `getattr(result, view.totals_field)`, and each `Field.field` of that object through `_cell`. It reads no other attribute of the result and checks no type when the view has no sections. | `workmain/cli/output.py:333-374` `report`, `_report_body` |
| Both `STATUS` views have `totals_field` `"totals"` and no sections. The calendar view reads `events`, `last_import` and `live_sync`; the clients view reads `client` and `client_id`. | `workmain/cli/commands/calendar.py:49-59`; `workmain/cli/commands/clients.py:59-68` |
| Every reference to the three type names, found by `git grep -nwE 'StatusTotals\|CalendarStatus\|ClientStatus'` over the whole repository | `workmain/services/calendar_service.py:65,72,74,172,175,176`; `workmain/services/clients_service.py:69,77,81,190,194,196,197,200`; `tests/test_clients_service.py:220,234,246,260,271,283,290`; `docs/ARCHITECTURE.md:141`; `docs/archive/specs/CALENDAR_COMMANDS_SPEC.md:113`; `docs/archive/specs/CLIENTS_COMMANDS_SPEC.md:101,102,103,239` |
| Call sites of the changed functions, found by `git grep -nE '(calendar_service\|clients_service)\.(get_status\|set_active)\|\bget_status\(\|\bset_active\(' -- workmain tests automation scripts`. Each was confirmed by what the call is made on: calls on `ClientRepository` and on `clockify_service`, and `automation/architecture_check_test.py`'s fixture source, are not callers. No reference by `getattr` or as an uncalled name was found. Over the whole repository, `git grep -nE "['\"](get_status\|set_active)['\"]"` matches only three things: the command tests' patch keys, below; those in `tests/test_clockify.py`, which patch `clockify_service`; and `docs/archive/specs/CLIENTS_COMMANDS_SPEC.md:260`, a historical spec's test table. | `calendar_service.get_status`: `workmain/cli/commands/calendar.py:151`; `tests/test_calendar_service.py:122,133`; patched by name in `tests/test_calendar.py` (`mocks["get_status"]`). `clients_service.get_status`: `workmain/cli/commands/clients.py:213`; `workmain/services/clients_service.py:214`; `tests/test_clients_service.py:219,259,269,281,288`; patched in `tests/test_clients_commands.py` (`mocks["get_status"]`). `clients_service.set_active`: `workmain/cli/commands/clients.py:195`; `tests/test_clients_service.py:175,186,213,232,242,244,251,254,267`; patched in `tests/test_clients_commands.py` (`mocks["set_active"]`). |
| Every caller reads the result only as `.filters` and `.totals`, or hands it to `renderer.report` | `workmain/cli/commands/calendar.py:152`; `workmain/cli/commands/clients.py:196,214`; `tests/test_calendar_service.py:123-126,134-135`; `tests/test_clients_service.py` lines above |
| The command tests patch the service function and the renderer, and assert only `renderer.report.assert_called_once_with(STATUS, mocks[...].return_value)` | `tests/test_calendar.py:84-89` `TestCalendarCommands::test_c2_status`; `tests/test_clients_commands.py:102-116` `test_c5_status`, `test_c6_set_active` |
| Docstring rules on the changed lines: `pyproject.toml` selects D101, D205 and D213 for `workmain/**`. `calendar_service.StatusTotals` has no docstring (D101), and `Page`'s docstring starts its summary on the opening line (D213). `clients_service.StatusTotals` has a one-line docstring. `automation/style_check.py` checks only the lines a branch adds or changes. | `ruff check --select D101 workmain/services/calendar_service.py` → `:65:7 D101`; `ruff check workmain/services/results.py` → `:13:5 D213`; `workmain/services/clients_service.py:70`; `automation/style_check.py` module docstring |
| `StatusTotals` is the only class name defined twice under `workmain/`. The check reports it under the section 3 entry "Per-service status types — #259" (1 finding) and prints `New findings: 0`. | `automation/architecture_check.py` `check_duplicates`; `docs/ARCHITECTURE.md:141`; a run on `2897bcf` |
| Suite baseline | `1708 passed, 0 failed, 0 skipped` — `CHANGELOG.md` 1.58.3, and `pytest` on this branch, 20261114 |

## 3. Design rules

- **DR1 — One status result.** `workmain/services/results.py` `Summary` is the only result made of `filters` and `totals` alone. `calendar_service.get_status`, `clients_service.get_status` and `clients_service.set_active` return it, and no service declares its own wrapper of that shape. Owner: `workmain/services/results.py`, "the result types services share" (`docs/ARCHITECTURE.md` section 2).
- **DR2 — Old names are deleted.** `CalendarStatus`, `ClientStatus` and both `StatusTotals` leave the code entirely. None stays as an alias, a re-export or a name in `__all__`.
- **DR3 — Totals types change in name and docstring only.** `CalendarStatusTotals` keeps `calendar_service.StatusTotals`'s fields, in their order, with their types, and gains a class docstring, which `StatusTotals` lacked (D101, `docs/standards/3-code.md` §3.5). `ClientStatusTotals` keeps `clients_service.StatusTotals`'s fields and the meaning of its docstring. Each stays a frozen dataclass in its own service module, which owns it (`docs/ARCHITECTURE.md` section 2).
- **DR4 — `Summary` follows `Page`.** A frozen dataclass, `Generic[T]`, with `totals: T` and then `filters: Tuple[Tuple[str, object], ...] = ()`, the type written out as `Page` writes it.
- **DR5 — Nothing under `workmain/cli/` changes.** The renderer and the views already read the result by attribute (§2). A step that seems to need a change there is a departure.

Anything these rules and the steps don't decide is a departure: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `Summary`, and `calendar_service` returns it | `workmain/services/results.py`, `workmain/services/calendar_service.py`, `tests/test_calendar_service.py` |
| 2 | `clients_service` returns `Summary` | `workmain/services/clients_service.py`, `tests/test_clients_service.py` |
| 3 | The map's deficiency entry is deleted | `docs/ARCHITECTURE.md` |
| 4 | Results artifact | `docs/dev/results/STATUS_RESULT_RESULTS.md` |

Every line a step adds or changes passes `python3 automation/style_check.py` (`docs/standards/3-code.md`).

### Step 1 — `Summary` and the calendar status

Done in this order, so that the fail-first run fails on the new assertion and not at import (`docs/standards/6-testing.md` §6.2 rule 9):

1. `workmain/services/results.py` adds, after `Page`:

   ```python
   @dataclass(frozen=True)
   class Summary(Generic[T]):
       totals: T
       filters: Tuple[Tuple[str, object], ...] = ()
   ```

   Its docstring says it is the result of a query that returns totals and no rows, and describes `filters` with the same meaning `Page`'s does. Its layout follows `docs/standards/3-code.md` §3.5 and passes D205 and D213: the summary on the line after the opening quotes, then a blank line. `Page`'s layout fails D213 and is not copied. The module docstring no longer limits the module to collection queries.
2. `tests/test_calendar_service.py` adds the line `from workmain.services.results import Summary`, on its own, where ruff's `I` rule orders it. `TestStatus::test_s5_status` adds `assert type(status) is Summary`. No other assertion in the file changes.
3. The implementer runs `test_s5_status` and sees it fail with an `AssertionError` on that line, because `get_status` still returns `CalendarStatus`. A failure of any other kind, such as an `ImportError` at collection, is not the fail-first run.
4. `workmain/services/calendar_service.py`: rename `StatusTotals` to `CalendarStatusTotals`, adding its class docstring (DR3), and delete `CalendarStatus` (DR2). Change `get_status`'s signature to `get_status(session: Session) -> Summary[CalendarStatusTotals]`, returning `Summary(CalendarStatusTotals(count, latest.date() if latest else None, LIVE_SYNC))`. Import `Summary` from `workmain.services.results`.
5. The implementer runs `test_s5_status` again and sees it pass. Results records both runs.

### Step 2 — the clients status

`Summary` exists from Step 1. Done in this order:

1. `tests/test_clients_service.py` adds the line `from workmain.services.results import Summary`, on its own, where ruff's `I` rule orders it. `TestActive::test_s17_sets_the_active_client_by_name` and `TestStatus::test_s20_reports_the_active_client` each add `assert type(status) is Summary`. `test_s17_sets_the_active_client_by_name` also adds `assert status.filters == ()`. That assertion passes before the change and after it, and it pins `set_active`'s `filters` for AC3.2.
2. The implementer runs both tests and sees each fail with an `AssertionError` on that line, because the service still returns `ClientStatus`.
3. `workmain/services/clients_service.py`: rename `StatusTotals` to `ClientStatusTotals` (DR3) and delete `ClientStatus` (DR2). The signatures become `get_status(session: Session) -> Summary[ClientStatusTotals]` and `set_active(session: Session, name: str) -> Summary[ClientStatusTotals]`. `get_status` returns `Summary(totals)`, and `set_active` still returns `get_status(session)`. Import `Summary` from `workmain.services.results`. In the same change, each `clients_service.StatusTotals` in `tests/test_clients_service.py` becomes `clients_service.ClientStatusTotals`, with the same arguments. No assertion changes beyond those item 1 of this step adds.
4. The implementer runs both tests again and sees them pass. Results records both runs.

### Step 3 — the map

`docs/ARCHITECTURE.md` section 3: delete this line and the blank line after it:

> **Per-service status types — #259.** Covers `workmain/services/calendar_service.py` and `workmain/services/clients_service.py`. `workmain/services/calendar_service.py` and `workmain/services/clients_service.py` each declare their own "filters plus totals" wrapper and a type named `StatusTotals`.

### Step 4 — results artifact

`docs/dev/results/STATUS_RESULT_RESULTS.md`, as `.claude/skills/session-start/SKILL.md` § Role 3 states. Every row whose check names Ray is recorded `Not met`, `Awaiting Ray` (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None. The spec runs no migration, deletes no GitHub object, merges nothing and changes no service's run state.

## 5. Acceptance criteria

The issue's third criterion is restated as AC3.1–AC3.3 (Decision Log, 20261114, Spanner).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No class under `workmain/` is named `StatusTotals`, `CalendarStatus` or `ClientStatus`, and no alias or re-export of those names remains anywhere in the code or tests (DR2) | `git grep -nwE 'StatusTotals\|CalendarStatus\|ClientStatus' -- workmain tests automation scripts` returning nothing |
| AC1.2 | `workmain/services/results.py` holds the generic, and the three status functions return it: `calendar_service.get_status`, `clients_service.get_status` and `clients_service.set_active` | `git grep -n '^class ' workmain/services/results.py` showing `Page` and `Summary`; `pytest tests/test_calendar_service.py::TestStatus::test_s5_status tests/test_clients_service.py::TestActive::test_s17_sets_the_active_client_by_name tests/test_clients_service.py::TestStatus::test_s20_reports_the_active_client` passing, each asserting `type(status) is Summary`, with results recording each test's earlier run failing with an `AssertionError` on that assertion before its service changed |
| AC2.1 | The map no longer lists per-service status types as a known deficiency | `grep -n 'Per-service status types' docs/ARCHITECTURE.md` returning nothing |
| AC2.2 | No class name is defined twice under `workmain/`, and the check reports nothing for the deleted entry and nothing new | The AC2.2 command below printing `[]` and exiting 0; and `python3 automation/architecture_check.py` printing `New findings: 0`, with no `#259` line under `Known deficiencies` |
| AC3.1 | `calendar status`, `clients status` and `clients set active` render through views and a renderer the branch leaves as they were | `git diff --stat origin/main...HEAD -- workmain/cli/` returning nothing |
| AC3.2 | The three status functions return the same `filters` and the same value in every totals field as before, on every case the service tests cover | `pytest tests/test_calendar_service.py::TestStatus tests/test_clients_service.py` passing, and the AC3.2 command below printing nothing. The command shows that, apart from `StatusTotals` becoming `ClientStatusTotals`, the branch removes or changes no line of either test file and adds only the import, the type assertions and `set_active`'s `filters` assertion |
| AC3.3 | Each of the three commands still hands its service's result to `renderer.report` with its `STATUS` view | `pytest tests/test_calendar.py::TestCalendarCommands::test_c2_status tests/test_clients_commands.py` passing, and `git diff --stat origin/main...HEAD -- tests/test_calendar.py tests/test_clients_commands.py` returning nothing |
| AC4.1 | The full suite passes | `pytest` reporting `0 failed` |

The AC2.2 command runs the duplicate-class check on its own. `main()` files each finding under the first map section 3 entry whose Covers pattern matches its path, so `New findings: 0` alone cannot show that no duplicate exists:

```bash
python3 -c "import sys; sys.path.insert(0, 'automation'); import architecture_check as a; r = a.check_duplicates(a.modules()); print(r); sys.exit(bool(r))"
```

The AC3.2 command diffs each service test file against the point the branch left `origin/main`. It applies the one rename first, and prints any line except the three Steps 1 and 2 may add:

```bash
B=$(git merge-base origin/main HEAD)
for f in tests/test_calendar_service.py tests/test_clients_service.py; do
  diff <(git show "$B:$f" | sed 's/StatusTotals/ClientStatusTotals/') "$f" \
    | grep -E '^[<>]' \
    | grep -vxE '> +(from workmain\.services\.results import Summary|assert type\(status\) is Summary|assert status\.filters == \(\))'
done
```

## 6. Test plan

- **Baseline before this work:** `1708 passed, 0 failed, 0 skipped` (`CHANGELOG.md` 1.58.3).
- **Expected after:** `1708 passed, 0 failed, 0 skipped`. The type assertions are added to existing tests, so the count doesn't change.
- `tests/test_calendar_service.py` `TestStatus::test_s5_status`, and `tests/test_clients_service.py` `TestActive::test_s17_sets_the_active_client_by_name` and `TestStatus::test_s20_reports_the_active_client`: each asserts that the result is a `Summary`. These are the fail-first tests: each is seen failing with an `AssertionError` before its service changes (Steps 1 and 2). `test_s17_sets_the_active_client_by_name` also asserts `set_active`'s `filters`.
- No renderer test is added. `tests/test_output.py` `TestReport::test_o1_totals_when_empty_with_no_sections` already covers a result with no sections and `totals_when_empty`, the shape both `STATUS` views render.

## 7. Risks and rollback

- **A caller outside the enumerated set constructs or type-checks the old names.** That caller fails at import or at test time, and AC1.1 and AC4.1 catch it. §2's search covers `workmain/`, `tests/`, `automation/` and `scripts/`.
- **#279 and #282 change these functions' parameters.** Whichever merges second rebases onto the other. The edits touch adjacent lines but not the same decision.
- **Rollback:** each step is one commit and reverts on its own. Step 2 reverts cleanly without Step 1. Reverting Step 1 while keeping Step 2 breaks `clients_service`'s import of `Summary`, so revert them in reverse order.

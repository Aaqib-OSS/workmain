# Shared Status Result — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20261114
**Spec:** `../specs/STATUS_RESULT_SPEC.md`
**Released as:** v1.58.4 (tag `v1.58.4`)

---

## 1. Summary

Complete. `workmain/services/results.py` now holds `Summary[T]` beside `Page`. `calendar_service.get_status` returns `Summary[CalendarStatusTotals]`, and `clients_service.get_status` and `clients_service.set_active` return `Summary[ClientStatusTotals]`. `CalendarStatus`, `ClientStatus` and both `StatusTotals` are deleted, and so is the map's "Per-service status types — #259" entry. Nothing under `workmain/cli/` changed.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `Summary`; `CalendarStatusTotals` with a class docstring; `CalendarStatus` deleted; calendar `get_status` returns `Summary` (`b237783`) | `workmain/services/results.py`, `workmain/services/calendar_service.py`, `tests/test_calendar_service.py` | +0 (one assertion added to `test_s5_status`) |
| 2 | `ClientStatusTotals`; `ClientStatus` deleted; clients `get_status` and `set_active` return `Summary` (`b43ab68`) | `workmain/services/clients_service.py`, `tests/test_clients_service.py` | +0 (assertions added to `test_s17_sets_the_active_client_by_name` and `test_s20_reports_the_active_client`) |
| 3 | Map section 3 entry deleted (`50043ee`) | `docs/ARCHITECTURE.md` | +0 |
| 4 | This artifact | `docs/dev/results/STATUS_RESULT_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `git grep -nwE 'StatusTotals\|CalendarStatus\|ClientStatus' -- workmain tests automation scripts` printed nothing, exit 1 |
| AC1.2 | Met | `git grep -n '^class ' workmain/services/results.py` → `:12 class Page(Generic[T])`, `:28 class Summary(Generic[T])`; the three named tests: `3 passed`; the earlier failing runs are in §5 |
| AC2.1 | Met | `grep -n 'Per-service status types' docs/ARCHITECTURE.md` printed nothing, exit 1 |
| AC2.2 | Met | The AC2.2 command printed `[]`, exit 0; `python3 automation/architecture_check.py` printed `New findings: 0`, with no `#259` line under `Known deficiencies` |
| AC3.1 | Met | `git diff --stat origin/main...HEAD -- workmain/cli/` printed nothing |
| AC3.2 | Met | `pytest tests/test_calendar_service.py::TestStatus tests/test_clients_service.py` → `26 passed`; the AC3.2 command printed nothing |
| AC3.3 | Met | `pytest tests/test_calendar.py::TestCalendarCommands::test_c2_status tests/test_clients_commands.py` → `17 passed`; `git diff --stat origin/main...HEAD -- tests/test_calendar.py tests/test_clients_commands.py` printed nothing |
| AC4.1 | Met | `pytest` → `1708 passed, 0 failed, 0 skipped` |

## 4. Deviations and decisions

None.

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | The module docstring reads "Result types shared by service-layer queries." | Naming both kinds ("collection and totals queries") | Step 1.1 requires only that the docstring stop limiting the module to collection queries. Dropping the one word does that without listing the module's contents, which `docs/standards/3-code.md` §3.1 rules out. |
| 2 | 1 | `Summary`'s docstring states its summary, then an `Attributes:` block for `totals` and `filters`, with the `filters` text copied from `Page`'s | Summary line only | `Page` documents its fields in `Attributes:`, and §3.5 names that block for classes. Copying the `filters` text keeps "the same meaning `Page`'s does" exact. |
| 3 | 1 | `CalendarStatusTotals`'s docstring has a summary and an `Attributes:` block for each field | A one-line docstring, as `ClientStatusTotals` has | D101 needs only a docstring, but the three fields are not obvious from their names (`live_sync` is a state string). |
| 4 | 1 | `get_status` builds its result on one line: `return Summary(CalendarStatusTotals(...))` | Keeping the old two-line wrap | The step gives the expression whole, and the line passes `automation/style_check.py`. |
| 5 | 2 | `test_s17_sets_the_active_client_by_name` puts the type and `filters` assertions before its `totals` assertion; `test_s20_reports_the_active_client` puts the type assertion first | Placing them after `totals` | Asserting the type first means a wrong type fails on that line, which is the fail-first line Step 2.2 requires. |

## 5. Verification

- **Test suite:** 1708 passed, 0 failed, 0 skipped (baseline: 1708 passed, 0 failed, 0 skipped).
- **Defect shown before the fix** (`docs/standards/6-testing.md` §6.2 rule 9):
  - `tests/test_calendar_service.py::TestStatus::test_s5_status`. Before Step 1.4: failed, `AssertionError: assert <class 'workmain.services.calendar_service.CalendarStatus'> is Summary` at `tests/test_calendar_service.py:124`. After: passed.
  - `tests/test_clients_service.py::TestActive::test_s17_sets_the_active_client_by_name`. Before Step 2.3: failed, `AssertionError: assert <class 'workmain.services.clients_service.ClientStatus'> is Summary` at `tests/test_clients_service.py:235`. After: passed.
  - `tests/test_clients_service.py::TestStatus::test_s20_reports_the_active_client`. Before Step 2.3: failed, `AssertionError: assert <class 'workmain.services.clients_service.ClientStatus'> is Summary` at `tests/test_clients_service.py:274`. After: passed.
- **Live verification:** none. The spec states no live check.
- **Daemon restart:** done by `/closeout`.

## 6. Follow-ups

None.

| Item | Description | Why deferred |
| --- | --- | --- |

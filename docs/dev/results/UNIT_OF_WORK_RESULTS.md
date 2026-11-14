# Unit of Work — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261114
**Spec:** `../specs/UNIT_OF_WORK_SPEC.md`
**Released as:** set by `/closeout`

---

## 1. Summary

Complete. All six steps shipped as the spec writes them, with no departure:

- `session_scope()` now records whether it is open on the calling thread, and `scope_open()` reads it.
- `workmain/services/unit_of_work.py` adds `UnitOfWork`. It holds all twelve repositories and its transaction, guards against re-entry, and is refused inside an open scope unless it records.
- `tests/mocks/fake_unit_of_work.py` adds `FakeUnitOfWork` and `FakeSystemStateRepository`. Parity and behaviour tests run each fake method against the real repository.
- `automation/session_param_check.py` lists session parameters.
- The map and `docs/standards/4-database.md` §4.1, §4.3 and `docs/standards/6-testing.md` §6.1, §6.2 state the unit-of-work form.

No caller in `workmain/` uses the unit of work yet. Three criteria are readings by Ray (AC1.2, AC10.1, AC10.2) and are left to him.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 (`4621dfc`) | Scope state and `scope_open()` (DR1, DR2); §6.1 exception for `tests/test_unit_of_work.py` (DR13); `TestScopeState` | `workmain/database/connection.py`, `docs/standards/6-testing.md`, `tests/test_unit_of_work.py` | +7 |
| 2 (`7971146`) | `UnitOfWork` (DR3–DR6); map section 1 Surfaces rule and section 2 `unit_of_work.py` and `connection.py` lines (DR12); `TestUnitOfWork`, `TestReentryGuard`, `TestOpenScopeCheck`, `TestRecordUnitOfWork` | `workmain/services/unit_of_work.py`, `docs/ARCHITECTURE.md`, `tests/test_unit_of_work.py` | +19 |
| 3 (`2f6ac81`) | `FakeUnitOfWork`, `FakeSystemStateRepository` (DR7–DR10); `tests/mocks/__init__.py` docstring; `TestFakeUnitOfWork`, `TestFakeOpenScopeCheck`, `TestFakeParity`, `TestSystemStateContract` | `tests/mocks/fake_unit_of_work.py`, `tests/mocks/__init__.py`, `tests/test_fake_unit_of_work.py` | +46 |
| 4 (`e4f5ec7`) | `automation/session_param_check.py` (DR14) and its tests | `automation/session_param_check.py`, `automation/session_param_check_test.py` | +21 (automation suite) |
| 5 (`4737662`) | §4.1's unit-of-work form and its six points, "unit of work" held to the object in §4.1 and §4.3 (DR11); §6.2 Service and Repository fake bullets (DR13) | `docs/standards/4-database.md`, `docs/standards/6-testing.md` | 0 |
| 6 | This artifact | `docs/dev/results/UNIT_OF_WORK_RESULTS.md` | 0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `pytest tests/test_unit_of_work.py::TestUnitOfWork`: 7 passed, 0 failed, 0 skipped. Covers repositories built on the one session opened while entered, absent after exit and after a commit that raises, and no `session`, `commit`, `rollback` or `begin_nested` attribute |
| AC1.2 | Not met | Awaiting Ray |
| AC2.1 | Met | `pytest tests/test_fake_unit_of_work.py::TestFakeUnitOfWork`: 8 passed, 0 failed, 0 skipped. No test in the class (lines 28–101) takes `db_session` |
| AC2.2 | Met | `TestFakeUnitOfWork::test_exception_restores_store_and_sets_rolled_back`: seeds a store, deep-copies it as the expected state, writes and raises, then asserts `uow.store is store`, `store == expected`, `rolled_back` true and `committed` false |
| AC2.3 | Met | `pytest tests/test_fake_unit_of_work.py::TestFakeParity`: 2 passed, 0 failed, 0 skipped |
| AC2.4 | Met | `pytest tests/test_fake_unit_of_work.py::TestSystemStateContract`: 26 passed, 0 failed, 0 skipped (13 tests × real, fake) |
| AC3.1 | Met | `TestUnitOfWork::test_commits_on_normal_exit`: `scope_open()` is false after exit, and `db_session` reads the row |
| AC3.2 | Met | `TestUnitOfWork::test_rolls_back_on_exception_and_propagates`: the `ValueError` is seen outside, and `db_session` finds no row |
| AC3.3 | Met | `TestUnitOfWork::test_discards_writes_on_keyboard_interrupt`: `KeyboardInterrupt` caught outside, no row through `db_session` |
| AC4.1 | Met | `python3 automation/architecture_check.py` prints `New findings: 0` |
| AC5.1 | Met | `pytest`: 1707 passed, 0 failed, 0 skipped |
| AC6.1 | Met | `pytest tests/test_unit_of_work.py::TestReentryGuard`: 6 passed, 0 failed, 0 skipped. This covers the guard's message on an entered and an exited instance, and a refused instance entering once the scope closes. A `get_session` counter, built with `pytest.MonkeyPatch.context()`, shows 0 sessions for each of the three refusals. Fake: `TestFakeUnitOfWork::test_entered_again_while_open_raises_guard_message` and `::test_entered_after_exit_raises_guard_message` pass, as does `TestFakeOpenScopeCheck::test_refused_fake_leaves_store_and_enters_after_outer_exits` |
| AC7.1 | Met | `pytest tests/test_unit_of_work.py::TestRecordUnitOfWork`: 2 passed, 0 failed, 0 skipped. The record unit of work reads `RECORD_LOCK_TIMEOUT`. The default one reads the same value as `db_session` and not `RECORD_LOCK_TIMEOUT` |
| AC8.1 | Met | `pytest tests/test_unit_of_work.py::TestOpenScopeCheck`: 4 passed, 0 failed, 0 skipped |
| AC8.2 | Met | `pytest tests/test_unit_of_work.py::TestScopeState`: 7 passed, 0 failed, 0 skipped |
| AC8.3 | Met | `pytest tests/test_fake_unit_of_work.py::TestFakeOpenScopeCheck`: 10 passed, 0 failed, 0 skipped. No test in the class takes `db_session`. `test_record_inside_open_non_record_enters_and_restores_flag` shows that the record fake resets by token |
| AC9.1 | Met | `pytest automation/session_param_check_test.py`: 21 passed, 0 failed, 0 skipped |
| AC9.2 | Met | `python3 automation/session_param_check.py workmain/services/*.py --exclude workmain/services/unit_of_work.py` exits 1. As a set, its lines equal the criterion's independent walk: 41 lines, `diff` of the sorted outputs is empty. `--package workmain/workflows` prints `workmain/services/schedule_service.py:36 __init__` |
| AC10.1 | Not met | Awaiting Ray |
| AC10.2 | Not met | Awaiting Ray |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
| — | None | — | — | — |

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | `session_scope()` resets the context variable in an outer `try`/`finally` around its existing `try`/`except`/`finally` | The reset in the same `finally` as `session.close()` | A `close()` that raises would skip a reset placed after it. The outer `finally` always runs after the close, as DR1 orders it |
| 2 | 1 | The context variable is the private `_scope_open`, and `scope_open()` sits after `get_db()` | A public name | DR2: nothing but `scope_open()` reads it |
| 3 | 1 | The §6.1 sentence is appended to the `tests/test_database_isolation.py` bullet | A separate bullet | DR13: the bullet "gains" it |
| 4 | 1 | The thread test only calls `scope_open()` on the other thread | — | `docs/standards/6-testing.md` §6.1 keeps database work on the test's thread |
| 5 | 2 | `UnitOfWork` drives its scope's context manager by hand (`__enter__` / `__exit__`) and keeps it in a private `_scope` | `contextlib.ExitStack` | There is only one scope, and an `ExitStack` would add a layer without adding behaviour |
| 6 | 2 | The refusal messages are module-private constants `_REENTRY_MESSAGE` and `_OPEN_SCOPE_MESSAGE`. The tests and the fake import them | Public constants or class attributes | A public name is contract the spec does not name, and DR7 needs the fake to raise the same message |
| 7 | 2 | `_entered` is set only after the scope has opened | Setting it before opening | DR4: a refused `__enter__` changes nothing |
| 8 | 2 | Repositories are removed with `self.__dict__.pop(name, None)` in a `finally` around the scope's exit | `delattr` | `pop` tolerates a name that was never set |
| 9 | 2 | AC1.1's "built on the unit of work's session" is checked by wrapping `DatabaseConnection.get_session` and comparing each repository's `.session` with the one session opened | — | DR3 exposes no session to compare against |
| 10 | 2 | The commit-that-raises test patches `commit` on the unit of work's session instance with `pytest.MonkeyPatch.context()` | Seeding a constraint violation | The failure is direct and stays at the commit |
| 11 | 2 | The default-scope `lock_timeout` test also compares with `SHOW lock_timeout` read on `db_session` first | Only `!= RECORD_LOCK_TIMEOUT` | AC7.1 says it "returns the server default" |
| 12 | 2 | Each refusal's no-session check is its own test: re-entry while open, re-entry after exit, inside an open scope | One test for all three | `docs/standards/6-testing.md` §6.2 rule 2 |
| 13 | 3 | `FakeSystemStateRepository` reuses the real `get_bool`, `set_bool`, `get_int` and `set_int` by class-attribute assignment, and writes `get`, `set` and `delete` over the store | Writing all seven | DR8 leaves this to the implementer. Reuse keeps the derived parsing from drifting, and DR10 still runs each method against both |
| 14 | 3 | The fake module uses `from __future__ import annotations`, as the real repository does | Evaluated annotations | DR9 compares `inspect.signature`, which compares annotations, and the real ones are strings |
| 15 | 3 | `store['system_state']` is created on first write, and a read of an absent table answers as empty | `setdefault` in `__init__` | A fake that only reads leaves the store as it was |
| 16 | 3 | "The variable is clear" is checked by behaviour: a non-record fake enters after the outer exits, parametrized over the outer's `record` | Reading the private context variable | AC8.3 states the check as an entry |
| 17 | 3 | `TestSystemStateContract` is parametrized at class level over `real` and `fake`. Each test takes `db_session` and builds its repository through a private static helper | A fixture | `docs/standards/6-testing.md` §6.2 rule 5, and DR10 names the parametrization |
| 18 | 3 | Added `TestFakeUnitOfWork::test_repositories_absent_after_exit` | — | DR7: repositories are removed on exit |
| 19 | 4 | Module paths and `--package` are alternatives: both, or neither, is a usage error (exit 2) | Allowing both together | DR14 states them as alternatives ("…; or `--package <dir>`") |
| 20 | 4 | `*args` and `**kwargs` count as parameters, as well as positional-only, positional and keyword-only ones | Only the three lists AC9.2's walk reads | DR14 says "a parameter". No service has a session in either, so AC9.2's set is unchanged, which the run shows |
| 21 | 4 | A lambda is not reported | Reporting it as `<lambda>` | DR14 says "function or method", and each output line needs a name |
| 22 | 4 | A `workmain.services` import that resolves to no file is skipped | Exit 2 | It names no module to check |
| 23 | 4 | `main()` turns argparse's usage exit into a return of 2. The helpers are private, and `main()` is the only public function, as in the other `automation/` scripts | Letting `SystemExit` escape | The tests call `main()` in-process |
| 24 | 4 | The tests capture output with `contextlib.redirect_stdout` and change directory with `pytest.MonkeyPatch.context()`, in a private helper | The `capsys` and `monkeypatch` fixtures | `docs/standards/6-testing.md` §6.2 rule 5; DR14 |
| 25 | 5 | §4.1 layout: point 1 ("two forms") comes before the two existing session-taking bullets, and points 2–6 directly after them. Point 1 names each form's bullets by position | All six points together before the existing bullets | DR11 point 1 keeps the existing bullets as the session-taking form's, and the order 1–6 is kept |
| 26 | 5 | §4.1's unit-of-work example is a second code block after the existing one, and it uses `uow.system_state.set_bool` | One block holding both forms | Each form reads on its own, and the method is real |
| 27 | 5 | The wait-rule bullet states only DR11 point 4 and calls it the unit-of-work form's wait rule | A drafted sentence on placing the outside call around writes, removed before the commit | That sentence was wrong (a write made earlier in the unit of work is held until exit) and is not in DR11 |

## 5. Verification

- **Test suite:** 1707 passed, 0 failed, 0 skipped (baseline: 1635 passed, 0 failed, 0 skipped). `pytest automation/`: 134 passed, 0 failed, 0 skipped.
- **Defect shown before the fix:** n/a. Issue #258 is a gap, not a defect fix.
- **Live verification:** none. No caller in `workmain/` builds a unit of work (DR6).
- **Daemon restart:** close-out's (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| — | None created by this work | — |

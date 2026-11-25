"""
Tests for the scope state and the unit of work.

The scope state records whether a session_scope() is open on the calling
thread. These tests open bare scopes through get_db(), because the state
exists for callers that still hold one.
"""

import re
import threading
from contextlib import contextmanager
from typing import Iterator, List

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from workmain.database.connection import (
    RECORD_LOCK_TIMEOUT,
    DatabaseConnection,
    get_db,
    scope_open,
)
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services.unit_of_work import (
    _OPEN_SCOPE_MESSAGE,
    _REENTRY_MESSAGE,
    UnitOfWork,
)

_KEY = 'uow-test-key'
_REENTRY = re.escape(_REENTRY_MESSAGE)
_OPEN_SCOPE = re.escape(_OPEN_SCOPE_MESSAGE)


@contextmanager
def _sessions_opened() -> Iterator[List[Session]]:
    """Record every session DatabaseConnection.get_session returns inside the block."""
    opened: List[Session] = []
    original = DatabaseConnection.get_session

    def counting(self: DatabaseConnection) -> Session:
        session = original(self)
        opened.append(session)
        return session

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(DatabaseConnection, 'get_session', counting)
        yield opened


def _recording(repository_class: type, built: list[Session]) -> type:
    """A subclass of repository_class that records the session it is constructed with."""

    class Recording(repository_class):
        def __init__(self, session: Session) -> None:
            built.append(session)
            super().__init__(session)

    return Recording


class TestScopeState:
    """scope_open() is true exactly while a session_scope() is open on its thread."""

    def test_true_inside_session_scope(self) -> None:
        with get_db().session_scope():
            assert scope_open() is True

    def test_true_inside_record_scope(self) -> None:
        with get_db().record_scope():
            assert scope_open() is True

    def test_false_before_and_after(self) -> None:
        assert scope_open() is False
        with get_db().session_scope():
            pass
        assert scope_open() is False

    def test_nested_scope_restores_true(self) -> None:
        with get_db().session_scope():
            with get_db().session_scope():
                pass
            assert scope_open() is True
        assert scope_open() is False

    def test_false_after_exception(self) -> None:
        with pytest.raises(ValueError):
            with get_db().session_scope():
                raise ValueError("leave the scope")
        assert scope_open() is False

    def test_false_after_keyboard_interrupt(self) -> None:
        with pytest.raises(KeyboardInterrupt):
            with get_db().session_scope():
                raise KeyboardInterrupt
        assert scope_open() is False

    def test_false_on_another_thread(self) -> None:
        seen = []
        with get_db().session_scope():
            thread = threading.Thread(target=lambda: seen.append(scope_open()))
            thread.start()
            thread.join()
            assert scope_open() is True
        assert seen == [False]


class TestUnitOfWork:
    """The unit of work holds every repository and its transaction, and nothing else."""

    def test_repositories_built_on_its_session_while_entered(self) -> None:
        originals = dict(UnitOfWork.REPOSITORIES)
        built: dict[str, list[Session]] = {name: [] for name in originals}
        with pytest.MonkeyPatch.context() as mp:
            for name, repository_class in originals.items():
                mp.setitem(UnitOfWork.REPOSITORIES, name, _recording(repository_class, built[name]))
            with _sessions_opened() as opened:
                with UnitOfWork() as uow:
                    for name, repository_class in originals.items():
                        assert isinstance(getattr(uow, name), repository_class)
                        assert len(built[name]) == 1
                        assert built[name][0] is opened[0]
        assert len(opened) == 1

    @pytest.mark.parametrize(
        'repository_class',
        list(UnitOfWork.REPOSITORIES.values()),
        ids=list(UnitOfWork.REPOSITORIES),
    )
    def test_repository_has_no_session_attribute(self, repository_class: type, db_session: Session) -> None:
        assert not hasattr(repository_class(db_session), 'session')

    def test_repositories_absent_after_exit(self) -> None:
        uow = UnitOfWork()
        with uow:
            pass
        for name in UnitOfWork.REPOSITORIES:
            assert not hasattr(uow, name)

    def test_repository_that_fails_to_build_closes_the_scope(self) -> None:
        class FailingRepository:
            def __init__(self, session: Session) -> None:
                raise RuntimeError("repository failed to build")

        uow = UnitOfWork()
        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(UnitOfWork.REPOSITORIES, 'notes', FailingRepository)
            with pytest.raises(RuntimeError, match="repository failed to build"):
                with uow:
                    pass
        assert scope_open() is False
        for name in UnitOfWork.REPOSITORIES:
            assert not hasattr(uow, name)
        with UnitOfWork() as fresh:
            assert isinstance(fresh.system_state, SystemStateRepository)

    def test_repositories_absent_after_commit_raises(self) -> None:
        def failing_commit() -> None:
            raise RuntimeError("commit failed")

        uow = UnitOfWork()
        with pytest.MonkeyPatch.context() as mp, _sessions_opened() as opened:
            with pytest.raises(RuntimeError, match="commit failed"):
                with uow:
                    mp.setattr(opened[0], 'commit', failing_commit)
        for name in UnitOfWork.REPOSITORIES:
            assert not hasattr(uow, name)

    def test_exposes_no_session_or_transaction_control(self) -> None:
        uow = UnitOfWork()
        hidden = ('session', 'commit', 'rollback', 'begin_nested')
        assert not any(hasattr(uow, name) for name in hidden)
        with uow:
            assert not any(hasattr(uow, name) for name in hidden)

    def test_commits_on_normal_exit(self, db_session: Session) -> None:
        with UnitOfWork() as uow:
            uow.system_state.set(_KEY, 'committed')
        assert scope_open() is False
        assert SystemStateRepository(db_session).get(_KEY) == 'committed'

    def test_rolls_back_on_exception_and_propagates(self, db_session: Session) -> None:
        with pytest.raises(ValueError, match="leave the unit of work"):
            with UnitOfWork() as uow:
                uow.system_state.set(_KEY, 'rolled back')
                raise ValueError("leave the unit of work")
        assert SystemStateRepository(db_session).get(_KEY) is None

    def test_discards_writes_on_keyboard_interrupt(self, db_session: Session) -> None:
        with pytest.raises(KeyboardInterrupt):
            with UnitOfWork() as uow:
                uow.system_state.set(_KEY, 'interrupted')
                raise KeyboardInterrupt
        assert SystemStateRepository(db_session).get(_KEY) is None


class TestReentryGuard:
    """An instance is entered once, and a refused entry changes nothing."""

    def test_entered_twice_raises_guard_message(self) -> None:
        uow = UnitOfWork()
        with uow:
            with pytest.raises(RuntimeError, match=_REENTRY):
                with uow:
                    pass
            uow.system_state.set(_KEY, 'still open')

    def test_entered_after_exit_raises_guard_message(self) -> None:
        uow = UnitOfWork()
        with uow:
            pass
        with pytest.raises(RuntimeError, match=_REENTRY):
            with uow:
                pass

    def test_refused_by_open_scope_check_enters_after_scope_closes(self) -> None:
        uow = UnitOfWork()
        with get_db().session_scope():
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with uow:
                    pass
        with uow:
            assert isinstance(uow.system_state, SystemStateRepository)

    def test_refused_reentry_while_open_opens_no_session(self) -> None:
        uow = UnitOfWork()
        with uow:
            with _sessions_opened() as opened:
                with pytest.raises(RuntimeError):
                    with uow:
                        pass
        assert opened == []

    def test_refused_reentry_after_exit_opens_no_session(self) -> None:
        uow = UnitOfWork()
        with uow:
            pass
        with _sessions_opened() as opened:
            with pytest.raises(RuntimeError):
                with uow:
                    pass
        assert opened == []

    def test_refused_in_open_scope_opens_no_session(self) -> None:
        with get_db().session_scope():
            with _sessions_opened() as opened:
                with pytest.raises(RuntimeError):
                    with UnitOfWork():
                        pass
        assert opened == []


class TestOpenScopeCheck:
    """A unit of work on session_scope() is refused inside an open session_scope()."""

    def test_inside_bare_session_scope_raises(self) -> None:
        with get_db().session_scope():
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with UnitOfWork():
                    pass

    def test_inside_entered_unit_of_work_raises(self) -> None:
        with UnitOfWork():
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with UnitOfWork():
                    pass

    def test_after_scope_closes_enters(self) -> None:
        with get_db().session_scope():
            pass
        with UnitOfWork() as uow:
            assert isinstance(uow.system_state, SystemStateRepository)

    def test_record_inside_open_scope_enters(self) -> None:
        with get_db().session_scope():
            with UnitOfWork(record=True) as uow:
                assert isinstance(uow.system_state, SystemStateRepository)


class TestRecordUnitOfWork:
    """A record unit of work runs on record_scope(), the default one on session_scope()."""

    def test_record_runs_on_record_scope(self) -> None:
        with _sessions_opened() as opened:
            with UnitOfWork(record=True):
                value = opened[0].execute(text('SHOW lock_timeout')).scalar()
        assert len(opened) == 1
        assert value == RECORD_LOCK_TIMEOUT

    def test_default_runs_on_session_scope(self, db_session: Session) -> None:
        server_default = db_session.execute(text('SHOW lock_timeout')).scalar()
        with _sessions_opened() as opened:
            with UnitOfWork():
                value = opened[0].execute(text('SHOW lock_timeout')).scalar()
        assert len(opened) == 1
        assert value == server_default
        assert value != RECORD_LOCK_TIMEOUT

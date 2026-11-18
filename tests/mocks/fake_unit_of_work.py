"""
An in-memory stand-in for workmain/services/unit_of_work.py's UnitOfWork.

A FakeUnitOfWork holds its rows in a store, a dict keyed by table name that
every fake repository it builds shares, so a test that passes one store to
several fake units of work sees each one's committed writes in the next. It
commits by keeping the store as it is, and rolls back by restoring the store,
in place, to a deep copy taken on entry. It refuses re-entry, and a non-record
fake inside another open fake, with the real unit of work's messages, so a
service test refuses the nesting production refuses.

Each fake repository takes the store and keeps its rows under its table's
name. FakeUnitOfWork.REPOSITORIES maps the attribute names
UnitOfWork.REPOSITORIES uses to the fake classes, and
tests/test_fake_unit_of_work.py checks every fake method's signature against
the real repository's and runs each fake's contract tests against both the
fake and the real repository on db_session.
"""

from __future__ import annotations

import contextvars
import copy
from types import TracebackType
from typing import Dict, Optional, Type

from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services.unit_of_work import _OPEN_SCOPE_MESSAGE, _REENTRY_MESSAGE

# Whether a FakeUnitOfWork is open on the calling thread: the fake's
# counterpart of the scope state session_scope() sets.
_fake_open: contextvars.ContextVar[bool] = contextvars.ContextVar(
    'fake_unit_of_work_open', default=False
)


class FakeSystemStateRepository:
    """The system_state key-value store, held in store['system_state']."""

    _TABLE = 'system_state'

    def __init__(self, store: dict) -> None:
        """
        Build the repository over the shared store.

        Args:
            store: The fake unit of work's store; the table's rows are
                store['system_state'], a dict of key to value created on
                first write
        """
        self._store = store

    def get(self, key: str) -> Optional[str]:
        """Return the string value for key, or None if absent."""
        return self._store.get(self._TABLE, {}).get(key)

    def set(self, key: str, value: str) -> None:
        """Upsert key with value."""
        self._store.setdefault(self._TABLE, {})[key] = value

    def delete(self, key: str) -> bool:
        """Delete key. Returns True if deleted, False if not found."""
        rows = self._store.get(self._TABLE, {})
        if key not in rows:
            return False
        del rows[key]
        return True

    get_bool = SystemStateRepository.get_bool
    set_bool = SystemStateRepository.set_bool
    get_int = SystemStateRepository.get_int
    set_int = SystemStateRepository.set_int


class FakeUnitOfWork:
    """
    A unit of work over an in-memory store.

    Attributes:
        REPOSITORIES: Attribute name to fake repository class, under the same
            names as UnitOfWork.REPOSITORIES
        store: The in-memory database, shared with every holder
        committed: True once the fake has exited normally
        rolled_back: True once an Exception has left the fake
    """

    REPOSITORIES: Dict[str, type] = {
        'system_state': FakeSystemStateRepository,
    }

    def __init__(self, record: bool = False, store: Optional[dict] = None) -> None:
        """
        Build a fake unit of work that has not been entered.

        Args:
            record: True to stand in for UnitOfWork(record=True), which may be
                entered inside an open unit of work
            store: The in-memory database to share; a new empty one if None
        """
        self._record = record
        self.store = {} if store is None else store
        self.committed = False
        self.rolled_back = False
        self._entered = False
        self._snapshot: Optional[dict] = None
        self._token: Optional[contextvars.Token] = None

    def __enter__(self) -> FakeUnitOfWork:
        """
        Snapshot the store, mark a fake open, and build the fake repositories.

        Returns:
            This fake unit of work

        Raises:
            RuntimeError: This instance has been entered before, or it does not
                record and another fake is open on this thread. Nothing is
                changed.
        """
        if self._entered:
            raise RuntimeError(_REENTRY_MESSAGE)
        if not self._record and _fake_open.get():
            raise RuntimeError(_OPEN_SCOPE_MESSAGE)
        self._snapshot = copy.deepcopy(self.store)
        self._token = _fake_open.set(True)
        self._entered = True
        for name, repository_class in self.REPOSITORIES.items():
            setattr(self, name, repository_class(self.store))
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        """
        Commit on a normal exit, otherwise restore the store; never suppress.

        Args:
            exc_type: The type of the exception leaving the block, or None
            exc: The exception leaving the block, or None
            traceback: Its traceback, or None

        Returns:
            False: an exception leaving the block always propagates
        """
        try:
            if exc_type is None:
                self.committed = True
            else:
                self.store.clear()
                self.store.update(self._snapshot)
                if issubclass(exc_type, Exception):
                    self.rolled_back = True
        finally:
            for name in self.REPOSITORIES:
                self.__dict__.pop(name, None)
            self._snapshot = None
            _fake_open.reset(self._token)
            self._token = None
        return False

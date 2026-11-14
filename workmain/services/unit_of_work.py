"""
The transaction a use case enters, and the repositories it holds.

A caller builds a UnitOfWork and passes it to a use case, which enters it
with `with uow:`. Entering opens a session_scope(), or a record_scope() for
a record of an outside action, and builds every repository on that session;
leaving it commits after a normal exit, rolls back on an Exception, and
discards uncommitted writes on any other BaseException. The session itself
is never exposed, and there is no public commit.

An instance is entered once. One that does not record is refused inside an
open session_scope(), which includes another entered unit of work.
"""

from types import TracebackType
from typing import ContextManager, Dict, Optional, Type

from sqlalchemy.orm import Session

from workmain.database.connection import get_db, scope_open
from workmain.database.repositories.ai_costs_repo import AiCostRepository
from workmain.database.repositories.client_repository import ClientRepository
from workmain.database.repositories.email_repository import EmailRepository
from workmain.database.repositories.gdrive_repository import GDriveRepository
from workmain.database.repositories.meetings_repo import MeetingsRepository
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.notification_repository import (
    NotificationConfigRepository,
)
from workmain.database.repositories.reports_repo import ReportsRepository
from workmain.database.repositories.schedule_repository import (
    ScheduleExceptionRepository,
)
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

_REENTRY_MESSAGE = (
    "A UnitOfWork is entered only once: this instance has already been entered."
)
_OPEN_SCOPE_MESSAGE = (
    "A UnitOfWork is not entered inside an open session_scope() or another "
    "unit of work; only a UnitOfWork(record=True) may be."
)


class UnitOfWork:
    """
    One transaction, and every repository built on its session.

    Attributes:
        REPOSITORIES: Attribute name to repository class; each is set on the
            instance while it is entered and removed when it exits.
    """

    REPOSITORIES: Dict[str, type] = {
        'ai_costs': AiCostRepository,
        'clients': ClientRepository,
        'email': EmailRepository,
        'gdrive_uploads': GDriveRepository,
        'meetings': MeetingsRepository,
        'notes': NotesRepository,
        'notification_config': NotificationConfigRepository,
        'reports': ReportsRepository,
        'schedule_exceptions': ScheduleExceptionRepository,
        'system_state': SystemStateRepository,
        'task_status': TaskStatusRepository,
        'time_entries': TimeEntriesRepository,
    }

    def __init__(self, record: bool = False) -> None:
        """
        Build a unit of work that has not been entered.

        Args:
            record: True to run on record_scope(), for a record of an outside
                action; False to run on session_scope()
        """
        self._record = record
        self._entered = False
        self._scope: Optional[ContextManager[Session]] = None

    def __enter__(self) -> 'UnitOfWork':
        """
        Open the scope and build the repositories on its session.

        Returns:
            This unit of work

        Raises:
            RuntimeError: This instance has been entered before, or it does not
                record and a session_scope() is already open on this thread.
                Nothing is opened or changed.
            BaseException: Building a repository raised. The scope is exited
                with that exception, no repository is left set, and the
                instance stays unentered.
        """
        if self._entered:
            raise RuntimeError(_REENTRY_MESSAGE)
        if not self._record and scope_open():
            raise RuntimeError(_OPEN_SCOPE_MESSAGE)
        db = get_db()
        scope = db.record_scope() if self._record else db.session_scope()
        session = scope.__enter__()
        try:
            for name, repository_class in self.REPOSITORIES.items():
                setattr(self, name, repository_class(session))
        except BaseException as error:
            for name in self.REPOSITORIES:
                self.__dict__.pop(name, None)
            scope.__exit__(type(error), error, error.__traceback__)
            raise
        self._entered = True
        self._scope = scope
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        """
        Hand the exit to the scope, then remove the repositories.

        Args:
            exc_type: The type of the exception leaving the block, or None
            exc: The exception leaving the block, or None
            traceback: Its traceback, or None

        Returns:
            False: an exception leaving the block always propagates
        """
        scope, self._scope = self._scope, None
        try:
            scope.__exit__(exc_type, exc, traceback)
        finally:
            for name in self.REPOSITORIES:
                self.__dict__.pop(name, None)
        return False

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
from datetime import date, datetime, timezone
from types import TracebackType
from typing import Dict, List, Optional, Type

from workmain.database.models import Client, Meeting, Note, TaskStatus
from workmain.database.repositories.client_repository import ClientRepository
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


def _rows(store: dict, table: str) -> dict:
    """Return the table's rows keyed by id, or an empty dict, without creating it."""
    return store.get(table, {})


def _next_id(rows: dict) -> int:
    """Return one more than the table's highest id, or 1 for an empty table."""
    return max(rows, default=0) + 1


def _build_note(store: dict, row: dict) -> Note:
    """
    Build a sessionless Note from a notes row, with its meeting.

    Args:
        store: The fake unit of work's store
        row: A notes row in FakeNotesRepository's shape

    Returns:
        A new Note whose created_date is created_at's date, as the computed
        column derives it, and whose meeting is a Meeting built from the
        meetings row meeting_id names, or None
    """
    created_at = row['created_at']
    note = Note(
        id=row['id'],
        content=row['content'],
        tags=row['tags'],
        created_at=created_at,
        created_date=None if created_at is None else created_at.date(),
        meeting_id=row['meeting_id'],
        client_id=row['client_id'],
    )
    meeting_row = _rows(store, 'meetings').get(row['meeting_id'])
    note.meeting = (
        None if meeting_row is None
        else Meeting(id=meeting_row['id'], title=meeting_row['title'])
    )
    return note


class FakeClientRepository:
    """
    The clients table, held in store['clients'], and the rows linked to it.

    Row shapes, each a dict keyed by id under store['<table>']:
        clients: id, name, is_active, created_at (aware, UTC)
        projects, report_recipients, reports, time_entries: id, client_id

    It also reads and unlinks notes and meetings rows, in the shapes
    FakeNotesRepository's docstring states, which hold client_id.
    """

    RESERVED_NAME = ClientRepository.RESERVED_NAME
    _TABLE = 'clients'
    _LINKED = (
        'meetings', 'notes', 'projects', 'report_recipients', 'reports', 'time_entries',
    )

    def __init__(self, store: dict) -> None:
        """
        Build the repository over the shared store.

        Args:
            store: The fake unit of work's store
        """
        self._store = store

    _validate_name = ClientRepository._validate_name

    @staticmethod
    def _client(row: dict) -> Client:
        """Build a new sessionless Client from a clients row."""
        return Client(
            id=row['id'],
            name=row['name'],
            is_active=row['is_active'],
            created_at=row['created_at'],
        )

    def _sorted_by_name(self, rows: List[dict]) -> List[Client]:
        """Build Clients from rows in name order, the order of collation C.UTF-8."""
        return [self._client(row) for row in sorted(rows, key=lambda row: row['name'])]

    def create(self, name: str) -> Client:
        """Write an inactive client, refusing the reserved name and a duplicate."""
        self._validate_name(name)
        if self.get_by_name(name) is not None:
            raise ValueError(f"A client named '{name}' already exists.")
        rows = self._store.setdefault(self._TABLE, {})
        client_id = _next_id(rows)
        rows[client_id] = {
            'id': client_id,
            'name': name,
            'is_active': False,
            'created_at': datetime.now(timezone.utc),
        }
        return self._client(rows[client_id])

    def get_by_id(self, client_id: int) -> Optional[Client]:
        """Return client by ID, or None if not found."""
        row = _rows(self._store, self._TABLE).get(client_id)
        return None if row is None else self._client(row)

    def get_by_name(self, name: str) -> Optional[Client]:
        """Return client by name (case-insensitive), or None if not found."""
        wanted = name.strip().lower()
        for row in _rows(self._store, self._TABLE).values():
            if row['name'].lower() == wanted:
                return self._client(row)
        return None

    def find_by_name_fuzzy(self, name: str) -> List[Client]:
        """Return clients whose names contain the search string (case-insensitive)."""
        wanted = name.strip().lower()
        return self._sorted_by_name(
            [row for row in _rows(self._store, self._TABLE).values()
             if wanted in row['name'].lower()]
        )

    def list_all(self) -> List[Client]:
        """Return all clients ordered by name."""
        return self._sorted_by_name(list(_rows(self._store, self._TABLE).values()))

    def delete(self, client_id: int) -> bool:
        """Delete a client and unlink its rows, as ON DELETE SET NULL does."""
        rows = _rows(self._store, self._TABLE)
        if client_id not in rows:
            return False
        del rows[client_id]
        for table in self._LINKED:
            for row in _rows(self._store, table).values():
                if row['client_id'] == client_id:
                    row['client_id'] = None
        return True

    def count_linked_records(self, client_id: int) -> Dict[str, int]:
        """Count the rows linked to a client, keyed by table in the real order."""
        return {
            table: sum(
                1 for row in _rows(self._store, table).values()
                if row['client_id'] == client_id
            )
            for table in self._LINKED
        }

    def set_active(self, client_id: int) -> Client:
        """Flag the client active, unflag the others, and store its id."""
        rows = _rows(self._store, self._TABLE)
        if client_id not in rows:
            raise ValueError(f"No client with ID {client_id}.")
        for row in rows.values():
            row['is_active'] = False
        rows[client_id]['is_active'] = True
        FakeSystemStateRepository(self._store).set_int('active_client_id', client_id)
        return self._client(rows[client_id])

    def clear_active(self) -> None:
        """Unflag every client and delete the stored active id."""
        for row in _rows(self._store, self._TABLE).values():
            row['is_active'] = False
        FakeSystemStateRepository(self._store).delete('active_client_id')

    def get_active(self) -> Optional[Client]:
        """Return the client the stored id names, else the flagged client with the lowest id."""
        client_id = FakeSystemStateRepository(self._store).get_int('active_client_id')
        if client_id is not None:
            client = self.get_by_id(client_id)
            if client is not None:
                return client
        rows = _rows(self._store, self._TABLE)
        for key in sorted(rows):
            if rows[key]['is_active']:
                return self._client(rows[key])
        return None


class FakeNotesRepository:
    """
    The notes table, held in store['notes'], and the meetings it names.

    Row shapes, each a dict keyed by id under store['<table>']:
        notes: id, content, tags, created_at (naive local time), meeting_id,
            client_id. A row has no created_date: a read derives it from
            created_at, as the computed column does.
        meetings: id, title, client_id
    """

    def __init__(self, store: dict) -> None:
        """
        Build the repository over the shared store.

        Args:
            store: The fake unit of work's store
        """
        self._store = store

    def get_by_id(self, note_id: int) -> Optional[Note]:
        """Return the note with its meeting, or None if not found."""
        row = _rows(self._store, 'notes').get(note_id)
        return None if row is None else _build_note(self._store, row)


class FakeTaskStatusRepository:
    """
    The task_status table, held in store['task_status'].

    Row shape, a dict keyed by id under store['task_status']:
        task_status: id, note_id, status, completed_at, forwarding_note_id,
            created_at, updated_at, each time naive local time

    It reads notes and meetings rows in the shapes FakeNotesRepository's
    docstring states.
    """

    _TABLE = 'task_status'

    def __init__(self, store: dict) -> None:
        """
        Build the repository over the shared store.

        Args:
            store: The fake unit of work's store
        """
        self._store = store

    def _task(self, row: dict) -> TaskStatus:
        """Build a new sessionless TaskStatus from a row, with its note when it exists."""
        task = TaskStatus(
            id=row['id'],
            note_id=row['note_id'],
            status=row['status'],
            completed_at=row['completed_at'],
            forwarding_note_id=row['forwarding_note_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )
        note_row = _rows(self._store, 'notes').get(row['note_id'])
        if note_row is not None:
            task.note = _build_note(self._store, note_row)
        return task

    def _row_for_note(self, note_id: int) -> Optional[dict]:
        """Return the task_status row for a note, or None."""
        for row in _rows(self._store, self._TABLE).values():
            if row['note_id'] == note_id:
                return row
        return None

    def _set_status(self, note_id: int, status: str) -> TaskStatus:
        """Set a task's status, completed_at and updated_at to now, as the real methods do."""
        row = self._row_for_note(note_id)
        if row is None:
            raise ValueError(f"No task_status record exists for note {note_id}.")
        now = datetime.now()
        row['status'] = status
        row['completed_at'] = now
        row['updated_at'] = now
        return self._task(row)

    def _filtered(
        self,
        status: Optional[str],
        search: Optional[str],
        date_filter: Optional[date],
    ) -> List[tuple]:
        """
        Return (task row, note row) pairs matching the filters, unordered.

        Only rows whose note exists are kept, as the real inner join keeps
        them. A status of None or 'all' does not filter. search matches the
        note's content as a case-insensitive substring, % and _ literally.
        """
        notes = _rows(self._store, 'notes')
        pairs = []
        for row in _rows(self._store, self._TABLE).values():
            note = notes.get(row['note_id'])
            if note is None:
                continue
            if status and status != 'all' and row['status'] != status:
                continue
            if search and search.lower() not in note['content'].lower():
                continue
            created_at = note['created_at']
            if date_filter and (created_at is None or created_at.date() != date_filter):
                continue
            pairs.append((row, note))
        return pairs

    def set_completed(self, note_id: int) -> TaskStatus:
        """Mark task as completed."""
        return self._set_status(note_id, 'completed')

    def set_dismissed(self, note_id: int) -> TaskStatus:
        """Mark task as dismissed."""
        return self._set_status(note_id, 'dismissed')

    def get_by_note_id(self, note_id: int) -> Optional[TaskStatus]:
        """Return the task_status record for a note, or None."""
        row = self._row_for_note(note_id)
        return None if row is None else self._task(row)

    def get_filtered(
        self,
        status: Optional[str] = 'active',
        search: Optional[str] = None,
        date_filter: Optional[date] = None,
        limit: int = 20,
    ) -> List[TaskStatus]:
        """
        Return matching tasks, newest note first, a None created_at first.

        Tied created_at values keep Python's stable sort order, where SQL
        leaves their order unstated. A limit of 0 means no limit.
        """
        pairs = sorted(
            self._filtered(status, search, date_filter),
            key=lambda pair: (
                pair[1]['created_at'] is None,
                pair[1]['created_at'] or datetime.min,
            ),
            reverse=True,
        )
        if limit:
            pairs = pairs[:limit]
        return [self._task(row) for row, _ in pairs]

    def count_filtered(
        self,
        status: Optional[str] = 'active',
        search: Optional[str] = None,
        date_filter: Optional[date] = None,
    ) -> int:
        """Return the total count of tasks matching the filters, unpaginated."""
        return len(self._filtered(status, search, date_filter))


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
        'clients': FakeClientRepository,
        'notes': FakeNotesRepository,
        'system_state': FakeSystemStateRepository,
        'task_status': FakeTaskStatusRepository,
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

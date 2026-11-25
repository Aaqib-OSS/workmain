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
from datetime import date, datetime, time, timezone
from decimal import Decimal
from types import TracebackType
from typing import Dict, List, Optional, Type

from workmain.database.models import Client, Meeting, Note, TaskStatus, TimeEntry
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


def _build_meeting(row: dict) -> Meeting:
    """
    Build a sessionless Meeting from a meetings row.

    Args:
        row: A meetings row in FakeMeetingsRepository's shape; a seed that
            never reaches FakeMeetingsRepository may omit every key but id,
            title and client_id, and each omitted key reads as None

    Returns:
        A new Meeting
    """
    return Meeting(
        id=row['id'],
        title=row['title'],
        client_id=row.get('client_id'),
        start_time=row.get('start_time'),
        end_time=row.get('end_time'),
        condensed_summary=row.get('condensed_summary'),
        condensed_at=row.get('condensed_at'),
    )


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
        source=row.get('source'),
        created_at=created_at,
        created_date=None if created_at is None else created_at.date(),
        meeting_id=row['meeting_id'],
        project_id=row.get('project_id'),
        client_id=row['client_id'],
    )
    meeting_row = _rows(store, 'meetings').get(row['meeting_id'])
    note.meeting = None if meeting_row is None else _build_meeting(meeting_row)
    return note


def _validate_client_project(
    store: dict, client_id: int | None, project_id: int | None, record: str
) -> None:
    """
    Refuse a project of another client, as the real repositories do.

    Args:
        store: The fake unit of work's store; projects rows are id, client_id
        client_id: The row's client, or None
        project_id: The row's project, or None
        record: 'note' or 'time entry', as the real message names it

    Raises:
        ValueError: The project does not exist, or belongs to another client,
            with the real repository's message. Nothing is checked unless
            both ids are set.
    """
    if project_id is None or client_id is None:
        return
    project = _rows(store, 'projects').get(project_id)
    if project is None:
        raise ValueError(f"Project {project_id} does not exist")
    if project['client_id'] != client_id:
        raise ValueError(
            f"Project {project_id} belongs to client {project['client_id']}, "
            f"not client {client_id}. Cannot link {record} to mismatched project."
        )


class FakeClientRepository:
    """
    The clients table, held in store['clients'], and the rows linked to it.

    Row shapes, each a dict keyed by id under store['<table>']:
        clients: id, name, is_active, created_at (aware, UTC)
        projects, report_recipients, reports: id, client_id

    It also reads and unlinks notes, meetings and time_entries rows, in the
    shapes FakeNotesRepository's, FakeMeetingsRepository's and
    FakeTimeEntriesRepository's docstrings state, which hold client_id.
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
        notes: id, content, tags, source, created_at (naive local time),
            meeting_id, project_id, client_id. A row has no created_date: a
            read derives it from created_at, as the computed column does. A
            seed may omit source and project_id, which read as None.
        meetings: in FakeMeetingsRepository's shape
        projects: id, client_id, read when a note names a project
    """

    def __init__(self, store: dict) -> None:
        """
        Build the repository over the shared store.

        Args:
            store: The fake unit of work's store
        """
        self._store = store

    def create(
        self,
        content: str,
        tags: list[str],
        project_id: int | None = None,
        meeting_id: int | None = None,
        source: str = 'ad-hoc',
        created_at: datetime | None = None,
        client_id: int | None = None,
    ) -> Note:
        """Write a note with its tags deduplicated and sorted, refusing another client's project."""
        _validate_client_project(self._store, client_id, project_id, 'note')
        rows = self._store.setdefault('notes', {})
        note_id = _next_id(rows)
        rows[note_id] = {
            'id': note_id,
            'content': content,
            'tags': sorted(set(tags)) if tags else [],
            'source': source,
            'created_at': created_at or datetime.now(),
            'meeting_id': meeting_id,
            'project_id': project_id,
            'client_id': client_id,
        }
        return _build_note(self._store, rows[note_id])

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

    def ensure_active(self, note_id: int) -> TaskStatus:
        """Return the note's task made active, creating it when the note has none."""
        row = self._row_for_note(note_id)
        if row is None:
            rows = self._store.setdefault(self._TABLE, {})
            task_id = _next_id(rows)
            now = datetime.now()
            row = rows[task_id] = {
                'id': task_id,
                'note_id': note_id,
                'status': 'active',
                'completed_at': None,
                'forwarding_note_id': None,
                'created_at': now,
                'updated_at': now,
            }
        elif row['status'] != 'active':
            row['status'] = 'active'
            row['completed_at'] = None
            row['forwarding_note_id'] = None
            row['updated_at'] = datetime.now()
        return self._task(row)

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


class FakeTimeEntriesRepository:
    """
    The time_entries table, held in store['time_entries'].

    Row shape, a dict keyed by id under store['time_entries']:
        time_entries: id, note_id, duration_hours (Decimal), entry_date,
            entry_time, category, project_id, meeting_id, client_id,
            clockify_id, synced_at, created_at (naive local time)

    It reads notes rows in FakeNotesRepository's shape, to attach each
    entry's note, and projects rows (id, client_id) to check an entry's
    project.
    """

    _TABLE = 'time_entries'

    def __init__(self, store: dict) -> None:
        """
        Build the repository over the shared store.

        Args:
            store: The fake unit of work's store
        """
        self._store = store

    def _entry(self, row: dict) -> TimeEntry:
        """Build a new sessionless TimeEntry from a row, with its note when it exists."""
        entry = TimeEntry(
            id=row['id'],
            note_id=row['note_id'],
            duration_hours=row['duration_hours'],
            entry_date=row['entry_date'],
            entry_time=row['entry_time'],
            category=row['category'],
            project_id=row['project_id'],
            meeting_id=row['meeting_id'],
            client_id=row['client_id'],
            clockify_id=row['clockify_id'],
            synced_at=row['synced_at'],
            created_at=row['created_at'],
        )
        note_row = _rows(self._store, 'notes').get(row['note_id'])
        if note_row is not None:
            entry.note = _build_note(self._store, note_row)
        return entry

    def create(
        self,
        note_id: int,
        duration_hours: float,
        entry_date: date,
        entry_time: time,
        category: str | None = None,
        project_id: int | None = None,
        meeting_id: int | None = None,
        client_id: int | None = None,
        clockify_id: str | None = None,
        synced_at: datetime | None = None,
        created_at: datetime | None = None,
    ) -> TimeEntry:
        """Write an entry, its duration as a Decimal, refusing another client's project."""
        _validate_client_project(self._store, client_id, project_id, 'time entry')
        rows = self._store.setdefault(self._TABLE, {})
        entry_id = _next_id(rows)
        rows[entry_id] = {
            'id': entry_id,
            'note_id': note_id,
            'duration_hours': Decimal(str(duration_hours)),
            'entry_date': entry_date,
            'entry_time': entry_time,
            'category': category,
            'project_id': project_id,
            'meeting_id': meeting_id,
            'client_id': client_id,
            'clockify_id': clockify_id,
            'synced_at': synced_at,
            'created_at': created_at or datetime.now(),
        }
        return self._entry(rows[entry_id])

    def get_by_meeting(self, meeting_id: int) -> list[TimeEntry]:
        """
        Return the meeting's entries with their notes, by date then time.

        Entries tied on both keep Python's stable sort order, where SQL
        leaves their order unstated.
        """
        rows = [
            row for row in _rows(self._store, self._TABLE).values()
            if row['meeting_id'] == meeting_id
        ]
        rows.sort(key=lambda row: (row['entry_date'], row['entry_time']))
        return [self._entry(row) for row in rows]

    def update(
        self,
        entry_id: int,
        duration_hours: float | None = None,
        entry_time: time | None = None,
        category: str | None = None,
        project_id: int | None = None,
        meeting_id: int | None = None,
        note_id: int | None = None,
    ) -> TimeEntry | None:
        """
        Change the given fields, keeping each one passed as None.

        The entry's own client is checked against the project it ends with,
        as the real method checks it, before anything changes. Returns None
        when no entry has the id.
        """
        row = _rows(self._store, self._TABLE).get(entry_id)
        if row is None:
            return None
        effective_project_id = project_id if project_id is not None else row['project_id']
        _validate_client_project(
            self._store, row['client_id'], effective_project_id, 'time entry'
        )
        if duration_hours is not None:
            row['duration_hours'] = Decimal(str(duration_hours))
        changes = {
            'entry_time': entry_time, 'category': category, 'project_id': project_id,
            'meeting_id': meeting_id, 'note_id': note_id,
        }
        for key, value in changes.items():
            if value is not None:
                row[key] = value
        return self._entry(row)


class FakeMeetingsRepository:
    """
    The meetings table, held in store['meetings'].

    Row shape, a dict keyed by id under store['meetings']:
        meetings: id, title, client_id, start_time, end_time,
            condensed_summary, condensed_at, each time naive local time. A
            seed that never reaches this repository may hold only id, title
            and client_id.
    """

    _TABLE = 'meetings'

    def __init__(self, store: dict) -> None:
        """
        Build the repository over the shared store.

        Args:
            store: The fake unit of work's store
        """
        self._store = store

    def get_by_id(self, meeting_id: int) -> Meeting | None:
        """Return the meeting, or None if not found."""
        row = _rows(self._store, self._TABLE).get(meeting_id)
        return None if row is None else _build_meeting(row)

    def set_condensed_summary(
        self, meeting_id: int, summary: str, condensed_at: datetime
    ) -> Meeting | None:
        """Set the summary and when it was condensed; None if no meeting has the id."""
        row = _rows(self._store, self._TABLE).get(meeting_id)
        if row is None:
            return None
        row['condensed_summary'] = summary
        row['condensed_at'] = condensed_at
        return _build_meeting(row)


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
        'meetings': FakeMeetingsRepository,
        'notes': FakeNotesRepository,
        'system_state': FakeSystemStateRepository,
        'task_status': FakeTaskStatusRepository,
        'time_entries': FakeTimeEntriesRepository,
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

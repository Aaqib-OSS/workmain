"""
Service layer for the task lifecycle (carry-forward notes).

Shared by the tasks CLI group. Each public function is a use case: it takes
a UnitOfWork not yet entered, enters it once, and returns frozen dataclasses
built inside it. _task_for_note is an operation on an entered unit of work,
and never enters one.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Tuple

from workmain.database.models import Note, TaskStatus
from workmain.services.exceptions import NotATaskError, TaskNotFoundError
from workmain.services.results import Page
from workmain.services.unit_of_work import UnitOfWork

FIND_LIMIT = 10


@dataclass(frozen=True)
class TaskRow:
    """A task as a collection shows it."""

    note_id: int
    status: str
    created_date: Optional[date]
    tags: Tuple[str, ...]
    content: str


@dataclass(frozen=True)
class TaskDetail:
    """A task as a record shows it."""

    note_id: int
    status: str
    created_at: Optional[datetime]
    completed_at: Optional[datetime]
    dismissed_at: Optional[datetime]
    forwarding_note_id: Optional[int]
    tags: Tuple[str, ...]
    meeting_id: Optional[int]
    meeting_title: Optional[str]
    content: str


def _row(ts: TaskStatus) -> TaskRow:
    note = ts.note
    return TaskRow(
        note_id=note.id,
        status=ts.status,
        created_date=note.created_date,
        tags=tuple(note.tags or ()),
        content=note.content or "",
    )


def _page(rows, total: int, filters) -> Page[TaskRow]:
    return Page(rows=tuple(_row(ts) for ts in rows), total=total, filters=tuple(filters))


def list_tasks(
    uow: UnitOfWork,
    status: str,
    search: Optional[str],
    created: Optional[date],
    limit: int,
) -> Page[TaskRow]:
    """
    Return tasks matching the filters, newest first.

    Args:
        uow: A unit of work not yet entered; this function enters it.
        status: 'active', 'completed', 'dismissed' or 'all'.
        search: Keyword matched against note content, or None.
        created: Note creation date, or None.
        limit: Maximum rows; 0 means no cap.
    """
    filters = []
    if status != "all":
        filters.append(("status", status))
    if search:
        filters.append(("search", search))
    if created:
        filters.append(("created", created))
    with uow:
        repo = uow.task_status
        rows = repo.get_filtered(
            status=status, search=search, date_filter=created, limit=limit
        )
        total = repo.count_filtered(status=status, search=search, date_filter=created)
        return _page(rows, total, filters)


def list_today(uow: UnitOfWork, search: Optional[str], today: date) -> Page[TaskRow]:
    """Return the active tasks created on `today`."""
    filters = [("status", "active"), ("created", today)]
    if search:
        filters.append(("search", search))
    with uow:
        rows = uow.task_status.get_filtered(
            status="active", search=search, date_filter=today, limit=0
        )
        return _page(rows, len(rows), filters)


def find_tasks(uow: UnitOfWork, identifier: str) -> Page[TaskRow]:
    """Resolve an identifier to candidate tasks.

    A digit string is a note ID. Anything else searches tasks in every
    status, newest first, capped at FIND_LIMIT.

    Raises:
        TaskNotFoundError: No note has the ID, or no task matches the text.
        NotATaskError: The note exists but has no task_status row.
    """
    with uow:
        repo = uow.task_status
        if identifier.isdigit():
            note_id = int(identifier)
            note = uow.notes.get_by_id(note_id)
            if note is None:
                raise TaskNotFoundError(f"No note found with ID {note_id}.")
            ts = repo.get_by_note_id(note_id)
            if ts is None:
                raise NotATaskError(note_id)
            return _page([ts], 1, ())

        rows = repo.get_filtered(status="all", search=identifier, limit=FIND_LIMIT)
        if not rows:
            raise TaskNotFoundError(f"No tasks found matching '{identifier}'.")
        total = repo.count_filtered(status="all", search=identifier)
        return _page(rows, total, (("search", identifier),))


def _task_for_note(uow: UnitOfWork, note_id: int) -> TaskStatus:
    """Return the note's task; uow is already entered."""
    note = uow.notes.get_by_id(note_id)
    if note is None:
        raise TaskNotFoundError(f"No note found with ID {note_id}.")
    ts = uow.task_status.get_by_note_id(note_id)
    if ts is None:
        raise NotATaskError(note_id)
    return ts


def get_task(uow: UnitOfWork, note_id: int) -> TaskDetail:
    """Return one task's detail.

    Raises:
        TaskNotFoundError: No note has the ID.
        NotATaskError: The note has no task_status row.
    """
    with uow:
        ts = _task_for_note(uow, note_id)
        note: Note = ts.note
        meeting = note.meeting
        return TaskDetail(
            note_id=note.id,
            status=ts.status,
            created_at=note.created_at,
            completed_at=ts.completed_at if ts.status == "completed" else None,
            dismissed_at=ts.completed_at if ts.status == "dismissed" else None,
            forwarding_note_id=ts.forwarding_note_id,
            tags=tuple(note.tags or ()),
            meeting_id=meeting.id if meeting else None,
            meeting_title=meeting.title if meeting else None,
            content=note.content or "",
        )


def complete_task(uow: UnitOfWork, note_id: int) -> TaskRow:
    """Mark a task completed and return it."""
    with uow:
        _task_for_note(uow, note_id)
        ts = uow.task_status.set_completed(note_id)
        return _row(ts)


def dismiss_task(uow: UnitOfWork, note_id: int) -> TaskRow:
    """Mark a task dismissed and return it."""
    with uow:
        _task_for_note(uow, note_id)
        ts = uow.task_status.set_dismissed(note_id)
        return _row(ts)

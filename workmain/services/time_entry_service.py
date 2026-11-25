"""
Every time-entry write, including the time-entry half of every paired write.

log_meeting_time and log_task_time are use cases: each takes a UnitOfWork not
yet entered, enters it once, and returns a frozen dataclass of plain values
built inside it. create_time_entry, create_paired_time_entry and
link_condensed_note are operations on a unit of work already entered, which
never enter one; meetings_service.record_condensation and
clockify_service.apply_pull call them inside their own unit of work.

Every entry is written with its note first (the note-first pattern): a task's
note is written by create_time_entry, and every other entry's note by
notes_service.create_note before create_paired_time_entry pairs an entry with
it.
"""

from dataclasses import dataclass
from datetime import date, datetime
from datetime import time as time_type
from decimal import Decimal

from workmain.database.models import Note, TimeEntry
from workmain.services import notes_service
from workmain.services.exceptions import (
    InvalidTagsError,
    MissingStartTimeError,
    ServiceValidationError,
)
from workmain.services.notes_service import apply_cf_hook_on_create
from workmain.services.unit_of_work import UnitOfWork
from workmain.utils.tag_utils import get_tag_system


@dataclass(frozen=True)
class CreatedEntry:
    """
    A time entry a use case wrote, with its note.

    Attributes:
        entry_id: The time entry's id
        note_id: The id of the note the entry points at
        content: The note's text, the entry's description
        duration_hours: The entry's duration in hours
        display_time: The entry's start time as displayed, e.g. "14:30"
    """

    entry_id: int
    note_id: int
    content: str
    duration_hours: Decimal
    display_time: str


def create_time_entry(
    uow: UnitOfWork,
    description: str,
    duration_hours: float,
    entry_time: time_type | None = None,
    entry_date: date | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    meeting_id: int | None = None,
    project_id: int | None = None,
) -> TimeEntry:
    """
    Write a task's note and its time entry, with the active client stamped.

    The note is written with source='task' and never carries a meeting_id,
    by design: a task-shaped entry belongs to no meeting's notes, and
    meeting_id, where one is given, is set on the time entry alone. Writes a
    notes row, a task_status row when the tags include carry-forward, and a
    time_entries row.

    Args:
        uow: A unit of work already entered
        description: Entry description, used as the note's content
        duration_hours: Duration in hours (e.g. 1.5)
        entry_time: Start time; required
        entry_date: Calendar date; today if None
        category: Optional category string, passed through unvalidated
        tags: Full-name tags; None or empty defaults to ["internal-only"]
        meeting_id: The time entry's meeting, or None
        project_id: Optional project ID

    Returns:
        The created TimeEntry, with .note readable while uow is entered

    Raises:
        MissingStartTimeError: entry_time is None
        InvalidTagsError: A tag is outside the configured vocabulary
    """
    if entry_time is None:
        raise MissingStartTimeError()

    if entry_date is None:
        entry_date = date.today()

    tag_system = get_tag_system()

    if not tags:
        resolved_tags = ["internal-only"]
    else:
        _, invalid = tag_system.validate_full_names(tags)
        if invalid:
            valid_vocab = tag_system.get_valid_full_names()
            raise InvalidTagsError(invalid_tags=invalid, valid_tags=valid_vocab)
        resolved_tags = tags

    active_client_id = uow.system_state.get_int("active_client_id")

    # Backdate the note's created_at to entry_date when it is not today, so
    # date-scoped report queries find the note.
    note_created_at = (
        datetime.combine(entry_date, datetime.now().time())
        if entry_date != date.today() else None
    )

    note = uow.notes.create(
        content=description,
        tags=resolved_tags,
        source="task",
        client_id=active_client_id,
        created_at=note_created_at,
    )
    apply_cf_hook_on_create(uow, note)

    return uow.time_entries.create(
        note_id=note.id,
        duration_hours=duration_hours,
        entry_date=entry_date,
        entry_time=entry_time,
        category=category,
        client_id=active_client_id,
        meeting_id=meeting_id,
        project_id=project_id,
    )


def create_paired_time_entry(
    uow: UnitOfWork,
    note: Note,
    duration_hours: float,
    entry_date: date,
    entry_time: time_type,
    category: str | None = None,
    project_id: int | None = None,
    clockify_id: str | None = None,
) -> TimeEntry:
    """
    Write the time-entry half of a note and time-entry pair.

    meeting_id and client_id are derived from the already-created note so the
    pair cannot diverge. synced_at is stamped whenever clockify_id is
    supplied. Writes one time_entries row.

    Args:
        uow: A unit of work already entered
        note: The note just created in uow
        duration_hours: Duration in hours
        entry_date: Calendar date
        entry_time: Start time
        category: Optional category string
        project_id: Optional project ID
        clockify_id: The Clockify entry's id, for an imported entry

    Returns:
        The created TimeEntry

    Raises:
        ValueError: The project belongs to another client
    """
    return uow.time_entries.create(
        note_id=note.id,
        duration_hours=duration_hours,
        entry_date=entry_date,
        entry_time=entry_time,
        category=category,
        project_id=project_id,
        meeting_id=note.meeting_id,
        client_id=note.client_id,
        clockify_id=clockify_id,
        synced_at=datetime.now() if clockify_id else None,
    )


def link_condensed_note(
    uow: UnitOfWork,
    meeting_id: int,
    condensed_note: Note,
) -> tuple[TimeEntry, bool]:
    """
    Point the meeting's time entry on its date at the condensed note.

    Creates an entry from the meeting when it has none on its date. Where the
    meeting has more than one entry on its date, only the earliest is
    repointed.

    Args:
        uow: A unit of work already entered
        meeting_id: The condensed meeting
        condensed_note: The note created from the condensed summary, in uow

    Returns:
        The repointed or created TimeEntry, and True if it was created

    Raises:
        ServiceValidationError: No meeting has meeting_id
        ValueError: The existing entry's project belongs to another client
    """
    meeting = uow.meetings.get_by_id(meeting_id)
    if meeting is None:
        raise ServiceValidationError(f"No meeting found with ID {meeting_id}.")
    meeting_date = meeting.start_time.date()
    existing_today = [
        e for e in uow.time_entries.get_by_meeting(meeting_id) if e.entry_date == meeting_date
    ]
    if existing_today:
        return uow.time_entries.update(existing_today[0].id, note_id=condensed_note.id), False
    duration_hours = (meeting.end_time - meeting.start_time).total_seconds() / 3600
    entry = create_paired_time_entry(
        uow,
        condensed_note,
        duration_hours=duration_hours,
        entry_date=meeting_date,
        entry_time=meeting.start_time.time(),
        category='meeting',
    )
    return entry, True


def log_meeting_time(
    uow: UnitOfWork,
    meeting_id: int,
    content: str,
    tags: list[str] | None,
    duration_hours: float,
    entry_date: date,
    entry_time: time_type,
    category: str | None = 'meeting',
    project_id: int | None = None,
    created_at: datetime | None = None,
) -> CreatedEntry:
    """
    Write a meeting's note and the time entry paired with it.

    Writes a notes row with source='meeting' and the meeting's id, a
    task_status row when the tags include carry-forward, and a time_entries
    row whose meeting and client come from that note. All commit together or
    none does.

    Args:
        uow: A unit of work not yet entered; this function enters it
        meeting_id: The meeting the time was spent in
        content: The note's text, the entry's description
        tags: Full-name tags; None or empty defaults to ["internal-only"]
        duration_hours: Duration in hours
        entry_date: Calendar date
        entry_time: Start time
        category: The entry's category; 'meeting' by default
        project_id: The entry's project, or None
        created_at: Override the note's creation timestamp (backdating)

    Returns:
        The entry written, with its note

    Raises:
        InvalidTagsError: A tag is outside the configured vocabulary
        ValueError: The project belongs to another client
    """
    with uow:
        note = notes_service.create_note(
            uow,
            content=content,
            tags=tags,
            source='meeting',
            meeting_id=meeting_id,
            created_at=created_at,
        )
        entry = create_paired_time_entry(
            uow,
            note,
            duration_hours=duration_hours,
            entry_date=entry_date,
            entry_time=entry_time,
            category=category,
            project_id=project_id,
        )
        return CreatedEntry(
            entry_id=entry.id,
            note_id=note.id,
            content=note.content,
            duration_hours=entry.duration_hours,
            display_time=entry.display_time,
        )


def log_task_time(
    uow: UnitOfWork,
    description: str,
    duration_hours: float,
    entry_time: time_type | None = None,
    entry_date: date | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    project_id: int | None = None,
) -> CreatedEntry:
    """
    Write a task's note and its time entry.

    Writes a notes row with source='task', which never carries a meeting_id,
    by design; a task_status row when the tags include carry-forward; and a
    time_entries row. All commit together or none does.

    Args:
        uow: A unit of work not yet entered; this function enters it
        description: Entry description, used as the note's content
        duration_hours: Duration in hours
        entry_time: Start time; required
        entry_date: Calendar date; today if None
        category: Optional category string
        tags: Full-name tags; None or empty defaults to ["internal-only"]
        project_id: Optional project ID

    Returns:
        The entry written, with its note

    Raises:
        MissingStartTimeError: entry_time is None; nothing is written
        InvalidTagsError: A tag is outside the configured vocabulary
        ValueError: The project belongs to another client
    """
    with uow:
        entry = create_time_entry(
            uow,
            description=description,
            duration_hours=duration_hours,
            entry_time=entry_time,
            entry_date=entry_date,
            category=category,
            tags=tags,
            project_id=project_id,
        )
        return CreatedEntry(
            entry_id=entry.id,
            note_id=entry.note_id,
            content=description,
            duration_hours=entry.duration_hours,
            display_time=entry.display_time,
        )

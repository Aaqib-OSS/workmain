"""
Meeting records, and a meeting's condensation.

record_condensation is a use case: it takes a UnitOfWork not yet entered,
enters it once, and returns a frozen dataclass of plain values built inside
it. It writes a meeting's condensed summary together with the condensed note
and the time entry linked to it, so the three commit together or none does.
The summary itself comes from NoteCondenser.condense_meeting, which the
caller runs first and which writes nothing.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from workmain.services import notes_service, time_entry_service
from workmain.services.exceptions import ServiceValidationError
from workmain.services.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CondensedEntry:
    """
    What record_condensation wrote.

    Attributes:
        note_id: The condensed note's id
        entry_id: The id of the time entry pointing at the condensed note
        duration_hours: That entry's duration in hours
        created: True if the entry was created, False if an existing one was
            repointed
    """

    note_id: int
    entry_id: int
    duration_hours: Decimal
    created: bool


def record_condensation(
    uow: UnitOfWork, meeting_id: int, summary: str, tags: list[str]
) -> CondensedEntry:
    """
    Record a meeting's condensation: its summary, its note and its time entry.

    Writes the meeting's condensed_summary and condensed_at; a notes row with
    source='condensed', the summary as content and the meeting's id; a
    task_status row when the tags include carry-forward; and either repoints
    the meeting's earliest time entry on its date at that note or writes a
    time_entries row from the meeting's times. All commit together or none
    does.

    Args:
        uow: A unit of work not yet entered; this function enters it
        meeting_id: The condensed meeting
        summary: The condensed summary
        tags: Full-name tags for the condensed note

    Returns:
        The condensed note and the entry linked to it

    Raises:
        ServiceValidationError: No meeting has meeting_id; nothing is written
        InvalidTagsError: A tag is outside the configured vocabulary
        ValueError: The existing entry's project belongs to another client
    """
    with uow:
        meeting = uow.meetings.set_condensed_summary(meeting_id, summary, datetime.now())
        if meeting is None:
            raise ServiceValidationError(f"No meeting found with ID {meeting_id}.")
        note = notes_service.create_note(
            uow,
            content=summary,
            tags=tags,
            meeting_id=meeting_id,
            source='condensed',
        )
        entry, created = time_entry_service.link_condensed_note(uow, meeting_id, note)
        return CondensedEntry(
            note_id=note.id,
            entry_id=entry.id,
            duration_hours=entry.duration_hours,
            created=created,
        )

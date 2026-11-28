"""
Every note write, and the carry-forward to task-status hook.

add_note is a use case: it takes a UnitOfWork not yet entered, enters it once,
and returns a frozen dataclass of plain values built inside it. create_note
and apply_cf_hook_on_create are operations on a unit of work already entered,
which never enter one; the use cases in time_entry_service, meetings_service
and clockify_service call them inside their own unit of work. update_note and
apply_cf_hook_on_tag_update still take a session their caller owns, until
notes edit is converted (#209).

create_note stamps the active client, validates tags against the configured
vocabulary and defaults them to internal-only.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from workmain.database.models import Note
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services.exceptions import InvalidTagsError
from workmain.services.unit_of_work import UnitOfWork
from workmain.utils.tag_utils import get_tag_system


@dataclass(frozen=True)
class CreatedNote:
    """
    A note add_note wrote.

    Attributes:
        id: The note's id
        content: The note's text
        display_tags: The note's tags as displayed, e.g. "[internal-only]"
    """

    id: int
    content: str
    display_tags: str


def apply_cf_hook_on_create(uow: UnitOfWork, note: Note) -> None:
    """
    Create an active task-status row if the note carries carry-forward.

    Args:
        uow: A unit of work already entered
        note: The note just created in uow
    """
    if 'carry-forward' in (note.tags or []):
        uow.task_status.ensure_active(note.id)


def apply_cf_hook_on_tag_update(
    session, note_id: int, old_tags: List[str], new_tags: List[str]
) -> None:
    """Handle a CF tag transition (add or remove) on an existing note.
    Relocated verbatim from notes.py:500-507 (Phase 12 Gate 3)."""
    if new_tags is None:
        return
    task_repo = TaskStatusRepository(session)
    if 'carry-forward' in new_tags and 'carry-forward' not in (old_tags or []):
        task_repo.ensure_active(note_id)
    elif 'carry-forward' not in new_tags and 'carry-forward' in (old_tags or []):
        task_repo.set_dismissed_by_tag_removal(note_id)


def create_note(
    uow: UnitOfWork,
    content: str,
    tags: list[str] | None = None,
    source: str = "ad-hoc",
    meeting_id: int | None = None,
    project_id: int | None = None,
    created_at: datetime | None = None,
) -> Note:
    """
    Write a note with the active client stamped and its tags validated.

    Writes one notes row, and a task_status row when the tags include
    carry-forward.

    Args:
        uow: A unit of work already entered
        content: Note text content
        tags: Full-name tags (e.g. ["internal-only"]); None or empty defaults
            to ["internal-only"]
        source: Note origin: "ad-hoc" (default), "task", "meeting",
            "condensed" or "clockify"
        meeting_id: The meeting the note belongs to, or None
        project_id: The project the note belongs to, or None
        created_at: Override creation timestamp (backdating); None means now

    Returns:
        The created Note, valid while uow is entered

    Raises:
        InvalidTagsError: A tag is outside the configured vocabulary
    """
    tag_system = get_tag_system()

    if not tags:
        resolved_tags = ["internal-only"]
    else:
        _, invalid = tag_system.validate_full_names(tags)
        if invalid:
            valid_vocab = tag_system.get_valid_full_names()
            raise InvalidTagsError(invalid_tags=invalid, valid_tags=valid_vocab)
        resolved_tags = tags

    active_client = uow.clients.get_active()
    active_client_id = active_client.id if active_client is not None else None

    note = uow.notes.create(
        content=content,
        tags=resolved_tags,
        source=source,
        client_id=active_client_id,
        meeting_id=meeting_id,
        project_id=project_id,
        created_at=created_at,
    )
    apply_cf_hook_on_create(uow, note)
    return note


def add_note(
    uow: UnitOfWork,
    content: str,
    tags: list[str] | None = None,
    source: str = "ad-hoc",
    meeting_id: int | None = None,
    project_id: int | None = None,
    created_at: datetime | None = None,
) -> CreatedNote:
    """
    Write one note on its own, with no time entry.

    Writes one notes row, and a task_status row when the tags include
    carry-forward, as create_note does; both commit together or not at all.

    Args:
        uow: A unit of work not yet entered; this function enters it
        content: Note text content
        tags: Full-name tags; None or empty defaults to ["internal-only"]
        source: Note origin, as create_note takes it
        meeting_id: The meeting the note belongs to, or None
        project_id: The project the note belongs to, or None
        created_at: Override creation timestamp (backdating); None means now

    Returns:
        The note written

    Raises:
        InvalidTagsError: A tag is outside the configured vocabulary; nothing
            is written
    """
    with uow:
        note = create_note(
            uow,
            content=content,
            tags=tags,
            source=source,
            meeting_id=meeting_id,
            project_id=project_id,
            created_at=created_at,
        )
        return CreatedNote(id=note.id, content=note.content, display_tags=note.display_tags)


def update_note(
    session,
    note_id: int,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    meeting_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> Note:
    """General note update; applies the CF-transition hook when tags change.

    Single repo call — relies on NotesRepository.update()'s existing
    None-means-unchanged partial-update semantics. Do not split this into
    per-field update calls (Design Rule, Item 69 Gate 2).

    Args:
        session: SQLAlchemy session (caller manages lifecycle).
        note_id: Note to update.
        content: New content, or None to leave unchanged.
        tags: New full-name tags, or None to leave unchanged. Invalid values
              raise InvalidTagsError.
        meeting_id: New meeting ID, or None to leave unchanged.
        project_id: New project ID, or None to leave unchanged.

    Returns:
        The updated Note ORM object.

    Raises:
        InvalidTagsError: If any tag is outside the configured vocabulary.
    """
    existing = NotesRepository(session).get_by_id(note_id)
    old_tags = list(existing.tags or [])

    if tags is not None:
        tag_system = get_tag_system()
        _, invalid = tag_system.validate_full_names(tags)
        if invalid:
            valid_vocab = tag_system.get_valid_full_names()
            raise InvalidTagsError(invalid_tags=invalid, valid_tags=valid_vocab)

    updated_note = NotesRepository(session).update(
        note_id=note_id,
        content=content,
        tags=tags,
        meeting_id=meeting_id,
        project_id=project_id,
    )

    if tags is not None:
        apply_cf_hook_on_tag_update(session, note_id, old_tags, tags)

    return updated_note

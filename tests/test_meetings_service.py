"""
Tests for workmain/services/meetings_service.py, on fake_uow.

record_condensation writes a meeting's summary, the condensed note and the
linked entry in one unit of work; rows are seeded into the fake's store in
the shapes tests/mocks/fake_unit_of_work.py states.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest

from tests.mocks.fake_unit_of_work import FakeUnitOfWork
from workmain.services import meetings_service
from workmain.services.exceptions import InvalidTagsError, ServiceValidationError

_START = datetime(2099, 3, 1, 9, 0)


def _seed_meeting(store: dict) -> int:
    store['meetings'] = {1: {
        'id': 1, 'title': 'Sentinel condense', 'client_id': None, 'start_time': _START,
        'end_time': _START + timedelta(minutes=45), 'condensed_summary': None,
        'condensed_at': None,
    }}
    return 1


def _seed_entry(store: dict, meeting_id: int, client_id: int | None = None,
                project_id: int | None = None) -> int:
    store['notes'] = {1: {
        'id': 1, 'content': 'Detail', 'tags': ['internal-only'], 'source': 'meeting',
        'created_at': _START, 'meeting_id': meeting_id, 'project_id': None, 'client_id': None,
    }}
    store['time_entries'] = {1: {
        'id': 1, 'note_id': 1, 'duration_hours': Decimal('0.75'), 'entry_date': _START.date(),
        'entry_time': _START.time(), 'category': 'meeting', 'project_id': project_id,
        'meeting_id': meeting_id, 'client_id': client_id, 'clockify_id': None,
        'synced_at': None, 'created_at': _START,
    }}
    return 1


def _condensed_notes(store: dict) -> list:
    return [n for n in store.get('notes', {}).values() if n['source'] == 'condensed']


class TestRecordCondensation:
    """record_condensation commits the summary, its note and its entry together or not at all."""

    def test_writes_the_summary_note_and_a_new_entry(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store)

        result = meetings_service.record_condensation(
            fake_uow, meeting_id, "Sentinel summary", ["client-report"],
        )

        assert fake_uow.committed is True
        meeting = fake_uow.store['meetings'][meeting_id]
        assert meeting['condensed_summary'] == "Sentinel summary"
        assert abs(datetime.now() - meeting['condensed_at']) < timedelta(minutes=1)
        note = fake_uow.store['notes'][result.note_id]
        assert (note['content'], note['tags'], note['source'], note['meeting_id']) == (
            "Sentinel summary", ["client-report"], 'condensed', meeting_id,
        )
        entry = fake_uow.store['time_entries'][result.entry_id]
        assert (entry['note_id'], entry['entry_date'], entry['entry_time']) == (
            result.note_id, date(2099, 3, 1), time(9, 0),
        )
        assert result == meetings_service.CondensedEntry(
            note_id=result.note_id, entry_id=result.entry_id,
            duration_hours=Decimal('0.75'), created=True,
        )

    def test_repoints_the_meetings_existing_entry(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store)
        entry_id = _seed_entry(fake_uow.store, meeting_id)

        result = meetings_service.record_condensation(
            fake_uow, meeting_id, "Sentinel summary", ["internal-only"],
        )

        assert (result.entry_id, result.created) == (entry_id, False)
        assert fake_uow.store['time_entries'][entry_id]['note_id'] == result.note_id
        assert len(fake_uow.store['time_entries']) == 1

    def test_a_failed_link_writes_no_summary_and_no_condensed_note(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        meeting_id = _seed_meeting(fake_uow.store)
        entry_id = _seed_entry(fake_uow.store, meeting_id, client_id=2, project_id=5)
        fake_uow.store['projects'] = {5: {'id': 5, 'client_id': 1}}

        with pytest.raises(ValueError, match="mismatched project"):
            meetings_service.record_condensation(
                fake_uow, meeting_id, "Sentinel summary", ["internal-only"],
            )

        assert fake_uow.rolled_back is True
        meeting = fake_uow.store['meetings'][meeting_id]
        assert (meeting['condensed_summary'], meeting['condensed_at']) == (None, None)
        assert _condensed_notes(fake_uow.store) == []
        assert fake_uow.store['time_entries'][entry_id]['note_id'] == 1

    def test_an_invalid_tag_writes_no_summary(self, fake_uow: FakeUnitOfWork) -> None:
        meeting_id = _seed_meeting(fake_uow.store)

        with pytest.raises(InvalidTagsError):
            meetings_service.record_condensation(fake_uow, meeting_id, "Sentinel", ["bogus"])

        assert fake_uow.store['meetings'][meeting_id]['condensed_summary'] is None

    def test_an_unknown_meeting_raises_naming_the_id_and_writes_nothing(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        with pytest.raises(ServiceValidationError, match="99999"):
            meetings_service.record_condensation(fake_uow, 99999, "Sentinel", ["internal-only"])

        assert fake_uow.store.get('notes', {}) == {}

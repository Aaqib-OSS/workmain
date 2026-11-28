"""
clients_service tests — listing, targeting, adding, deleting and the active client context.

Every test runs a use case on fake_uow, its store seeded in
the row shapes tests/mocks/fake_unit_of_work.py's fake repositories state.
"""

from datetime import datetime, timezone

import pytest

from tests.mocks.fake_unit_of_work import FakeUnitOfWork
from workmain.services import clients_service
from workmain.services.exceptions import (
    ActiveClientDeleteError,
    ClientNotFoundError,
    InvalidClientNameError,
)
from workmain.services.results import Page, Summary

CREATED = datetime(2099, 1, 1, 9, 0, tzinfo=timezone.utc)
NOTE_TIME = datetime(2099, 1, 1, 9, 0)


class TestList:
    def test_lists_clients_in_name_order(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Beta', 'is_active': False, 'created_at': CREATED},
            2: {'id': 2, 'name': 'Alpha', 'is_active': True, 'created_at': CREATED},
        }

        page = clients_service.list_clients(fake_uow)

        assert page == Page(
            rows=(
                clients_service.ClientRow(2, 'Alpha', True),
                clients_service.ClientRow(1, 'Beta', False),
            ),
            total=2,
            filters=(),
        )


class TestGet:
    def test_by_id_digit_string(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            7: {'id': 7, 'name': 'Acme', 'is_active': False, 'created_at': CREATED},
        }

        detail = clients_service.get_client(fake_uow, '7')

        assert detail == clients_service.ClientDetail(7, 'Acme', False, CREATED)

    def test_by_name_in_other_case(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            7: {'id': 7, 'name': 'Acme', 'is_active': False, 'created_at': CREATED},
        }

        detail = clients_service.get_client(fake_uow, 'aCME')

        assert detail.client_id == 7

    def test_digit_string_gets_no_suggestions(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme 42', 'is_active': False, 'created_at': CREATED},
        }

        with pytest.raises(ClientNotFoundError) as e:
            clients_service.get_client(fake_uow, '42')

        assert str(e.value) == "Client '42' not found."

    def test_not_found_suggests_substring_matches(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Beta Corp', 'is_active': False, 'created_at': CREATED},
            2: {'id': 2, 'name': 'Alpha Corp', 'is_active': False, 'created_at': CREATED},
            3: {'id': 3, 'name': 'Gamma', 'is_active': False, 'created_at': CREATED},
        }

        with pytest.raises(ClientNotFoundError) as e:
            clients_service.get_client(fake_uow, 'corp')

        assert str(e.value) == (
            "Client 'corp' not found. Did you mean: Alpha Corp (#2), Beta Corp (#1)?"
        )

    def test_not_found_without_matches(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(ClientNotFoundError) as e:
            clients_service.get_client(fake_uow, 'Nobody')

        assert str(e.value) == "Client 'Nobody' not found."


class TestAdd:
    def test_adds_an_inactive_client(self, fake_uow: FakeUnitOfWork) -> None:
        row = clients_service.add_client(fake_uow, 'Acme')

        assert row == clients_service.ClientRow(1, 'Acme', False)
        assert fake_uow.committed is True
        stored = fake_uow.store['clients'][1]
        assert (stored['name'], stored['is_active']) == ('Acme', False)

    def test_reserved_name(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(InvalidClientNameError) as e:
            clients_service.add_client(fake_uow, ' Internal ')

        assert str(e.value) == (
            "'internal' is a reserved keyword and cannot be used as a client name."
        )
        assert fake_uow.store == {}
        assert fake_uow.committed is False

    def test_duplicate_name_in_other_case(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': False, 'created_at': CREATED},
        }

        with pytest.raises(InvalidClientNameError) as e:
            clients_service.add_client(fake_uow, 'aCME')

        assert str(e.value) == "A client named 'aCME' already exists."
        assert list(fake_uow.store['clients']) == [1]
        assert fake_uow.committed is False


class TestDelete:
    def test_preview_states_linked_counts(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': False, 'created_at': CREATED},
        }
        fake_uow.store['meetings'] = {1: {'id': 1, 'title': 'Sync', 'client_id': 1}}
        fake_uow.store['notes'] = {
            note_id: {
                'id': note_id, 'content': 'Note', 'tags': ['internal-only'],
                'created_at': NOTE_TIME, 'meeting_id': None, 'client_id': 1,
            }
            for note_id in (1, 2)
        }
        for table in ('projects', 'report_recipients', 'reports', 'time_entries'):
            fake_uow.store[table] = {1: {'id': 1, 'client_id': 1}}

        preview = clients_service.preview_delete(fake_uow, 'Acme', False)

        assert preview == clients_service.DeletePreview(
            filters=(('client', 'Acme'), ('id', 1)),
            client=clients_service.ClientRow(1, 'Acme', False),
            totals=clients_service.LinkedTotals(
                meetings=1, notes=2, projects=1, report_recipients=1, reports=1,
                time_entries=1,
            ),
            question=(
                "Delete client 'Acme' (ID: 1)? "
                "Its 2 notes, 1 time entries, 1 meetings, 1 reports, 1 projects "
                "and 1 report recipients will lose their client."
            ),
        )

    def test_active_client_without_force(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': True, 'created_at': CREATED},
        }

        with pytest.raises(ActiveClientDeleteError) as e:
            clients_service.preview_delete(fake_uow, 'Acme', False)

        assert str(e.value) == "Client 'Acme' is currently active. Use --force to delete."

    def test_active_client_with_force(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': True, 'created_at': CREATED},
        }

        preview = clients_service.preview_delete(fake_uow, 'Acme', True)

        assert preview.client == clients_service.ClientRow(1, 'Acme', True)

    def test_preview_of_unknown_client(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(ClientNotFoundError) as e:
            clients_service.preview_delete(fake_uow, 'Nobody', True)

        assert str(e.value) == "Client 'Nobody' not found."

    def test_delete_unlinks_linked_rows(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': False, 'created_at': CREATED},
            2: {'id': 2, 'name': 'Other', 'is_active': False, 'created_at': CREATED},
        }
        fake_uow.store['meetings'] = {1: {'id': 1, 'title': 'Sync', 'client_id': 1}}
        fake_uow.store['notes'] = {
            note_id: {
                'id': note_id, 'content': 'Note', 'tags': ['internal-only'],
                'created_at': NOTE_TIME, 'meeting_id': None, 'client_id': owner,
            }
            for note_id, owner in ((1, 1), (2, 2))
        }
        for table in ('projects', 'report_recipients', 'reports', 'time_entries'):
            fake_uow.store[table] = {1: {'id': 1, 'client_id': 1}}

        row = clients_service.delete_client(fake_uow, 1)

        assert row == clients_service.ClientRow(1, 'Acme', False)
        assert fake_uow.committed is True
        assert list(fake_uow.store['clients']) == [2]
        for table in ('meetings', 'projects', 'report_recipients', 'reports', 'time_entries'):
            assert fake_uow.store[table][1]['client_id'] is None, table
        assert fake_uow.store['notes'][1]['client_id'] is None
        assert fake_uow.store['notes'][2]['client_id'] == 2

    def test_deleting_the_active_client_clears_the_context(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': True, 'created_at': CREATED},
        }

        clients_service.delete_client(fake_uow, 1)

        assert fake_uow.committed is True
        assert fake_uow.store['clients'] == {}
        status = clients_service.get_status(FakeUnitOfWork(store=fake_uow.store))
        assert status.totals == clients_service.ClientStatusTotals('internal', None)

    def test_delete_of_unknown_id(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(ClientNotFoundError) as e:
            clients_service.delete_client(fake_uow, 99)

        assert str(e.value) == "Client '99' not found."


class TestActive:
    def test_sets_the_active_client_by_name(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': False, 'created_at': CREATED},
        }

        status = clients_service.set_active(fake_uow, 'aCME')

        assert status == Summary(clients_service.ClientStatusTotals('Acme', 1), ())
        assert fake_uow.committed is True
        assert fake_uow.store['clients'][1]['is_active'] is True

    @pytest.mark.parametrize('name', ['internal', 'INTERNAL', ' Internal '])
    def test_internal_clears_the_context(self, fake_uow: FakeUnitOfWork, name: str) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': True, 'created_at': CREATED},
        }

        status = clients_service.set_active(fake_uow, name)

        assert status.totals == clients_service.ClientStatusTotals('internal', None)
        assert fake_uow.committed is True
        assert fake_uow.store['clients'][1]['is_active'] is False

    def test_unknown_name_leaves_the_active_client(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Alpha', 'is_active': True, 'created_at': CREATED},
        }

        with pytest.raises(ClientNotFoundError) as e:
            clients_service.set_active(fake_uow, 'alp')

        assert str(e.value) == "Client 'alp' not found. Did you mean: Alpha (#1)?"
        assert fake_uow.committed is False
        status = clients_service.get_status(FakeUnitOfWork(store=fake_uow.store))
        assert status.totals == clients_service.ClientStatusTotals('Alpha', 1)


class TestStatus:
    def test_reports_the_active_client(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': True, 'created_at': CREATED},
        }

        status = clients_service.get_status(fake_uow)

        assert status == Summary(clients_service.ClientStatusTotals('Acme', 1), ())

    def test_internal_when_nothing_is_active_and_formatters(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        fake_uow.store['clients'] = {
            1: {'id': 1, 'name': 'Acme', 'is_active': False, 'created_at': CREATED},
        }

        status = clients_service.get_status(fake_uow)

        assert status.totals == clients_service.ClientStatusTotals('internal', None)
        assert clients_service.format_active_marker(True) == '●'
        assert clients_service.format_active_marker(False) == ''
        assert clients_service.format_yes_no(True) == 'Yes'
        assert clients_service.format_yes_no(False) == 'No'

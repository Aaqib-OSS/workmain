"""
Command tests for the clients group.

Each path through a command runs end to end through CliRunner against the test's database, with the recording
renderer. Rows are seeded through db_session, and rows a path writes or
leaves alone are read back by a query after db_session.expunge_all().
"""

from unittest.mock import NonCallableMagicMock, patch

import click
from click.testing import CliRunner
from sqlalchemy.orm import Session

from workmain.cli.commands import clients as clients_module
from workmain.cli.commands.clients import (
    CLIENT_CHANGE,
    CLIENT_LIST,
    CLIENT_RECORD,
    DELETE_PREVIEW,
    STATUS,
    clients,
)
from workmain.cli.output import WorkmAInGroup
from workmain.database.models import Client, Note
from workmain.database.repositories.client_repository import ClientRepository
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services import clients_service
from workmain.services.results import Summary


class TestClientsCommands:
    def test_c1_group_is_a_workmain_group(self) -> None:
        assert isinstance(clients, WorkmAInGroup)

    def test_add(self, db_session: Session, recording_renderer: NonCallableMagicMock) -> None:
        result = CliRunner(mix_stderr=False).invoke(
            clients, ['add', 'ZqvAcme'], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        db_session.expunge_all()
        client = db_session.query(Client).filter(Client.name == 'ZqvAcme').one()
        assert client.is_active is False
        recording_renderer.changed.assert_called_once_with(
            CLIENT_CHANGE, clients_service.ClientRow(client.id, 'ZqvAcme', False), 'Created',
        )

    def test_list(self, db_session: Session, recording_renderer: NonCallableMagicMock) -> None:
        repo = ClientRepository(db_session)
        beta = repo.create('ZqvBeta')
        alpha = repo.create('ZqvAlpha')

        result = CliRunner(mix_stderr=False).invoke(clients, ['list'], obj=recording_renderer)

        assert result.exit_code == 0, result.stderr
        recording_renderer.collection.assert_called_once()
        view, page = recording_renderer.collection.call_args.args
        assert view is CLIENT_LIST
        assert [row for row in page.rows if row.name.startswith('Zqv')] == [
            clients_service.ClientRow(alpha.id, 'ZqvAlpha', False),
            clients_service.ClientRow(beta.id, 'ZqvBeta', False),
        ]
        assert (page.total, page.filters) == (len(page.rows), ())
        db_session.expunge_all()
        assert db_session.query(Client).filter(Client.name.like('Zqv%')).count() == 2

    def test_show(self, db_session: Session, recording_renderer: NonCallableMagicMock) -> None:
        client = ClientRepository(db_session).create('ZqvAcme')

        result = CliRunner(mix_stderr=False).invoke(
            clients, ['show', 'zqvACME'], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.record.assert_called_once_with(
            CLIENT_RECORD,
            clients_service.ClientDetail(client.id, 'ZqvAcme', False, client.created_at),
        )
        db_session.expunge_all()
        assert db_session.query(Client).filter(Client.id == client.id).one().name == 'ZqvAcme'

    def test_status(self, db_session: Session, recording_renderer: NonCallableMagicMock) -> None:
        repo = ClientRepository(db_session)
        client = repo.create('ZqvAcme')
        repo.set_active(client.id)

        result = CliRunner(mix_stderr=False).invoke(clients, ['status'], obj=recording_renderer)

        assert result.exit_code == 0, result.stderr
        recording_renderer.report.assert_called_once_with(
            STATUS, Summary(clients_service.ClientStatusTotals('ZqvAcme', client.id)),
        )
        db_session.expunge_all()
        assert db_session.query(Client).filter(Client.id == client.id).one().is_active is True

    def test_set_active(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        repo = ClientRepository(db_session)
        repo.clear_active()
        client = repo.create('ZqvAcme')

        result = CliRunner(mix_stderr=False).invoke(
            clients, ['set', 'active', 'zqvacme'], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.report.assert_called_once_with(
            STATUS, Summary(clients_service.ClientStatusTotals('ZqvAcme', client.id)),
        )
        db_session.expunge_all()
        assert db_session.query(Client).filter(Client.id == client.id).one().is_active is True
        assert SystemStateRepository(db_session).get_int('active_client_id') == client.id

    def test_delete_answered_yes_deletes_and_unlinks(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        client = ClientRepository(db_session).create('ZqvAcme')
        note = NotesRepository(db_session).create(
            content='ZqvNote', tags=['internal-only'], client_id=client.id,
        )

        result = CliRunner(mix_stderr=False).invoke(
            clients, ['delete', 'ZqvAcme'], obj=recording_renderer, input='y\n',
        )

        assert result.exit_code == 0, result.stderr
        question = (
            f"Delete client 'ZqvAcme' (ID: {client.id})? "
            "Its 1 notes, 0 time entries, 0 meetings, 0 reports, 0 projects "
            "and 0 report recipients will lose their client."
        )
        row = clients_service.ClientRow(client.id, 'ZqvAcme', False)
        recording_renderer.report.assert_called_once_with(
            DELETE_PREVIEW,
            clients_service.DeletePreview(
                filters=(('client', 'ZqvAcme'), ('id', client.id)),
                client=row,
                totals=clients_service.LinkedTotals(
                    meetings=0, notes=1, projects=0, report_recipients=0, reports=0,
                    time_entries=0,
                ),
                question=question,
            ),
        )
        recording_renderer.changed.assert_called_once_with(CLIENT_CHANGE, row, 'Deleted')
        recording_renderer.cancelled.assert_not_called()
        db_session.expunge_all()
        assert db_session.query(Client).filter(Client.id == client.id).one_or_none() is None
        assert db_session.query(Note).filter(Note.id == note.id).one().client_id is None

    def test_delete_answered_no_keeps_the_client(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        client = ClientRepository(db_session).create('ZqvAcme')

        result = CliRunner(mix_stderr=False).invoke(
            clients, ['delete', 'ZqvAcme'], obj=recording_renderer, input='n\n',
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.report.assert_called_once()
        recording_renderer.cancelled.assert_called_once_with()
        recording_renderer.changed.assert_not_called()
        db_session.expunge_all()
        assert db_session.query(Client).filter(Client.id == client.id).one().name == 'ZqvAcme'

    def test_delete_aborted_prompt_exits_1_and_keeps_the_client(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        client = ClientRepository(db_session).create('ZqvAcme')

        with patch.object(clients_module.click, 'confirm', side_effect=click.Abort()):
            result = CliRunner(mix_stderr=False).invoke(
                clients, ['delete', 'ZqvAcme'], obj=recording_renderer,
            )

        assert result.exit_code == 1
        recording_renderer.report.assert_called_once()
        recording_renderer.cancelled.assert_not_called()
        recording_renderer.changed.assert_not_called()
        db_session.expunge_all()
        assert db_session.query(Client).filter(Client.id == client.id).one().name == 'ZqvAcme'

    def test_delete_with_force_deletes_the_active_client_without_asking(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        repo = ClientRepository(db_session)
        client = repo.create('ZqvAcme')
        repo.set_active(client.id)

        result = CliRunner(mix_stderr=False).invoke(
            clients, ['delete', 'ZqvAcme', '--force'], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.report.assert_called_once()
        recording_renderer.changed.assert_called_once_with(
            CLIENT_CHANGE, clients_service.ClientRow(client.id, 'ZqvAcme', True), 'Deleted',
        )
        db_session.expunge_all()
        assert db_session.query(Client).filter(Client.id == client.id).one_or_none() is None
        assert SystemStateRepository(db_session).get_int('active_client_id') is None

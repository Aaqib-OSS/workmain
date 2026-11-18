"""
CLI command group for client records and the active client context.

Manages the clients that notes, time entries and reports are attributed to.
The active client drives that attribution; with none active, work is internal.
"""

import click

from workmain.cli.output import (
    CollectionView,
    Column,
    Field,
    RecordView,
    ReportView,
    WorkmAInGroup,
    pass_renderer,
)
from workmain.services import clients_service
from workmain.services.unit_of_work import UnitOfWork

CLIENT_LIST = CollectionView(
    "clients",
    (
        Column("client_id", "ID", "key"),
        Column("name", "Name", "text"),
        Column("is_active", "Active", "key", fmt=clients_service.format_active_marker),
    ),
    empty_hint="Add a client with: workmain clients add <name>",
)

CLIENT_RECORD = RecordView(
    "Client",
    "client_id",
    "name",
    (
        Field("is_active", "Active", fmt=clients_service.format_yes_no),
        Field("created_at", "Created"),
    ),
)

CLIENT_CHANGE = RecordView("Client", "client_id", "name", (), body_field="name")

DELETE_PREVIEW = ReportView(
    "client delete",
    "totals",
    (
        Field("notes", "Notes"),
        Field("time_entries", "Time entries"),
        Field("meetings", "Meetings"),
        Field("reports", "Reports"),
        Field("projects", "Projects"),
        Field("report_recipients", "Report recipients"),
    ),
    (),
    totals_when_empty=True,
)

STATUS = ReportView(
    "client context",
    "totals",
    (
        Field("client", "Active client"),
        Field("client_id", "ID"),
    ),
    (),
    totals_when_empty=True,
)


# ---------------------------------------------------------------------------
# clients group
# ---------------------------------------------------------------------------

@click.group(cls=WorkmAInGroup)
def clients():
    """Client management and context switching."""


# ---------------------------------------------------------------------------
# clients add
# ---------------------------------------------------------------------------

@clients.command('add')
@click.argument('name')
@pass_renderer
def clients_add(renderer, name: str):
    """Create a new client.

    \b
    Examples:
      workmain clients add "Acme Corp"
      workmain clients add ACME
    """
    row = clients_service.add_client(UnitOfWork(), name)
    renderer.changed(CLIENT_CHANGE, row, "Created")


# ---------------------------------------------------------------------------
# clients list
# ---------------------------------------------------------------------------

@clients.command('list')
@pass_renderer
def clients_list(renderer):
    """List all configured clients.

    \b
    Examples:
      workmain clients list
    """
    page = clients_service.list_clients(UnitOfWork())
    renderer.collection(CLIENT_LIST, page)


# ---------------------------------------------------------------------------
# clients show
# ---------------------------------------------------------------------------

@clients.command('show')
@click.argument('id_or_name')
@pass_renderer
def clients_show(renderer, id_or_name: str):
    """Show detail for a client.

    ID_OR_NAME can be the numeric ID or the client name.

    \b
    Examples:
      workmain clients show ACME
      workmain clients show 1
    """
    detail = clients_service.get_client(UnitOfWork(), id_or_name)
    renderer.record(CLIENT_RECORD, detail)


# ---------------------------------------------------------------------------
# clients delete
# ---------------------------------------------------------------------------

@clients.command('delete')
@click.argument('id_or_name')
@click.option('--force', is_flag=True, default=False,
              help='Skip confirmation prompt. Required if client is currently active.')
@pass_renderer
def clients_delete(renderer, id_or_name: str, force: bool):
    """Delete a client.

    ID_OR_NAME can be the numeric ID or the client name.
    Use --force if the client is currently active.

    \b
    Examples:
      workmain clients delete "Acme Corp"
      workmain clients delete 2 --force
    """
    preview = clients_service.preview_delete(UnitOfWork(), id_or_name, force)
    renderer.report(DELETE_PREVIEW, preview)
    if not force and not click.confirm(preview.question, default=False):
        renderer.cancelled()
        return
    row = clients_service.delete_client(UnitOfWork(), preview.client.client_id)
    renderer.changed(CLIENT_CHANGE, row, "Deleted")


# ---------------------------------------------------------------------------
# clients set (subgroup) → active
# ---------------------------------------------------------------------------

@clients.group('set')
def clients_set():
    """Configure client context."""


@clients_set.command('active')
@click.argument('name')
@pass_renderer
def clients_set_active(renderer, name: str):
    """Set the active client context.

    NAME is a client name or the reserved word 'internal' to clear context.
    Accepts name only (not ID)

    \b
    Examples:
      workmain clients set active ACME
      workmain clients set active internal
    """
    status = clients_service.set_active(UnitOfWork(), name)
    renderer.report(STATUS, status)


# ---------------------------------------------------------------------------
# clients status
# ---------------------------------------------------------------------------

@clients.command('status')
@pass_renderer
def clients_status(renderer):
    """Show current active client context.

    \b
    Examples:
      workmain clients status
    """
    status = clients_service.get_status(UnitOfWork())
    renderer.report(STATUS, status)


__all__ = ['clients']

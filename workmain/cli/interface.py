"""
Main CLI interface using the Click framework.
"""

import logging
import os
import sys

import click

# Import version
try:
    from workmain.__version__ import __version__
except ImportError:
    __version__ = "1.1.0"

# Import Phase 2 commands
# Import Phase 6 commands
from workmain.cli.commands.calendar import calendar
from workmain.cli.commands.clients import clients

# Import Phase 5 commands
from workmain.cli.commands.clockify import clockify
from workmain.cli.commands.email import email

# Import Sprint commands
from workmain.cli.commands.eod import eod

# Import Phase 7 commands
from workmain.cli.commands.gdocs import gdocs
from workmain.cli.commands.meetings import meetings
from workmain.cli.commands.notes import notes
from workmain.cli.commands.notifications import notifications
from workmain.cli.commands.providers import providers

# Import Phase 4 commands
from workmain.cli.commands.reports import reports

# Phase 10: Notification & Scheduling
from workmain.cli.commands.schedule import schedule

# Import Phase 8 commands
from workmain.cli.commands.slack import slack
from workmain.cli.commands.tasks import tasks

# Import Phase 3 commands
from workmain.cli.commands.templates import templates
from workmain.cli.commands.time import time
from workmain.cli.output import Renderer, WorkmAInGroup


def _configure_cli_logging() -> None:
    """Route log records to stdout, so stderr carries only a command's own lines.

    The daemon does the same for the systemd journal. In an EOD child, stdout
    is captured and echoed to the daemon's journal.

    Python warnings are captured into the log too, so a library warning never
    reaches stderr, which a calling process reads as the command's own warning
    (docs/standards/5-cli.md §5.6).

    The level is the environment variable LOG_LEVEL. Unset, empty, unknown and
    NOTSET all give WARNING, so a bad value never stops a command and NOTSET
    never lets every record through to the stdout a caller captures.
    """
    level = logging.getLevelNamesMapping().get(
        os.environ.get('LOG_LEVEL', '').strip().upper()
    )
    if not level:
        level = logging.WARNING
    logging.captureWarnings(True)
    logging.basicConfig(
        level=level,
        format='%(name)s %(levelname)s %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@click.group(cls=WorkmAInGroup)
@click.version_option(version=__version__, prog_name="workmain")
@click.pass_context
def cli(ctx):
    """
    WorkmAIn - Work Management AI
    
    An intelligent personal work management system for capturing notes,
    tracking time, and generating AI-powered reports.
    
    Use 'workmain COMMAND --help' for more information on a specific command.
    """
    _configure_cli_logging()
    ctx.ensure_object(Renderer)


# Phase 2: Note and Meeting Commands
cli.add_command(clients)
cli.add_command(notes)
cli.add_command(meetings)

# Phase 2: Time Tracking Commands
cli.add_command(time)

# Phase 2: Task Management Commands
cli.add_command(tasks)

# Phase 3: Template Management Commands
cli.add_command(templates)

# Phase 4: AI Report Generation (REAL IMPLEMENTATION)
cli.add_command(reports)

# Phase 4: AI Provider Management (Feature 2)
cli.add_command(providers)

# Phase 5: Clockify Integration
cli.add_command(clockify)

# Phase 6: Outlook Integration
cli.add_command(calendar)
cli.add_command(email)

# Phase 7: Google Drive Integration
cli.add_command(gdocs)

# Phase 8: Slack Integration
cli.add_command(slack)

# Standardization Sprint
cli.add_command(eod)

# Phase 10: Notification & Scheduling
cli.add_command(schedule)
cli.add_command(notifications)


# Placeholder command groups deferred; tracked in GitHub Issues
# (config, provider, clients, recipients, notifications)


if __name__ == "__main__":
    cli()
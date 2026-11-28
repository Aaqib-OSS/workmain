"""
Store the active client as clients.is_active alone.

Moves the active client from the system_state key active_client_id into
clients.is_active and deletes the key. Replaces idx_clients_is_active with
uq_clients_one_active, a unique partial index that admits one flagged row,
and rewrites the clients and system_state table comments to match.

The upgrade first checks the two stores. When the key names one client and
another is flagged, it raises and moves nothing, and the upgrade's one
transaction leaves the database at 0001. The downgrade writes the key back
from the flag, so it reverses rather than raises.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision: str = '0002'
down_revision: str | None = '0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_KEY = 'active_client_id'

_CLIENTS_COMMENT = (
    'Client records. is_active=TRUE identifies the active client, and the unique '
    'partial index uq_clients_one_active allows one such row. NULL client_id on data '
    'records = internal/company work. The reserved keyword internal on clients set '
    'active clears context. A client named internal cannot be created (CHECK '
    'constraint + functional unique index on lower(name)).'
)
_CLIENTS_COMMENT_0001 = (
    'Client records. is_active=TRUE identifies the active client. Only one row may '
    'have is_active=TRUE at a time (repository-enforced). NULL client_id on data '
    'records = internal/company work. The reserved keyword internal on clients set '
    'active clears context. A client named internal cannot be created (CHECK '
    'constraint + functional unique index on lower(name)).'
)
_SYSTEM_STATE_COMMENT = (
    'General-purpose KV store for WorkmAIn runtime state. String values only — '
    'repository layer handles type casting. Keys: notify_method, notify_enabled.'
)
_SYSTEM_STATE_COMMENT_0001 = (
    'General-purpose KV store for WorkmAIn runtime state. String values only — '
    'repository layer handles type casting. Keys: notify_method, notify_enabled, '
    'active_client_id.'
)


def _parse_key(value: str | None) -> int | None:
    """
    Read the key's value as SystemStateRepository.get_int reads it.

    Args:
        value: The stored value, or None when the key is absent

    Returns:
        The client id, or None when the value is absent or does not parse
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def move_key_to_flag(connection: Connection) -> None:
    """
    Move the active client from the system_state key into clients.is_active.

    A key that parses is set; an absent or unparseable one is unset. When the
    key is set, the client it names is flagged if it exists, and every other
    client is unflagged. When it is unset, every client is unflagged. The key
    is deleted in every case. Every flagged row is unflagged in one statement
    before the target is flagged in another, so the unique index never sees
    two flagged rows.

    Args:
        connection: The connection the revision runs on

    Raises:
        RuntimeError: If the key is set and a client other than the one it
            names is flagged. Nothing is changed.
    """
    raw = connection.execute(
        sa.text('SELECT value FROM system_state WHERE key = :key'), {'key': _KEY}
    ).scalar_one_or_none()
    client_id = _parse_key(raw)
    flagged = connection.execute(
        sa.text('SELECT id, name FROM clients WHERE is_active ORDER BY id')
    ).all()

    if client_id is not None and any(row.id != client_id for row in flagged):
        listed = ', '.join(f'{row.id} ({row.name})' for row in flagged)
        raise RuntimeError(
            f"system_state.{_KEY} is {raw!r}, but the flagged clients are {listed}. "
            "Settle which client is active, then run the upgrade again."
        )

    connection.execute(sa.text('UPDATE clients SET is_active = false WHERE is_active'))
    if client_id is not None:
        connection.execute(
            sa.text('UPDATE clients SET is_active = true WHERE id = :id'), {'id': client_id}
        )
    connection.execute(sa.text('DELETE FROM system_state WHERE key = :key'), {'key': _KEY})


def move_flag_to_key(connection: Connection) -> None:
    """
    Write the system_state key from the flagged client.

    Writes no key when no client is flagged.

    Args:
        connection: The connection the revision runs on
    """
    client_id = connection.execute(
        sa.text('SELECT id FROM clients WHERE is_active ORDER BY id')
    ).scalars().first()
    if client_id is None:
        return
    connection.execute(
        sa.text(
            'INSERT INTO system_state (key, value, updated_at) VALUES (:key, :value, now()) '
            'ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()'
        ),
        {'key': _KEY, 'value': str(client_id)},
    )


def upgrade() -> None:
    """
    Move the key into the flag, hold the flag to one row, and restate the comments.
    """
    move_key_to_flag(op.get_bind())
    op.drop_index('idx_clients_is_active', table_name='clients')
    op.create_index(
        'uq_clients_one_active', 'clients', ['is_active'],
        unique=True, postgresql_where=sa.text('is_active'),
    )
    op.create_table_comment(
        'clients', _CLIENTS_COMMENT, existing_comment=_CLIENTS_COMMENT_0001
    )
    op.create_table_comment(
        'system_state', _SYSTEM_STATE_COMMENT, existing_comment=_SYSTEM_STATE_COMMENT_0001
    )


def downgrade() -> None:
    """
    Restore the baseline's index, the key from the flag, and the baseline's comments.
    """
    op.drop_index('uq_clients_one_active', table_name='clients')
    op.create_index(
        'idx_clients_is_active', 'clients', ['is_active'],
        postgresql_where=sa.text('is_active = true'),
    )
    move_flag_to_key(op.get_bind())
    op.create_table_comment(
        'clients', _CLIENTS_COMMENT_0001, existing_comment=_CLIENTS_COMMENT
    )
    op.create_table_comment(
        'system_state', _SYSTEM_STATE_COMMENT_0001, existing_comment=_SYSTEM_STATE_COMMENT
    )

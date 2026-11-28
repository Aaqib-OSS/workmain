"""
Tests for revision 0002's data moves between system_state.active_client_id and clients.is_active.

move_key_to_flag and move_flag_to_key are called on db_session's connection,
so each test seeds, moves and reads inside its own transaction. The test
database is already at 0002, whose unique index admits one flagged client, so
no test seeds two.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from workmain.database.models import Client
from workmain.database.repositories.system_state_repository import SystemStateRepository

_REVISION = (
    Path(__file__).resolve().parent.parent
    / 'workmain' / 'database' / 'migrations' / 'versions' / '0002_active_client_flag.py'
)


def _load_revision() -> ModuleType:
    """The revision module, loaded by path: its file name is not an identifier."""
    spec = importlib.util.spec_from_file_location('revision_0002_active_client_flag', _REVISION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


revision = _load_revision()

_NAME_A = 'ZqvRevisionClientA'
_NAME_B = 'ZqvRevisionClientB'
_KEY = 'active_client_id'


def _client(session: Session, name: str, is_active: bool = False) -> int:
    client = Client(name=name, is_active=is_active)
    session.add(client)
    session.flush()
    return client.id


def _set_key(session: Session, value: str) -> None:
    SystemStateRepository(session).set(_KEY, value)
    session.flush()


def _flagged(session: Session) -> list[int]:
    return list(session.execute(text('SELECT id FROM clients WHERE is_active ORDER BY id')).scalars())


def _key(session: Session) -> str | None:
    return session.execute(
        text('SELECT value FROM system_state WHERE key = :key'), {'key': _KEY}
    ).scalar_one_or_none()


def _key_present(session: Session) -> bool:
    return session.execute(
        text('SELECT count(*) FROM system_state WHERE key = :key'), {'key': _KEY}
    ).scalar_one() == 1


class TestMoveKeyToFlag:
    def test_key_naming_one_client_while_another_is_flagged_raises_and_changes_nothing(
        self, db_session: Session
    ) -> None:
        a = _client(db_session, _NAME_A)
        b = _client(db_session, _NAME_B, is_active=True)
        _set_key(db_session, str(a))

        with pytest.raises(RuntimeError) as e:
            revision.move_key_to_flag(db_session.connection())

        assert repr(str(a)) in str(e.value)
        assert f'{b} ({_NAME_B})' in str(e.value)
        assert _flagged(db_session) == [b]
        assert _key(db_session) == str(a)

    def test_key_naming_no_client_while_a_client_is_flagged_raises_and_changes_nothing(
        self, db_session: Session
    ) -> None:
        b = _client(db_session, _NAME_B, is_active=True)
        _set_key(db_session, '99999999')

        with pytest.raises(RuntimeError) as e:
            revision.move_key_to_flag(db_session.connection())

        assert "'99999999'" in str(e.value)
        assert f'{b} ({_NAME_B})' in str(e.value)
        assert _flagged(db_session) == [b]
        assert _key(db_session) == '99999999'

    def test_key_naming_an_existing_client_with_nothing_flagged_flags_it(self, db_session: Session) -> None:
        a = _client(db_session, _NAME_A)
        _client(db_session, _NAME_B)
        _set_key(db_session, str(a))

        revision.move_key_to_flag(db_session.connection())

        assert _flagged(db_session) == [a]
        assert not _key_present(db_session)

    def test_key_naming_the_flagged_client_keeps_it_flagged(self, db_session: Session) -> None:
        a = _client(db_session, _NAME_A, is_active=True)
        _client(db_session, _NAME_B)
        _set_key(db_session, str(a))

        revision.move_key_to_flag(db_session.connection())

        assert _flagged(db_session) == [a]
        assert not _key_present(db_session)

    def test_key_naming_no_client_with_nothing_flagged_flags_nothing(self, db_session: Session) -> None:
        _client(db_session, _NAME_A)
        _set_key(db_session, '99999999')

        revision.move_key_to_flag(db_session.connection())

        assert _flagged(db_session) == []
        assert not _key_present(db_session)

    def test_absent_key_unflags_the_flagged_client(self, db_session: Session) -> None:
        _client(db_session, _NAME_A, is_active=True)

        revision.move_key_to_flag(db_session.connection())

        assert _flagged(db_session) == []
        assert not _key_present(db_session)

    def test_unparseable_key_unflags_the_flagged_client_and_is_deleted(self, db_session: Session) -> None:
        _client(db_session, _NAME_A, is_active=True)
        _set_key(db_session, 'not-a-number')

        revision.move_key_to_flag(db_session.connection())

        assert _flagged(db_session) == []
        assert not _key_present(db_session)


class TestMoveFlagToKey:
    def test_writes_the_flagged_clients_id(self, db_session: Session) -> None:
        _client(db_session, _NAME_A)
        b = _client(db_session, _NAME_B, is_active=True)

        revision.move_flag_to_key(db_session.connection())

        assert _key(db_session) == str(b)

    def test_writes_no_key_when_no_client_is_flagged(self, db_session: Session) -> None:
        _client(db_session, _NAME_A)

        revision.move_flag_to_key(db_session.connection())

        assert not _key_present(db_session)

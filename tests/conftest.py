"""
Pytest fixtures shared across all test files.
"""

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

if TYPE_CHECKING:
    from tests.mocks.fake_unit_of_work import FakeUnitOfWork

TEST_DB_NAME = "workmain_test"

_REPO_ROOT = Path(__file__).resolve().parent.parent


def pytest_configure(config: pytest.Config) -> None:
    """
    Point the run at the test database before anything imports workmain.

    workmain.database.connection fixes the database name when it is first
    imported, and load_dotenv() never overrides a variable already set, so
    setting DB_NAME here keeps .env's name out of the run. .env is not read.

    Args:
        config: The pytest configuration.
    """
    value = os.environ.get("DB_NAME")
    if value is None:
        os.environ["DB_NAME"] = TEST_DB_NAME
    elif value != TEST_DB_NAME:
        pytest.exit(
            f"Tests run only on {TEST_DB_NAME}; DB_NAME is set to '{value}'.",
            returncode=4,
        )


def require_test_database(url: str) -> None:
    """
    Stop the run unless the URL names the test database.

    Catches a connection resolved before pytest_configure set DB_NAME.

    Args:
        url: The database URL the run would connect through.
    """
    from sqlalchemy.engine import make_url

    name = make_url(url).database
    if name != TEST_DB_NAME:
        pytest.exit(
            f"Tests run only on {TEST_DB_NAME}; the connection names '{name}'.",
            returncode=4,
        )


def _stop_build(url: str, detail: str) -> None:
    """Stop the run because the test database could not be built."""
    from sqlalchemy.engine import make_url

    message = f"Could not build {TEST_DB_NAME}: {detail.strip()}"
    if f'database "{TEST_DB_NAME}" does not exist' in detail:
        message += (
            f"\n{TEST_DB_NAME} is created once by the database server's "
            f"administrator, owned by {make_url(url).username}."
        )
    pytest.exit(message, returncode=4)


def build_test_database() -> None:
    """
    Empty the test database and build its schema with Alembic.

    Every object the application's user owns is dropped, which leaves the
    public schema as initdb made it. The schema is then built by
    `alembic upgrade head` in a child process: running a revision runs
    env.py, whose logging setup would disable this process's loggers.
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.pool import NullPool

    from workmain.database.connection import get_db

    url = get_db().url
    require_test_database(url)

    engine = create_engine(url, poolclass=NullPool)
    try:
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL lock_timeout = '10s'"))
            connection.execute(text("DROP OWNED BY CURRENT_USER"))
    except SQLAlchemyError as exc:
        _stop_build(url, str(exc))
    finally:
        engine.dispose()

    upgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if upgrade.returncode != 0:
        _stop_build(url, f"alembic upgrade head exited {upgrade.returncode}\n{upgrade.stderr}")


@pytest.fixture(scope="session")
def _test_database() -> None:
    """
    Build the test database once, before the run's first test.

    Every object the application's user owns in workmain_test is dropped, and
    the schema is built again by `alembic upgrade head` in a child process.
    pytest_configure has already pointed DB_NAME at workmain_test, and the run
    stops before the first test when DB_NAME names another database.
    workmain_test is created once by the database server's administrator,
    owned by the application's user.
    """
    build_test_database()


@pytest.fixture(autouse=True)
def _isolated_database(monkeypatch: pytest.MonkeyPatch, _test_database: None) -> Iterator[None]:
    """
    Run every test inside one database transaction, rolled back at teardown.

    The application's session factory is bound to a connection this fixture
    owns, inside a transaction it began, with
    join_transaction_mode="create_savepoint". Every session opened through
    get_db() joins that transaction: commit() releases a savepoint and
    rollback() returns to one, so all sessions in a test see each other's
    writes, and the rollback at teardown discards them all. A run killed
    mid-test leaves the transaction open, and PostgreSQL rolls it back when
    the connection drops.

    Sessions on this one connection finish last-in, first-out: an object a
    test builds on db_session and hands to code that opens its own session
    fails at that code's commit.

    DatabaseConnection.close() raises during a test, and a test that replaces
    the session factory fails at teardown, because either would move the
    test's code to a connection outside this transaction.
    """
    load_dotenv()

    from sqlalchemy.orm import sessionmaker

    from workmain.database.connection import DatabaseConnection, get_db

    db = get_db()
    engine = db.connect()
    live_factory = db.SessionLocal
    connection = engine.connect()
    outer = connection.begin()
    test_factory = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    db.SessionLocal = test_factory

    def _refuse_close(self):
        raise RuntimeError(
            "DatabaseConnection.close() during a test would reconnect outside "
            "the test's transaction"
        )

    monkeypatch.setattr(DatabaseConnection, 'close', _refuse_close)

    try:
        yield
    finally:
        replaced = db.SessionLocal is not test_factory
        db.SessionLocal = live_factory
        outer.rollback()
        connection.close()
        assert not replaced, "the test replaced the session factory"


@pytest.fixture
def db_session():
    """
    A session for the test's own seeding and reads.

    It comes from the same factory application code uses, so the test and the
    code it calls share one transaction and see each other's writes. Commit
    it freely; every write rolls back with the test.

    Its identity map keeps every object it has loaded: until db_session
    commits, rolls back or expire_all() is called, get() and attribute
    access return those objects as they were when loaded, and a query after
    expunge_all() reads the rows as they are now.
    """
    from workmain.database.connection import get_db

    session = get_db().get_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_uow() -> "FakeUnitOfWork":
    """
    A FakeUnitOfWork over a fresh, empty store, for a service test.

    A second unit of work over the same rows is
    FakeUnitOfWork(store=fake_uow.store).
    """
    from tests.mocks.fake_unit_of_work import FakeUnitOfWork

    return FakeUnitOfWork()


@pytest.fixture
def offline_provider_env():
    """Fake keys for both vendors with both vendor clients patched out."""
    env = {
        "ANTHROPIC_API_KEY": "sk-ant-test000000000000000000000000000000000000",
        "GOOGLE_API_KEY": "A" * 39,
    }
    with patch.dict(os.environ, env), \
         patch("workmain.ai.providers.claude.Anthropic"), \
         patch("workmain.ai.providers.gemini.genai.Client"):
        yield

"""
Tests for the scope state and the unit of work.

The scope state records whether a session_scope() is open on the calling
thread. These tests open bare scopes through get_db(), because the state
exists for callers that still hold one.
"""

import threading

import pytest

from workmain.database.connection import get_db, scope_open


class TestScopeState:
    """scope_open() is true exactly while a session_scope() is open on its thread."""

    def test_true_inside_session_scope(self) -> None:
        with get_db().session_scope():
            assert scope_open() is True

    def test_true_inside_record_scope(self) -> None:
        with get_db().record_scope():
            assert scope_open() is True

    def test_false_before_and_after(self) -> None:
        assert scope_open() is False
        with get_db().session_scope():
            pass
        assert scope_open() is False

    def test_nested_scope_restores_true(self) -> None:
        with get_db().session_scope():
            with get_db().session_scope():
                pass
            assert scope_open() is True
        assert scope_open() is False

    def test_false_after_exception(self) -> None:
        with pytest.raises(ValueError):
            with get_db().session_scope():
                raise ValueError("leave the scope")
        assert scope_open() is False

    def test_false_after_keyboard_interrupt(self) -> None:
        with pytest.raises(KeyboardInterrupt):
            with get_db().session_scope():
                raise KeyboardInterrupt
        assert scope_open() is False

    def test_false_on_another_thread(self) -> None:
        seen = []
        with get_db().session_scope():
            thread = threading.Thread(target=lambda: seen.append(scope_open()))
            thread.start()
            thread.join()
            assert scope_open() is True
        assert seen == [False]

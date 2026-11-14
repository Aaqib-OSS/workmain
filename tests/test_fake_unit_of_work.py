"""
Tests for the fake unit of work and the fake system-state repository.

The fake must stand in for the real unit of work in a service test: keep
rows in memory, commit and roll back as the real one does, refuse the same
nesting, and answer every faked repository method as the SQL does.
"""

import copy
import inspect
import re

import pytest
from sqlalchemy.orm import Session

from tests.mocks.fake_unit_of_work import FakeSystemStateRepository, FakeUnitOfWork
from workmain.database.repositories.system_state_repository import SystemStateRepository
from workmain.services.unit_of_work import (
    _OPEN_SCOPE_MESSAGE,
    _REENTRY_MESSAGE,
    UnitOfWork,
)

_REENTRY = re.escape(_REENTRY_MESSAGE)
_OPEN_SCOPE = re.escape(_OPEN_SCOPE_MESSAGE)


class TestFakeUnitOfWork:
    """The fake keeps rows in memory, commits and rolls back, and is entered once."""

    def test_value_set_is_returned(self) -> None:
        with FakeUnitOfWork() as uow:
            uow.system_state.set('colour', 'blue')
            assert uow.system_state.get('colour') == 'blue'

    def test_normal_exit_sets_committed(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            uow.system_state.set('colour', 'blue')
        assert uow.committed is True
        assert uow.rolled_back is False

    def test_exception_restores_store_and_sets_rolled_back(self) -> None:
        store = {'system_state': {'colour': 'red'}}
        expected = copy.deepcopy(store)
        uow = FakeUnitOfWork(store=store)
        with pytest.raises(ValueError):
            with uow:
                uow.system_state.set('colour', 'blue')
                uow.system_state.set('shape', 'square')
                raise ValueError("leave the fake")
        assert uow.store is store
        assert store == expected
        assert uow.rolled_back is True
        assert uow.committed is False

    def test_keyboard_interrupt_restores_store_and_sets_neither(self) -> None:
        store = {'system_state': {'colour': 'red'}}
        expected = copy.deepcopy(store)
        uow = FakeUnitOfWork(store=store)
        with pytest.raises(KeyboardInterrupt):
            with uow:
                uow.system_state.set('colour', 'blue')
                raise KeyboardInterrupt
        assert store == expected
        assert uow.committed is False
        assert uow.rolled_back is False

    def test_shared_store_carries_committed_write(self) -> None:
        store: dict = {}
        with FakeUnitOfWork(store=store) as first:
            first.system_state.set('colour', 'blue')
        with FakeUnitOfWork(store=store) as second:
            assert second.system_state.get('colour') == 'blue'

    def test_repositories_absent_after_exit(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            pass
        for name in FakeUnitOfWork.REPOSITORIES:
            assert not hasattr(uow, name)

    def test_entered_again_while_open_raises_guard_message(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            with pytest.raises(RuntimeError, match=_REENTRY):
                with uow:
                    pass
            uow.system_state.set('colour', 'blue')
        assert uow.committed is True
        assert uow.store == {'system_state': {'colour': 'blue'}}

    def test_entered_after_exit_raises_guard_message(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            pass
        with pytest.raises(RuntimeError, match=_REENTRY):
            with uow:
                pass


class TestFakeOpenScopeCheck:
    """A non-record fake is refused inside another open fake, and the open state always clears."""

    def test_nested_non_record_raises(self) -> None:
        with FakeUnitOfWork():
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with FakeUnitOfWork():
                    pass

    def test_refused_fake_leaves_store_and_enters_after_outer_exits(self) -> None:
        store = {'system_state': {'colour': 'red'}}
        inner = FakeUnitOfWork(store=store)
        with FakeUnitOfWork(store=store):
            before = copy.deepcopy(store)
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with inner:
                    pass
            assert store == before
        with inner:
            inner.system_state.set('colour', 'blue')
        assert inner.committed is True

    def test_non_record_inside_record_raises(self) -> None:
        with FakeUnitOfWork(record=True):
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with FakeUnitOfWork():
                    pass

    def test_record_inside_open_non_record_enters_and_restores_flag(self) -> None:
        with FakeUnitOfWork():
            with FakeUnitOfWork(record=True) as record:
                record.system_state.set('recorded', 'yes')
            with pytest.raises(RuntimeError, match=_OPEN_SCOPE):
                with FakeUnitOfWork():
                    pass

    @pytest.mark.parametrize('record', [False, True])
    def test_clear_after_normal_exit(self, record: bool) -> None:
        with FakeUnitOfWork(record=record):
            pass
        with FakeUnitOfWork() as uow:
            pass
        assert uow.committed is True

    @pytest.mark.parametrize('record', [False, True])
    def test_clear_after_exception(self, record: bool) -> None:
        with pytest.raises(ValueError):
            with FakeUnitOfWork(record=record):
                raise ValueError("leave the fake")
        with FakeUnitOfWork() as uow:
            pass
        assert uow.committed is True

    @pytest.mark.parametrize('record', [False, True])
    def test_clear_after_keyboard_interrupt(self, record: bool) -> None:
        with pytest.raises(KeyboardInterrupt):
            with FakeUnitOfWork(record=record):
                raise KeyboardInterrupt
        with FakeUnitOfWork() as uow:
            pass
        assert uow.committed is True


class TestFakeParity:
    """A fake has nothing the real unit of work or repository lacks."""

    def test_repository_names_are_real(self) -> None:
        assert set(FakeUnitOfWork.REPOSITORIES) <= set(UnitOfWork.REPOSITORIES)

    def test_fake_methods_exist_on_real_with_equal_signatures(self) -> None:
        for name, fake_class in FakeUnitOfWork.REPOSITORIES.items():
            real_class = UnitOfWork.REPOSITORIES[name]
            for method_name, method in inspect.getmembers(fake_class, inspect.isfunction):
                if method_name.startswith('_'):
                    continue
                real_method = getattr(real_class, method_name)
                assert inspect.signature(method) == inspect.signature(real_method), method_name


@pytest.mark.parametrize('kind', ['real', 'fake'])
class TestSystemStateContract:
    """Each FakeSystemStateRepository method answers as SystemStateRepository does."""

    @staticmethod
    def _repository(kind: str, db_session: Session) -> SystemStateRepository:
        if kind == 'real':
            return SystemStateRepository(db_session)
        return FakeSystemStateRepository({})

    def test_get_absent_key(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        assert repo.get('absent') is None

    def test_set_then_get(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('colour', 'blue')
        assert repo.get('colour') == 'blue'

    def test_set_overwrites(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('colour', 'blue')
        repo.set('colour', 'green')
        assert repo.get('colour') == 'green'

    def test_delete_present_key(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('colour', 'blue')
        assert repo.delete('colour') is True
        assert repo.get('colour') is None

    def test_delete_absent_key(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        assert repo.delete('absent') is False

    def test_get_bool_of_padded_true(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('flag', 'True ')
        assert repo.get_bool('flag') is True

    def test_get_bool_of_other_value(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('flag', 'yes')
        assert repo.get_bool('flag', default=True) is False

    def test_get_bool_of_absent_key_with_default(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        assert repo.get_bool('absent', default=True) is True

    def test_set_bool(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set_bool('on', True)
        repo.set_bool('off', False)
        assert (repo.get('on'), repo.get('off')) == ('true', 'false')

    def test_get_int(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('count', '42')
        assert repo.get_int('count') == 42

    def test_get_int_of_unparseable_value(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set('count', 'many')
        assert repo.get_int('count', default=3) == 3

    def test_get_int_of_absent_key_with_default(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        assert repo.get_int('absent', default=5) == 5

    def test_set_int(self, kind: str, db_session: Session) -> None:
        repo = self._repository(kind, db_session)
        repo.set_int('count', 7)
        assert repo.get('count') == '7'

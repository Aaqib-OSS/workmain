"""
Tests for workmain.services.tasks_service.

Covers list, today, find, get, complete and dismiss. Every test runs a use
case on fake_uow, its store seeded in the row shapes
tests/mocks/fake_unit_of_work.py's fake repositories state.
"""

from datetime import date, datetime

import pytest

from tests.mocks.fake_unit_of_work import FakeUnitOfWork
from workmain.services import tasks_service
from workmain.services.exceptions import NotATaskError, TaskNotFoundError

SEEDED = datetime(2099, 1, 1, 8, 0)


class TestListTasks:
    def test_limit_caps_rows_and_total_counts_all(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': f'task {i}', 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 2, 9, i), 'meeting_id': None, 'client_id': None,
            }
            for i in range(1, 26)
        }
        fake_uow.store['task_status'] = {
            i: {
                'id': i, 'note_id': i, 'status': 'active', 'completed_at': None,
                'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
            }
            for i in range(1, 26)
        }

        page = tasks_service.list_tasks(fake_uow, 'active', None, date(2099, 1, 2), 20)

        assert len(page.rows) == 20
        assert page.total == 25

    def test_limit_zero_returns_every_row(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': f'task {i}', 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 3, 9, i), 'meeting_id': None, 'client_id': None,
            }
            for i in range(1, 26)
        }
        fake_uow.store['task_status'] = {
            i: {
                'id': i, 'note_id': i, 'status': 'active', 'completed_at': None,
                'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
            }
            for i in range(1, 26)
        }

        page = tasks_service.list_tasks(fake_uow, 'active', None, date(2099, 1, 3), 0)

        assert len(page.rows) == 25
        assert page.total == 25

    def test_status_all_returns_every_status(self, fake_uow: FakeUnitOfWork) -> None:
        statuses = {1: 'active', 2: 'completed', 3: 'dismissed'}
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': status, 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 4, 9, i), 'meeting_id': None, 'client_id': None,
            }
            for i, status in statuses.items()
        }
        fake_uow.store['task_status'] = {
            i: {
                'id': i, 'note_id': i, 'status': status, 'completed_at': None,
                'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
            }
            for i, status in statuses.items()
        }

        page = tasks_service.list_tasks(fake_uow, 'all', None, date(2099, 1, 4), 0)

        assert {r.status for r in page.rows} == {'active', 'completed', 'dismissed'}

    def test_status_filter_narrows(self, fake_uow: FakeUnitOfWork) -> None:
        statuses = {1: 'active', 2: 'completed'}
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': status, 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 5, 9, i), 'meeting_id': None, 'client_id': None,
            }
            for i, status in statuses.items()
        }
        fake_uow.store['task_status'] = {
            i: {
                'id': i, 'note_id': i, 'status': status, 'completed_at': None,
                'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
            }
            for i, status in statuses.items()
        }

        page = tasks_service.list_tasks(fake_uow, 'completed', None, date(2099, 1, 5), 0)

        assert [r.note_id for r in page.rows] == [2]

    def test_row_fields_equal_seeded(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {7: {
            'id': 7, 'content': 'seeded content', 'tags': ['both', 'carry-forward'],
            'created_at': datetime(2099, 1, 6, 9, 0), 'meeting_id': None, 'client_id': None,
        }}
        fake_uow.store['task_status'] = {1: {
            'id': 1, 'note_id': 7, 'status': 'active', 'completed_at': None,
            'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
        }}

        page = tasks_service.list_tasks(fake_uow, 'active', None, date(2099, 1, 6), 0)

        assert page.rows == (
            tasks_service.TaskRow(
                7, 'active', date(2099, 1, 6), ('both', 'carry-forward'), 'seeded content',
            ),
        )

    def test_filters_hold_only_narrowing_filters(self, fake_uow: FakeUnitOfWork) -> None:
        d = date(2099, 1, 9)

        page = tasks_service.list_tasks(fake_uow, 'active', 'x', d, 0)
        assert page.filters == (('status', 'active'), ('search', 'x'), ('created', d))
        page = tasks_service.list_tasks(FakeUnitOfWork(store=fake_uow.store), 'all', None, None, 0)
        assert page.filters == ()


class TestListToday:
    def test_active_tasks_on_the_date_only(self, fake_uow: FakeUnitOfWork) -> None:
        seeds = {
            1: ('live', 'active', datetime(2099, 1, 10, 9, 0)),
            2: ('done', 'completed', datetime(2099, 1, 10, 10, 0)),
            3: ('yesterday', 'active', datetime(2099, 1, 9, 9, 0)),
        }
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': content, 'tags': ['carry-forward'],
                'created_at': created_at, 'meeting_id': None, 'client_id': None,
            }
            for i, (content, _, created_at) in seeds.items()
        }
        fake_uow.store['task_status'] = {
            i: {
                'id': i, 'note_id': i, 'status': status, 'completed_at': None,
                'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
            }
            for i, (_, status, _) in seeds.items()
        }
        d = date(2099, 1, 10)

        page = tasks_service.list_today(fake_uow, None, d)

        assert [r.note_id for r in page.rows] == [1]
        assert page.total == 1
        assert page.filters == (('status', 'active'), ('created', d))

    def test_search_narrows_and_is_a_filter(self, fake_uow: FakeUnitOfWork) -> None:
        seeds = {1: 'Splunk alert', 2: 'Other work'}
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': content, 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 10, 9, i), 'meeting_id': None, 'client_id': None,
            }
            for i, content in seeds.items()
        }
        fake_uow.store['task_status'] = {
            i: {
                'id': i, 'note_id': i, 'status': 'active', 'completed_at': None,
                'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
            }
            for i in seeds
        }
        d = date(2099, 1, 10)

        page = tasks_service.list_today(fake_uow, 'splunk', d)

        assert [r.note_id for r in page.rows] == [1]
        assert page.filters == (('status', 'active'), ('created', d), ('search', 'splunk'))


class TestFindTasks:
    def test_digit_string_is_a_note_id(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {7: {
            'id': 7, 'content': 'by id', 'tags': ['carry-forward'],
            'created_at': datetime(2099, 1, 11, 9, 0), 'meeting_id': None, 'client_id': None,
        }}
        fake_uow.store['task_status'] = {1: {
            'id': 1, 'note_id': 7, 'status': 'active', 'completed_at': None,
            'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
        }}

        page = tasks_service.find_tasks(fake_uow, '7')

        assert [r.note_id for r in page.rows] == [7]
        assert (page.total, page.filters) == (1, ())

    def test_unknown_id_raises(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError) as e:
            tasks_service.find_tasks(fake_uow, '2000000000')

        assert str(e.value) == 'No note found with ID 2000000000.'

    def test_note_without_task_raises(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {7: {
            'id': 7, 'content': 'plain', 'tags': ['internal-only'],
            'created_at': datetime(2099, 1, 12, 9, 0), 'meeting_id': None, 'client_id': None,
        }}

        with pytest.raises(NotATaskError) as e:
            tasks_service.find_tasks(fake_uow, '7')

        assert str(e.value) == str(NotATaskError(7))

    def test_search_finds_tasks_only(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': content, 'tags': tags,
                'created_at': datetime(2099, 1, 13, 9, i), 'meeting_id': None, 'client_id': None,
            }
            for i, content, tags in (
                (1, 'marker a task', ['carry-forward']),
                (2, 'marker not a task', ['internal-only']),
            )
        }
        fake_uow.store['task_status'] = {1: {
            'id': 1, 'note_id': 1, 'status': 'active', 'completed_at': None,
            'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
        }}

        page = tasks_service.find_tasks(fake_uow, 'marker')

        assert [r.note_id for r in page.rows] == [1]

    def test_search_covers_every_status(self, fake_uow: FakeUnitOfWork) -> None:
        statuses = {1: 'active', 2: 'completed', 3: 'dismissed'}
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': f'marker {status}', 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 14, 9, i), 'meeting_id': None, 'client_id': None,
            }
            for i, status in statuses.items()
        }
        fake_uow.store['task_status'] = {
            i: {
                'id': i, 'note_id': i, 'status': status, 'completed_at': None,
                'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
            }
            for i, status in statuses.items()
        }

        page = tasks_service.find_tasks(fake_uow, 'marker')

        assert {r.status for r in page.rows} == {'active', 'completed', 'dismissed'}

    def test_search_is_capped_at_ten(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {
            i: {
                'id': i, 'content': f'marker {i}', 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 15, 9, i), 'meeting_id': None, 'client_id': None,
            }
            for i in range(1, 13)
        }
        fake_uow.store['task_status'] = {
            i: {
                'id': i, 'note_id': i, 'status': 'active', 'completed_at': None,
                'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
            }
            for i in range(1, 13)
        }

        page = tasks_service.find_tasks(fake_uow, 'marker')

        assert len(page.rows) == 10
        assert page.total == 12
        assert page.filters == (('search', 'marker'),)

    def test_no_match_raises(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError) as e:
            tasks_service.find_tasks(fake_uow, 'nothing')

        assert str(e.value) == "No tasks found matching 'nothing'."


class TestGetTask:
    def test_completed_task_with_meeting_and_forwarding_note(
        self, fake_uow: FakeUnitOfWork
    ) -> None:
        done_at = datetime(2099, 1, 16, 12, 0)
        fake_uow.store['meetings'] = {5: {'id': 5, 'title': 'Sentinel sync', 'client_id': None}}
        fake_uow.store['notes'] = {
            7: {
                'id': 7, 'content': 'done', 'tags': ['carry-forward'],
                'created_at': datetime(2099, 1, 16, 9, 0), 'meeting_id': 5, 'client_id': None,
            },
            8: {
                'id': 8, 'content': 'target', 'tags': ['internal-only'],
                'created_at': datetime(2099, 1, 16, 10, 0), 'meeting_id': None,
                'client_id': None,
            },
        }
        fake_uow.store['task_status'] = {1: {
            'id': 1, 'note_id': 7, 'status': 'completed', 'completed_at': done_at,
            'forwarding_note_id': 8, 'created_at': SEEDED, 'updated_at': done_at,
        }}

        detail = tasks_service.get_task(fake_uow, 7)

        assert detail == tasks_service.TaskDetail(
            note_id=7, status='completed', created_at=datetime(2099, 1, 16, 9, 0),
            completed_at=done_at, dismissed_at=None, forwarding_note_id=8,
            tags=('carry-forward',), meeting_id=5, meeting_title='Sentinel sync',
            content='done',
        )

    def test_dismissed_task_sets_dismissed_at(self, fake_uow: FakeUnitOfWork) -> None:
        gone_at = datetime(2099, 1, 17, 12, 0)
        fake_uow.store['notes'] = {7: {
            'id': 7, 'content': 'gone', 'tags': ['carry-forward'],
            'created_at': datetime(2099, 1, 17, 9, 0), 'meeting_id': None, 'client_id': None,
        }}
        fake_uow.store['task_status'] = {1: {
            'id': 1, 'note_id': 7, 'status': 'dismissed', 'completed_at': gone_at,
            'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': gone_at,
        }}

        detail = tasks_service.get_task(fake_uow, 7)

        assert (detail.dismissed_at, detail.completed_at) == (gone_at, None)
        assert (detail.meeting_id, detail.meeting_title) == (None, None)

    def test_note_without_task_raises(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {7: {
            'id': 7, 'content': 'plain', 'tags': ['internal-only'],
            'created_at': datetime(2099, 1, 18, 9, 0), 'meeting_id': None, 'client_id': None,
        }}

        with pytest.raises(NotATaskError):
            tasks_service.get_task(fake_uow, 7)

    def test_unknown_note_raises(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError) as e:
            tasks_service.get_task(fake_uow, 99)

        assert str(e.value) == 'No note found with ID 99.'


class TestChangeTask:
    @pytest.mark.parametrize('change, status', [
        (tasks_service.complete_task, 'completed'),
        (tasks_service.dismiss_task, 'dismissed'),
    ])
    def test_change_sets_the_status_and_returns_the_row(
        self, fake_uow: FakeUnitOfWork, change: object, status: str
    ) -> None:
        fake_uow.store['notes'] = {7: {
            'id': 7, 'content': 'c', 'tags': ['carry-forward'],
            'created_at': datetime(2099, 1, 19, 9, 0), 'meeting_id': None, 'client_id': None,
        }}
        fake_uow.store['task_status'] = {1: {
            'id': 1, 'note_id': 7, 'status': 'active', 'completed_at': None,
            'forwarding_note_id': None, 'created_at': SEEDED, 'updated_at': SEEDED,
        }}

        row = change(fake_uow, 7)

        assert row == tasks_service.TaskRow(
            7, status, date(2099, 1, 19), ('carry-forward',), 'c',
        )
        assert fake_uow.committed is True
        stored = fake_uow.store['task_status'][1]
        assert stored['status'] == status
        assert stored['completed_at'] is not None

    def test_complete_note_without_task_raises(self, fake_uow: FakeUnitOfWork) -> None:
        fake_uow.store['notes'] = {7: {
            'id': 7, 'content': 'plain', 'tags': ['internal-only'],
            'created_at': datetime(2099, 1, 21, 9, 0), 'meeting_id': None, 'client_id': None,
        }}

        with pytest.raises(NotATaskError):
            tasks_service.complete_task(fake_uow, 7)

        assert fake_uow.committed is False

    def test_complete_unknown_note_raises(self, fake_uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError) as e:
            tasks_service.complete_task(fake_uow, 99)

        assert str(e.value) == 'No note found with ID 99.'

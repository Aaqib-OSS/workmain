"""
Command tests for the tasks group.

Each path through a command runs end to end through CliRunner against the
test's database, with the recording renderer. Rows are seeded through
db_session, and rows a path writes or leaves alone are read back by a query
after db_session.expunge_all().
"""

from datetime import date, datetime, time, timedelta
from unittest.mock import NonCallableMagicMock

from click.testing import CliRunner
from sqlalchemy.orm import Session

from workmain.cli.commands.tasks import TASK_LIST, TASK_RECORD, TASK_TODAY, tasks
from workmain.database.models import TaskStatus
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.task_status_repo import TaskStatusRepository
from workmain.services.results import Page
from workmain.services.tasks_service import TaskDetail, TaskRow


class TestTasksList:
    def test_defaults_show_active_tasks_capped_at_20(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        notes = NotesRepository(db_session)
        repo = TaskStatusRepository(db_session)
        active_ids = []
        for i in range(21):
            note = notes.create(
                content=f'ZqvActive {i}', tags=['carry-forward'],
                created_at=datetime(2099, 1, 1, 9, 0) + timedelta(minutes=i),
            )
            repo.create_active(note.id)
            active_ids.append(note.id)
        done = notes.create(
            content='ZqvDone', tags=['carry-forward'], created_at=datetime(2099, 1, 2, 9, 0),
        )
        repo.create_active(done.id)
        repo.set_completed(done.id)

        result = CliRunner(mix_stderr=False).invoke(tasks, ['list'], obj=recording_renderer)

        assert result.exit_code == 0, result.stderr
        recording_renderer.collection.assert_called_once()
        view, page = recording_renderer.collection.call_args.args
        assert view is TASK_LIST
        assert [row.note_id for row in page.rows] == active_ids[::-1][:20]
        assert {row.status for row in page.rows} == {'active'}
        assert (page.total, page.filters) == (21, (('status', 'active'),))
        db_session.expunge_all()
        statuses = [
            ts.status for ts in db_session.query(TaskStatus)
            .filter(TaskStatus.note_id.in_(active_ids + [done.id]))
        ]
        assert sorted(statuses) == ['active'] * 21 + ['completed']

    def test_limit_and_filters_cap_the_matching_tasks(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        notes = NotesRepository(db_session)
        repo = TaskStatusRepository(db_session)
        seeds = [
            ('ZqvMatch one', 'completed', datetime(2099, 1, 5, 9, 0)),
            ('ZqvMatch two', 'completed', datetime(2099, 1, 5, 10, 0)),
            ('ZqvMatch three', 'completed', datetime(2099, 1, 5, 11, 0)),
            ('ZqvMatch active', 'active', datetime(2099, 1, 5, 12, 0)),
            ('ZqvOther completed', 'completed', datetime(2099, 1, 5, 13, 0)),
            ('ZqvMatch next day', 'completed', datetime(2099, 1, 6, 9, 0)),
        ]
        ids = []
        for content, status, created_at in seeds:
            note = notes.create(content=content, tags=['carry-forward'], created_at=created_at)
            repo.create_active(note.id)
            if status == 'completed':
                repo.set_completed(note.id)
            ids.append(note.id)

        result = CliRunner(mix_stderr=False).invoke(
            tasks,
            ['list', '--limit', '2', '--status', 'completed', '--search', 'zqvmatch',
             '--date', '2099-01-05'],
            obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        view, page = recording_renderer.collection.call_args.args
        assert view is TASK_LIST
        assert [row.note_id for row in page.rows] == [ids[2], ids[1]]
        assert page.total == 3
        assert page.filters == (
            ('status', 'completed'), ('search', 'zqvmatch'), ('created', date(2099, 1, 5)),
        )

    def test_all_removes_the_cap_whatever_limit_says(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        notes = NotesRepository(db_session)
        repo = TaskStatusRepository(db_session)
        seeds = [
            ('ZqvMatch one', 'completed', datetime(2099, 1, 5, 9, 0)),
            ('ZqvMatch two', 'completed', datetime(2099, 1, 5, 10, 0)),
            ('ZqvMatch three', 'completed', datetime(2099, 1, 5, 11, 0)),
            ('ZqvMatch active', 'active', datetime(2099, 1, 5, 12, 0)),
            ('ZqvOther completed', 'completed', datetime(2099, 1, 5, 13, 0)),
            ('ZqvMatch next day', 'completed', datetime(2099, 1, 6, 9, 0)),
        ]
        ids = []
        for content, status, created_at in seeds:
            note = notes.create(content=content, tags=['carry-forward'], created_at=created_at)
            repo.create_active(note.id)
            if status == 'completed':
                repo.set_completed(note.id)
            ids.append(note.id)

        result = CliRunner(mix_stderr=False).invoke(
            tasks,
            ['list', '--all', '--limit', '2', '--status', 'completed', '--search', 'zqvmatch',
             '--date', '2099-01-05'],
            obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        view, page = recording_renderer.collection.call_args.args
        assert view is TASK_LIST
        assert [row.note_id for row in page.rows] == [ids[2], ids[1], ids[0]]
        assert page.total == 3


class TestTasksToday:
    def test_today_shows_todays_active_tasks_matching_the_search(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        today = date.today()
        notes = NotesRepository(db_session)
        repo = TaskStatusRepository(db_session)
        seeds = [
            ('ZqvToday match', 'active', datetime.combine(today, time(0, 1))),
            ('ZqvElse', 'active', datetime.combine(today, time(0, 2))),
            ('ZqvToday done', 'completed', datetime.combine(today, time(0, 3))),
            ('ZqvToday yesterday', 'active', datetime.combine(today - timedelta(days=1), time(9))),
        ]
        ids = []
        for content, status, created_at in seeds:
            note = notes.create(content=content, tags=['carry-forward'], created_at=created_at)
            repo.create_active(note.id)
            if status == 'completed':
                repo.set_completed(note.id)
            ids.append(note.id)

        result = CliRunner(mix_stderr=False).invoke(
            tasks, ['today', '--search', 'zqvtoday'], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.collection.assert_called_once()
        view, page = recording_renderer.collection.call_args.args
        assert view is TASK_TODAY
        assert [row.note_id for row in page.rows] == [ids[0]]
        assert page.filters == (('status', 'active'), ('created', today), ('search', 'zqvtoday'))


class TestTasksShow:
    def test_show_picks_the_task_and_records_its_detail(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        created_at = datetime(2099, 1, 7, 9, 0)
        note = NotesRepository(db_session).create(
            content='ZqvShow', tags=['carry-forward'], created_at=created_at,
        )
        TaskStatusRepository(db_session).create_active(note.id)

        result = CliRunner(mix_stderr=False).invoke(
            tasks, ['show', str(note.id)], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        row = TaskRow(note.id, 'active', date(2099, 1, 7), ('carry-forward',), 'ZqvShow')
        recording_renderer.pick.assert_called_once_with(TASK_LIST, Page((row,), 1, ()))
        recording_renderer.record.assert_called_once_with(
            TASK_RECORD,
            TaskDetail(
                note_id=note.id, status='active', created_at=created_at, completed_at=None,
                dismissed_at=None, forwarding_note_id=None, tags=('carry-forward',),
                meeting_id=None, meeting_title=None, content='ZqvShow',
            ),
        )
        recording_renderer.cancelled.assert_not_called()

    def test_show_with_the_pick_cancelled_records_nothing(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        note = NotesRepository(db_session).create(
            content='ZqvShow', tags=['carry-forward'], created_at=datetime(2099, 1, 7, 9, 0),
        )
        TaskStatusRepository(db_session).create_active(note.id)
        recording_renderer.pick.side_effect = lambda view, page: None

        result = CliRunner(mix_stderr=False).invoke(
            tasks, ['show', 'zqvshow'], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.pick.assert_called_once()
        recording_renderer.cancelled.assert_called_once_with()
        recording_renderer.record.assert_not_called()
        db_session.expunge_all()
        assert db_session.query(TaskStatus).filter(
            TaskStatus.note_id == note.id
        ).one().status == 'active'


class TestTasksCompleteDismiss:
    def test_complete_marks_the_picked_task_completed(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        note = NotesRepository(db_session).create(
            content='ZqvChange', tags=['carry-forward'], created_at=datetime(2099, 1, 8, 9, 0),
        )
        TaskStatusRepository(db_session).create_active(note.id)

        result = CliRunner(mix_stderr=False).invoke(
            tasks, ['complete', str(note.id)], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.pick.assert_called_once()
        recording_renderer.changed.assert_called_once_with(
            TASK_RECORD,
            TaskRow(note.id, 'completed', date(2099, 1, 8), ('carry-forward',), 'ZqvChange'),
            'Completed',
        )
        db_session.expunge_all()
        stored = db_session.query(TaskStatus).filter(TaskStatus.note_id == note.id).one()
        assert stored.status == 'completed'
        assert stored.completed_at is not None

    def test_complete_with_the_pick_cancelled_changes_nothing(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        note = NotesRepository(db_session).create(
            content='ZqvChange', tags=['carry-forward'], created_at=datetime(2099, 1, 8, 9, 0),
        )
        TaskStatusRepository(db_session).create_active(note.id)
        recording_renderer.pick.side_effect = lambda view, page: None

        result = CliRunner(mix_stderr=False).invoke(
            tasks, ['complete', 'zqvchange'], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.cancelled.assert_called_once_with()
        recording_renderer.changed.assert_not_called()
        db_session.expunge_all()
        stored = db_session.query(TaskStatus).filter(TaskStatus.note_id == note.id).one()
        assert (stored.status, stored.completed_at) == ('active', None)

    def test_dismiss_marks_the_picked_task_dismissed(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        note = NotesRepository(db_session).create(
            content='ZqvChange', tags=['carry-forward'], created_at=datetime(2099, 1, 8, 9, 0),
        )
        TaskStatusRepository(db_session).create_active(note.id)

        result = CliRunner(mix_stderr=False).invoke(
            tasks, ['dismiss', str(note.id)], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.pick.assert_called_once()
        recording_renderer.changed.assert_called_once_with(
            TASK_RECORD,
            TaskRow(note.id, 'dismissed', date(2099, 1, 8), ('carry-forward',), 'ZqvChange'),
            'Dismissed',
        )
        db_session.expunge_all()
        stored = db_session.query(TaskStatus).filter(TaskStatus.note_id == note.id).one()
        assert stored.status == 'dismissed'
        assert stored.completed_at is not None

    def test_dismiss_with_the_pick_cancelled_changes_nothing(
        self, db_session: Session, recording_renderer: NonCallableMagicMock
    ) -> None:
        note = NotesRepository(db_session).create(
            content='ZqvChange', tags=['carry-forward'], created_at=datetime(2099, 1, 8, 9, 0),
        )
        TaskStatusRepository(db_session).create_active(note.id)
        recording_renderer.pick.side_effect = lambda view, page: None

        result = CliRunner(mix_stderr=False).invoke(
            tasks, ['dismiss', 'zqvchange'], obj=recording_renderer,
        )

        assert result.exit_code == 0, result.stderr
        recording_renderer.cancelled.assert_called_once_with()
        recording_renderer.changed.assert_not_called()
        db_session.expunge_all()
        stored = db_session.query(TaskStatus).filter(TaskStatus.note_id == note.id).one()
        assert (stored.status, stored.completed_at) == ('active', None)

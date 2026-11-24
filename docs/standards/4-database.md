## 4. Database Standards

### 4.1 Session pattern

- Application code under `workmain/` opens a session through `DatabaseConnection.session_scope()`, reached through `get_db()`; tests follow §6.1. The scope commits when its block exits normally, rolls back when an `Exception` leaves the block, and closes the session in every case.

  ```python
  from workmain.database.connection import get_db

  db = get_db()
  with db.session_scope() as session:
      repo = SomeRepository(session)
      # ... work ...
  ```

  ```python
  from workmain.services.unit_of_work import UnitOfWork

  def set_flag(uow: UnitOfWork, key: str) -> None:    # a use case
      with uow:
          uow.system_state.set_bool(key, True)
          # ... work; a normal return commits ...

  set_flag(UnitOfWork(), 'some_flag')                  # its caller
  ```

- Code takes one of two forms, which are in use side by side.

**Session-taking form.**

- **The code that opens a scope owns it.** It may commit inside the scope. Code it hands the session to — a repository, a service, an orchestrator such as `ActionExecutor` — reads and writes through that session; committing it, rolling it back and opening another session are the owner's. Two exceptions: handed code may contain a failure in a savepoint (`session.begin_nested()`, below), and it records an outside action in a session of its own (§4.3).
- **The owner commits before it waits.** If the scope has written since its last commit, the owner commits immediately before it prompts, opens an editor, starts a child `workmain` process or performs an outside action.

**Unit-of-work form.** A caller builds a `UnitOfWork` (`workmain/services/unit_of_work.py`) and passes it to a use case. A unit of work has no public `commit()`.

- **A use case** is a service function that a surface, workflow, orchestration module or the daemon calls. It takes a unit of work not yet entered and enters it with `with uow:`. On exit the unit of work commits after a normal return and rolls back on an `Exception`.
- **An operation** is a function a use case calls. It takes a unit of work already entered and works inside it; entering and committing are the use case's.
- **The caller builds the unit of work, one for each use-case call,** and the use case enters it.
- **A use case makes an outside call only while its unit of work holds no write.** It receives the outside-call dependency from its caller, and that dependency makes its own §4.3 record.
- **A use case that decides not to go ahead raises,** so a normal return always means its writes are wanted.
- **A use case is called with no `session_scope()` open,** except on a `UnitOfWork(record=True)` under §4.3's conditions for an outside-action record. `UnitOfWork.__enter__` raises otherwise.

**Both forms.**

- **A handler that recovers from an exception sits outside the `with`, or around a savepoint inside it.** A handler around the `with` runs after the scope has rolled back. In the session-taking form, the guarded work inside the block runs in `with session.begin_nested():` and the handler wraps that, so a failure rolls back to the savepoint and the scope carries on. A savepoint's block commits nothing: a commit there commits the whole transaction. A database error caught inside the block without a savepoint leaves the transaction failed, and the scope's commit then raises.
- **A command exits after its scope closes.** `SystemExit`, from `sys.exit()` or `raise SystemExit`, and `KeyboardInterrupt` are not `Exception`s, so a scope they leave neither commits nor rolls back, and its uncommitted writes are discarded. `ctx.exit()` and `click.Abort` are `Exception`s and roll the scope back.

### 4.2 Session discipline

- **Code that changes an ORM object queries it in the session that writes it.** A session does not track an object loaded in another, so a change to one passed across is never written, and nothing raises.
- **Code reads what it needs from an ORM object while its `session_scope()` block is open.** The exit commit expires every loaded attribute, and a read afterwards raises `DetachedInstanceError`.

### 4.3 Repository pattern

- All data access goes through a repository.
- Every model subclasses `Base` in `workmain/database/models.py`.

  ```python
  class SomethingRepository:
      def __init__(self, session: Session) -> None:
          self.session = session

      def create(self, name: str) -> Something:
          obj = Something(name=name)
          self.session.add(obj)
          self.session.flush()
          self.session.refresh(obj)
          return obj
  ```

- **A repository method flushes after a write, and refreshes an object it returns,** so the object carries its id and its database defaults, and later queries in the session see the row. Committing is the scope owner's (§4.1).
- **A repository method that returns rows loads, with them, every related record its callers read on each row.** A relationship is lazy by default, so reading one costs a query per row. The method uses `contains_eager` where its query already joins the related table, `joinedload` for a many-to-one it does not join, and `selectinload` for a one-to-many, and loads only what its callers read. A change that adds a per-row read of a relationship adds the loader to the method in the same change. §6.2 states how the loading is tested.

**Outside-action records.**

- **A row that records an outside action commits on its own.** An outside action is something already done outside WorkmAIn's database: a provider call that has been billed, a file in Drive, a Slack message, an entry in Clockify. Its record is written immediately after the action, in a session of its own opened with `get_db().record_scope()`, independent of the command's transaction, so a later failure in the command cannot undo the record of something that cannot be undone. `record_scope()` is `session_scope()` with a lock timeout, so a record that reaches a row another transaction holds fails instead of waiting.
  - It writes and references only rows the command's open transaction has not written. A second session cannot see an uncommitted row, and waits on a row the transaction has locked.
  - Its failure is reported. Cost recording logs a warning and carries on. Every other record reports, on stderr, what happened outside, what was not recorded and what will repeat. The command's exit status stays as it was: the outside action succeeded, and a non-zero exit invites a rerun that would repeat it.
  - It is tested at the function that writes it (§6.2).

### 4.5 Migrations

- **A database's schema changes only through an Alembic revision** in `workmain/database/migrations/versions/`. `alembic.ini` at the repository root configures Alembic (§7). `workmain/database/migrations/env.py` connects through `DATABASE_URL` in `workmain/database/connection.py`, so `.env` names the database a command reaches.
- **A revision is written** with `alembic revision -m "<what it changes>" --rev-id <NNNN>` from the repository root, where `<NNNN>` is the next four-digit number after the highest in `versions/`. Its `upgrade()` makes the change. Its `downgrade()` reverses it, or raises where reversing would destroy data. A change to a table changes its model in `workmain/database/models.py` in the same commit.
- **A revision is applied** with `alembic upgrade head` from the repository root. `alembic current` prints the revision a database is at.
- **The first revision, `0001`, is a baseline:** live's schema when Alembic was adopted, in `versions/0001_baseline.sql`. Live was stamped at it, not built by it. Any other database is built from empty by `alembic upgrade head`.
- **Applying a revision to the live database is an authorization point** (§1.4).

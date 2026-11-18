## 6. Testing Standards

- pytest is the exclusive runner.
- **The application suite is a bare `pytest` from the repository root.** Any other run offered as the suite's result names the alternative and states why.
- Non-application suites, such as `pytest automation/`, are separate suites, each reached by its own path.
- **A test reports what actually happened.**
  - Passed means it ran to its end and its assertions held.
  - Failed means it ran and raised an error, timed out or gave a wrong answer.
  - Skipped means a precondition declared with `@pytest.mark.skipif` was absent, decided before the test exercises anything.
- **Recorded test evidence states all three counts, in the form `<passed> passed, <failed> failed, <skipped> skipped`, and writes each one even when it is zero**, so the record shows whether the whole suite ran.

### 6.1 Test isolation from the database

**Every test runs in `workmain_test`, inside one transaction that rolls back when the test ends.** The fixtures in `tests/conftest.py` build the database and hold the transaction, and `pytest --fixtures -v` shows how each one works.

- **A test seeds and reads through `db_session`.** Every session the code under test opens through `get_db()` joins the same transaction, so the test and the code see each other's writes.
- **Everything a test reaches stays on the test's connection.** Tests of the database build are the only ones that run outside it, because the build comes before the transaction, and they undo what they change.

### 6.2 Writing a test

**Each piece of logic is tested in the layer that owns it** (`docs/ARCHITECTURE.md` §1).

- **Behaviour** is tested at the service. The test calls the service function and asserts the result's fields or the exception it raises. A service that takes a unit of work gets `fake_uow`, a `FakeUnitOfWork`, and one that still takes a session gets `db_session`.
- **SQL** is tested at the repository, on `db_session`. Each fake repository method is tested against the real one, in a class parametrized over both, so the fake answers as the database does. A method that loads related records with its rows (§4.3) has a test that its statement count stays the same as its rows grow, with each row seeded with related rows of its own and `db_session.expunge_all()` called before counting, so a lazy load shows in the count.
- **A command** has one end-to-end test per path through it: each outcome of a flag, a prompt's answer or a pick. The test runs the command through `CliRunner` against the test's database, with a recording renderer, and asserts the exit code, what the renderer received, and the rows the path writes or leaves alone.
- **Printed text** is read only by renderer tests, at a width the test sets, and by a command test reading the `Error:` line on `result.stderr`.
- **An outside-action record** (§4.3) is tested at the function that writes it: a spy shows the function opened `record_scope()`, and the record is read through `db_session`. The spy stands for the record surviving its caller's failure, which only production shows.

Converting code to a new form replaces every test of it, in whichever file it is.

Rules:

- **A test's name says what it checks, and is its description.**
- **A test's result depends only on what it sets up, and its changes stay inside `workmain_test` and its `tmp_path`.** Anything it needs from `config/`, `.env`, `~/.workmain/`, the terminal's width or the network, it sets up itself.
- **A test seeds the rows it needs**: on `db_session` for the database, or into `fake_uow`'s store, in the row shape its fake repository's docstring describes.
- **A test is a method of a plain class, and it takes what it needs as arguments.** Related tests share a `Test<Topic>` class. A test takes its fixtures and `parametrize` values as arguments and builds everything else in its own body.
- **Each test checks one path**, with as many assertions as that path needs.

### 6.3 Placement

- Moved to §7.

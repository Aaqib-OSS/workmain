## 5. CLI Standards

- Governs everything in `workmain/cli/commands/`.

### 5.1 Hierarchy

  ```text
  workmain <group> <subcommand> [ARGUMENT] [OPTIONS]
      │         │         │
    noun      verb    what/how
  ```

- A top-level standalone command is an orchestration workflow that coordinates several groups. Ray approves each new one against that criterion.

### 5.2 Groups

- A group is a noun.
  - Plural for collections (`notes`, `meetings`, `reports`).
  - Singular for a single integration (`clockify`, `gdocs`, `slack`) or for configuration/state (`schedule`, `notifications`).
  - A group that could have a `list` subcommand is plural.
- One domain is one group: a service's commands sit under a single top-level group.
- A subgroup is one level deep and follows the same noun rule, with three exceptions:
  - **`set`** as a configuration namespace (`clients set active`, `providers set default`, `slack set channel`), where the parent has more than one configurable property and the subcommands are the property nouns.
  - **`sync`** with `push` / `pull` / `both` (`clockify sync push`).
  - **`upload`** with an artifact noun (`gdocs upload notes`).
- A group's callback only prepares the context its subcommands use. Called with no subcommand, a group prints its help, which Click does itself while the group leaves `invoke_without_command` unset. A group reports its own state through a `status` subcommand (§5.3).

### 5.3 Subcommands

- A subcommand is an imperative verb from the standard vocabulary.

| Action | Verb | Replaces |
| --- | --- | --- |
| Create a record | `add` | `create`, `new`, `insert` |
| Create a structured resource | `create` | `make`, `build`, `generate` |
| Modify a record | `edit` | `update`, `modify`, `change` |
| Remove a record | `delete` | `remove`, `rm`, `drop` |
| List | `list` | `ls`, `all`, `view` |
| Show one item in detail | `show` | `get`, `detail`, `inspect` |
| Write output to disk | `save` | `export`, `write`, `dump` |
| Transmit to a recipient | `send` | `post` (except Slack) |
| Render without saving | `preview` | `draft`, `render` |
| Read an external file | `import` | `load`, `ingest` |
| Verify credentials | `auth` | `login`, `connect` |
| Check integration state | `status` | `info`, `health`, `ping` |
| Archive to an external store | `upload` | `send`, `push`, `sync` |

- **A domain-specific verb** is imperative, approved by Ray, documented in `--help`, and distinct from every standard verb. The approved verbs, each with its reason, are `APPROVED_VERBS` in `tests/test_cli_conventions.py`, which fails the suite on any command name other than a standard verb from the table above, an approved verb, or a name §5.1 or §5.2 permits.
- Names that predate that test are its `EXISTING_EXCEPTIONS`. The list only shrinks: an entry leaves when its command is renamed or removed.

### 5.4 Arguments vs. options

- **Positional**
  - when the value is required and unambiguous.
  - At most two per command.
  - Beyond that, named options for all but the primary target.
- **Option**
  - when the value is optional,
  - is one of several independent modifiers,
  - or needs a label to be understood.
- **Name-or-ID targeting.** Every command operating on a database record accepts either its ID or its name.
  - An exact name match resolves directly.
  - Multiple matches open the fuzzy picker, with enough context (date, type, status) to tell them apart.
- **Free-form text** is accepted inline, as a quoted positional, and asked for with `click.prompt()` when omitted.

### 5.5 Flags

- Every option has a `--long-form` in lowercase-hyphenated words.
- Short forms are optional.

**Case convention:** lowercase short forms are for frequent flags; uppercase for the less-used variant of a related concept (`-t/--tags` vs `-T/--time`).

- **A short form means one long form across every command.**
- **Some flags have no short form on purpose:** safety-critical or infrequent ones, where friction is the point. They are `NO_SHORT_FORM` in `tests/test_cli_conventions.py`.
- `tests/test_cli_conventions.py` checks both rules against every command Click builds, so a conflict fails the suite.

- Boolean flags use `is_flag=True`.
- A multi-value option takes one comma-delimited value (`--tags ilo,cf`).

### 5.6 Output

**A command parses, calls and renders.**

- **Parse.** A command parses its arguments with Click types (`workmain/cli/params.py`).
- **Call.** It calls a function in `workmain/services/`, which decides everything the command reports. The command is the service's caller under `docs/standards/4-database.md` §4.1: it builds the `UnitOfWork` for each use-case call, or owns the `session_scope()` for a service that takes a session. It closes any scope it opens before it renders, and before it calls a service function that acts outside WorkmAIn, which records the action in a scope of its own (§4.3).
- **Render.** It passes the service's result, unchanged, to the `Renderer` it receives through `@pass_renderer` (`workmain/cli/output.py`), with a view it declares as a module constant. All output is the renderer's: it builds every row, formats every value and writes everything the user sees. How it lays out a result is `workmain/cli/output.py`'s, stated in its docstrings and pinned by `tests/test_output.py`.
- The command ends by returning or by raising.

**Errors and exit codes.**

- A service raises `ServiceValidationError` for a request it cannot carry out, a missing setting such as an API key included, and `IntegrationError` (`workmain/services/exceptions.py`) when a call to another system fails or is refused.
- An exception the command does not recover from propagates to `WorkmAInGroup`, which reports it. Every group is declared with `cls=WorkmAInGroup`, so a command run through its own group, as its tests run it, reports the same way.
- A result that can partly fail carries an `error`, which the service builds: the command renders the result, then raises the error when it is set.
- A warning that a calling process must receive, such as how a result was produced, goes to stderr, where the caller reads it as the command's warning.
- A command that reports an error exits with one of the non-zero codes below. A cancelled pick and a warning exit `0`.
- Exit codes:
  - `0` success.
  - `1` user-facing error. A `ServiceValidationError` is reported as Click's `Error: <message>` on stderr. An exception no command handled is reported as one `Error: <type>: <message>` line on stderr, and its traceback is logged at `DEBUG`: run the command again with `LOG_LEVEL=DEBUG` to see it.
  - `2` usage error: an unknown option, a missing argument or a rejected value. Click exits `2` for these itself.
  - `3` integration error: an `IntegrationError`, reported as `Error: <message>` on stderr.

**Patterns.**

- **Confirm.** A command that deletes, or sends outside WorkmAIn, asks first unless `--force` is set. Its service offers a preview and an apply. The preview says whether there is anything to apply, carries what the apply needs, and composes the question, which states exactly what the apply will do. The command renders the preview. With nothing to apply it calls `renderer.nothing_to_do()` and stops. With `--force` set it calls the apply. Otherwise it asks the preview's question with `click.confirm()`, and calls the apply on yes or `renderer.cancelled()` on no. It renders the apply's result. The preview and the apply each run in a unit of work or scope of their own (§4.1).
- **Pick.** The service finds the candidates in one call, and acts on the chosen ID in another, which re-reads the record.
- **Dry run.** A dry run changes nothing. The command passes `dry_run=True` to `Renderer.report`.

**Help text.** Every Click command function has a docstring, with a one-line summary and at least one `Examples:` block. That docstring *is* the `--help` output, so it is written for the person running the command and is the one place invocations and flags belong.

### 5.7 Files and registration

- One top-level group per file, at `workmain/cli/commands/<group>.py`, registered with `cli.add_command()` in `workmain/cli/interface.py`.

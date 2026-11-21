## 3. Code Standards

Comments, docstrings and strings describe the code as it is. Git and the issue hold how it came to be, including any gate, phase, sprint, backlog item or open question.

`automation/style_check.py` checks every line a branch changes against the rules here that a tool can check. `pyproject.toml` `[tool.ruff.lint]` maps each rule code it uses to its section.

### 3.1 Module headers

- A module docstring follows PEP 257: a one-line summary, then a paragraph saying what the module does, why, and what it requires, such as an environment variable it reads or the call that yields an instance of it. Git tags, `CHANGELOG.md` and `workmain/__version__.py` are the version record.

  ```python
  """
  Parses, validates, converts and formats tags for display.

  Tags are case-insensitive, are normalized on entry, and are validated
  against config/tags.json. Callers receive full names; short forms are an
  input convenience and are never stored.
  """
  ```

### 3.2 Import organization

- Standard library, then third-party, then local, with a blank line between groups.

### 3.5 Function and class docstrings

- Every parameter and return has a type hint, written with built-in generics and `|`: `list[str]`, `dict[str, int]`, `int | None`.
- Every public function and class has a Google-style docstring, with the `Args:`, `Returns:`, `Raises:` and `Attributes:` blocks that apply.

  ```python
  def create(self, content: str, tags: list[str], project_id: int | None = None) -> Note:
      """
      Create a new note.

      Args:
          content: Note content (clean text without hashtags)
          tags: List of full tag names (e.g., ['internal-only'])
          project_id: Optional project ID to link

      Returns:
          Created Note object
      """
  ```

### 3.7 Security

- A secret is read from `.env` through python-dotenv, or from a file under `~/.workmain/` named by the module that reads it.
- `.env` and every secret file under `~/.workmain/` are mode 600.

### 3.8 Framework mechanisms first

- **Use the mechanism Python's standard library, Click, Rich or SQLAlchemy provides before writing your own.** Where two of them do the job, either meets this rule, unless another section names one.
- **A spec that writes its own records why.** Its Decision Log names the mechanism it set aside and the reason it does not fit.
- The library's version is tested and behaves the same in every caller. A hand-written version has to get every edge case right on its own, and each copy can get a different one wrong.

| Job | Written by hand | Use instead |
| --- | --- | --- |
| Ask for a number from 1 to `n` | A loop that converts and bounds-checks the input | `click.prompt(..., type=click.IntRange(1, n))` |
| Restrict an option to fixed values | An `if value not in (...)` check in the command body | `type=click.Choice([...])` on the option |
| Parse a `YYYY-MM-DD` date | Splitting on `-` and building a `date` from the parts | `date.fromisoformat(value)` |
| Build a file path | Joining strings with `/` | `pathlib.Path(base) / name` |
| Share one instance per run | A module variable and a `None` check in the getter | `@functools.cache` on a getter named for what it returns, such as `get_tag_system()` |

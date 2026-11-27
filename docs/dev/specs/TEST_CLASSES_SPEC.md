# Module-level tests into plain classes — Spec

**Status:** Draft

**Author:** Spanner

**Date:** 20261127

**Read at:** `043e8c5`

**Branch:** `feature/issue-288-test-classes` (base: `dev`, `docs/standards/2-git.md` §2.1)

**Target release:** set by `/closeout`

**Originating item:** Issue #288

**Design study:** `../design/DESIGN_TEST_CLASSES.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261127 | Ray | Branch type `feature/*`, on the full path. Pull request #290 was opened by an outside contributor without a spec. Its commit `402ec1a` is the base of this branch, and the contributor gets full credit. #290 is closed with a reference to this branch's pull request. | Adopted; header, Step 1, Close-out. |
| 20261127 | Ray | Design study Q1: Option A. All 15 module-level command tests move, including the 11 providers command tests #290 already moved and the 4 in command test files it left. | Adopted; DR1, Step 2, AC1.1. |
| 20261127 | Ray | Design study Q2: Option A. `402ec1a` is cherry-picked with its author kept. The same commit carries `f6667a2`'s five test bodies and the annotations the style check requires, and its body says which lines those are. | Adopted; Step 1. |
| 20261127 | Ray | The issue gains a criterion: the three Ollama unavailability tests pass whatever listens on `localhost:11434`. | Adopted; DR4, Step 3, AC4.1. The issue has no criterion for it, so per `docs/standards/1-workflow.md` §1.2, §5 states it as AC4.1 and the issue body gains it as a fourth criterion at close-out. |
| 20261127 | Ray | Every line a step changes, re-indented lines included, passes `automation/style_check.py` in that step's commit. No violation is left for a later issue. | Adopted; §4 opening. |

---

## 1. Scope

**In scope:**

- The 86 module-level tests at the **Read at:** commit (§2), in `tests/test_provider_foundation.py` (66), `tests/test_ai_foundation.py` (6), `tests/test_ai_providers_live.py` (4), `tests/test_cli_logging.py` (4), `tests/test_compare_providers.py` (2), `tests/test_cost_display.py` (1), `tests/test_meetings_merge.py` (1), `tests/test_meetings_reschedule.py` (1) and `tests/test_notes_add.py` (1). Each becomes a method of a plain class in its own file (Steps 1 and 2).
- What `automation/style_check.py` requires of each line those moves change (§4 opening).
- How `test_ollama_provider_generate_raises_unavailable`, `test_ollama_provider_test_connection_returns_false` and `test_ollama_provider_check_availability_returns_unavailable` in `tests/test_provider_foundation.py` get the unavailability they test (Step 3).

**Out of scope:**

- What any other test checks (DR2).
- The 60 tests in `unittest.TestCase` classes: the command-group issues under #198 convert them.
- The duplicate coverage of `check_availability` and `generate` in `tests/test_ollama_provider.py` (design study F9). Both files keep their tests.
- Whether the live tests in `tests/test_ai_providers_live.py` leave the application suite: #292.
- `usefixtures('offline_provider_env')` on `TestCompareProviders` in `tests/test_compare_providers.py`: #287.
- AC, DR, T-number and issue-number tags in moved docstrings and comments. `docs/standards/3-code.md` §3 does not list them, and the style check does not flag them (design study §3, standards gap reported to Ray).
- Any file outside `tests/`, other than this set's documents.

## 2. Verified current state

At `043e8c5`, whose `tests/` is `origin/dev` `5d9bed2`'s, 20261127.

| Claim | Evidence |
| --- | --- |
| The issue's AST command prints 86 lines: the 86 tests §1 lists, by file. | The AC1.1 command in §5 |
| Pull request #290 is one commit, `402ec1a`, authored by its contributor and parented on `3fff87a`. It changes only `tests/test_provider_foundation.py`, `tests/test_ai_foundation.py`, `tests/test_ai_providers_live.py`, `tests/test_cli_logging.py` and `tests/test_compare_providers.py`. Its subject, `Move module-level tests into topic classes`, has no `<type>(<scope>):` prefix, so `.githooks/commit-msg` would refuse it as a commit on this branch. | `git log -1 --format='%an%n%s%n%P' 402ec1a`; `git diff --stat 3fff87a 402ec1a`; `docs/standards/2-git.md` §2.4 |
| In those five files, `402ec1a` moves all 82 module-level tests into plain classes: 7 in `tests/test_provider_foundation.py` and one in each of the others (design study F3). Measured against `3fff87a`, the AC2.2 command prints only the 4 tests `402ec1a` leaves, in the other four files, as `MISSING`. | The AC2.2 command, run as `python3 - 3fff87a 402ec1a` |
| Measured against this branch's base, the same command also prints `CHANGED` for 5 tests whose bodies `f6667a2` (#155) changed on `dev` after `3fff87a`: `test_claude_provider_reads_model_from_config`, `test_claude_provider_requires_model_in_config`, `test_gemini_provider_reads_model_from_config`, `test_gemini_provider_requires_model_in_config` and `test_provider_disabled_by_construction_failure_reports_reason`. | The AC2.2 command, run as `python3 - origin/dev 402ec1a` |
| `git cherry-pick 402ec1a` onto `5d9bed2` conflicts in `tests/test_provider_foundation.py` in two hunks, both where `402ec1a` deletes an original that `f6667a2` changed. The moved copies do not conflict. | `git merge-tree --write-tree origin/dev 402ec1a` |
| `automation/style_check.py --base 3fff87a` on `402ec1a` reports 128 violations on re-indented lines: ANN201 (82), ANN001 (29), ANN202 (11), D205 (3), D213 (3). `pyproject.toml` ignores D101–D103 under `tests/**`, so a new class needs no docstring. | Design study F7; `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` |
| 11 of the 66 tests in `tests/test_provider_foundation.py` are providers command tests run through `CliRunner`, which #211 will replace. No other module-level test there reaches `workmain.cli`. | Design study F11 |
| `tests/test_cost_display.py::test_costs_usage_error_exits_2_on_stderr` is parametrized over `meetings`, `notes`, `providers` and `reports`. | `tests/test_cost_display.py:133` |
| The three Ollama tests each build `OllamaProvider({'model': 'mistral-7b', 'host': 'localhost', 'port': 11434})` and reach the real `urllib.request.urlopen` through `OllamaProvider.check_availability`. `generate` calls `check_availability` first, and `BaseProvider.test_connection` returns whether it is `AVAILABLE`. `check_availability` returns `UNAVAILABLE` on any exception. | `tests/test_provider_foundation.py:124`, `:137`, `:156`; `workmain/ai/providers/ollama.py` `check_availability`, `generate`; `workmain/ai/base_provider.py` `test_connection` |
| With a server on `127.0.0.1:11434` answering `GET /api/tags` with `mistral-7b:latest` and `POST /api/generate` with a complete reply, all three tests fail. With nothing listening, all three pass. Without the `POST` handler, the `generate` test passes for the wrong reason: the 501 is a `URLError`, which `generate` turns into `ProviderUnavailableError` (`workmain/ai/providers/ollama.py:116`). | The AC4.1 command in §5, run at `043e8c5` |
| The collected test IDs, with the class part removed, are identical at `3fff87a` and at `402ec1a`. There are 1707 at each. | The AC2.1 command in §5, run with `3fff87a` as its base and `402ec1a` as the branch |
| Suite at `043e8c5`: `1862 passed, 0 failed, 0 skipped`, with 1 xfailed and 3 xpassed, from a bare `pytest` with `.env`'s provider keys set. `pytest --collect-only -q` collects 1866. | Run 20261127 |

## 3. Design rules

- **DR1 — Every test in `tests/` is a method of a plain class.** The class has no base class and no keyword in its `class` statement. Each class is named `Test<Topic>` (`docs/standards/6-testing.md` §6.2). Each test stays in the file it is in.
- **DR2 — No moved test changes what it checks,** except the three Ollama tests (DR4). Each moved test has the same name, decorators and body as at the branch's base. Its arguments are the same after `self`. The only changes are annotations and docstrings, made as the §4 opening states.
- **DR3 — The 82 tests `402ec1a` moves stay in the classes `402ec1a` puts them in,** under the names it gives those classes (design study F3). That grouping is the contributor's work, adopted with the commit (Decision Log, Q2).
- **DR4 — Each of the three Ollama tests makes the availability check fail within its own body,** so it reaches no network address, and its result is the same whatever listens on `localhost:11434`. What each test asserts is unchanged. How the failure is set up is below the contract.

Anything this spec does not decide is a departure: `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Every line a step changes passes `python3 automation/style_check.py` in that step's commit, and a re-indented line counts as changed. That is the one change a moved line may get beyond its indentation: the annotations and docstring layout the check requires, and nothing more (DR2).

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `402ec1a` on the branch, carrying `dev`'s test bodies and the style check's annotations | `tests/test_provider_foundation.py`, `tests/test_ai_foundation.py`, `tests/test_ai_providers_live.py`, `tests/test_cli_logging.py`, `tests/test_compare_providers.py` |
| 2 | The four tests in command test files move into plain classes | `tests/test_cost_display.py`, `tests/test_meetings_merge.py`, `tests/test_meetings_reschedule.py`, `tests/test_notes_add.py` |
| 3 | The three Ollama tests set up the unavailability themselves | `tests/test_provider_foundation.py` |
| 4 | Results artifact | `docs/dev/results/TEST_CLASSES_RESULTS.md` |

### Step 1 — the contributor's move

`git fetch origin pull/290/head`, then `git cherry-pick 402ec1a`. Resolve the two conflict hunks by keeping `402ec1a`'s deletion of the originals. Then, before the commit:

- Each of the 5 moved tests §2 names gets the body it has on this branch's base. This is the change `f6667a2` made to the original, which the conflict does not carry.
- Every line the style check flags gets what it requires (§4 opening).

The commit keeps `402ec1a`'s author. Its subject is reworded to the `docs/standards/2-git.md` §2.4 form, and its body keeps `402ec1a`'s `Signed-off-by:` line. The body states that the move and the class grouping are the author's, cites `402ec1a` and #290, and lists what the commit adds beyond `402ec1a`: the five bodies from `f6667a2`, and the annotations and docstring layout the style check required.

The AC2.2 command prints only the 4 tests Step 2 moves, each as `MISSING`.

### Step 2 — the four command-file tests

Under DR1 and DR2, each of `test_costs_usage_error_exits_2_on_stderr` (`tests/test_cost_display.py`), `test_merge_keeps_moved_notes_when_the_delete_prompt_is_cancelled` (`tests/test_meetings_merge.py`), `test_reschedule_keeps_the_approved_updates_when_a_later_prompt_is_cancelled` (`tests/test_meetings_reschedule.py`) and `test_t12_note_persists_when_the_time_entry_prompt_is_cancelled` (`tests/test_notes_add.py`) becomes a method of a plain class in its own file. Whether it joins an existing plain class there or a new one, and the class's name, are below the contract. It does not join a `unittest.TestCase` class, because DR1 requires a plain one.

The AC1.1 and AC2.2 commands print nothing.

### Step 3 — the Ollama tests

Under DR4, for `test_ollama_provider_generate_raises_unavailable`, `test_ollama_provider_test_connection_returns_false` and `test_ollama_provider_check_availability_returns_unavailable`, in the class Step 1 puts them in.

This is the defect fix, so the step runs the AC4.1 command before the change, where it reports 3 failed, and after it, where it reports 3 passed (`.claude/skills/session-start/references/anvil.md` § Working rules). The commit body records both runs.

### Step 4 — results artifact

`docs/dev/results/TEST_CLASSES_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. Under "Defect shown before the fix" it records Step 3's two AC4.1 runs. It also records the AC1.1 command's two runs: 86 lines before Step 1, and nothing after Step 2.

### Close-out

`/closeout` opens this branch's pull request to `dev`. Then Ray edits that pull request's description to credit #290's author for the move. Ray closes #290 with a comment linking the new pull request. Neither is a step of this spec, and neither is an authorization point: closing a pull request deletes nothing (`docs/standards/1-workflow.md` §1.4).

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every test in `tests/` is defined in a class | The AC1.1 command below, the issue's own, printing nothing. It prints 86 lines at the **Read at:** commit. |
| AC1.2 | Every test that was module-level at the branch's base is a method of a plain class in the same file (DR1) | The AC2.2 command below printing no `NOT PLAIN` and no `MISSING` line |
| AC2.1 | No test is lost or added: the suite collects the same tests, by file, name and parameters, as the branch's base | The AC2.1 command below printing nothing, and `pytest --collect-only -q \| tail -1` reporting the same count on the branch as on its base (1866 at the **Read at:** commit) |
| AC2.2 | No moved test changes what it checks, apart from the three Ollama tests (DR2) | The AC2.2 command below printing no `CHANGED` line. It compares each moved test with its original at the branch's base, after removing `self`, annotations and docstrings. It reports the 5 `f6667a2` bodies as `CHANGED` when run against `402ec1a` (§2), so it can catch a body the conflict lost. |
| AC3.1 | The full suite passes | A bare `pytest` reporting 0 failed, with the passed, skipped, xfailed and xpassed counts equal to the baseline in §2 when run with the same `.env` |
| AC4.1 | The three Ollama unavailability tests pass whatever listens on `localhost:11434` (DR4). The issue body gains this as its fourth criterion at close-out. | The AC4.1 command below reporting `3 passed`. It serves a model list naming the tests' model, and a complete reply, on `127.0.0.1:11434`, which makes all three fail at the **Read at:** commit (§2). A bare `pytest` with nothing listening, AC3.1, covers the other case. |

**AC1.1 command** (the issue's), run from the repository root:

```bash
python3 -c "import ast,pathlib; [print(f'{p}:{n.lineno} {n.name}') for p in sorted(pathlib.Path('tests').rglob('test_*.py')) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test')]"
```

**AC2.1 command**, run from the repository root. It collects the base in a temporary worktree and removes the class part of every test ID:

```bash
collect() { (cd "$1" && pytest --collect-only -q -p no:cacheprovider 2>/dev/null | grep '::' | sed -E 's/::[A-Za-z_][A-Za-z0-9_]*::/::/' | sort); }
w=$(mktemp -d) && git worktree add --detach "$w" "$(git merge-base origin/dev HEAD)" >/dev/null 2>&1
diff <(collect "$w") <(collect .); git worktree remove --force "$w"
```

**AC2.2 command**, run from the repository root as `python3 - "$(git merge-base origin/dev HEAD)" HEAD`. The two arguments are the revision whose module-level tests are read, and the revision whose classes are searched for them:

```python
import ast, subprocess, sys
base, head = sys.argv[1], sys.argv[2]
ollama = {"test_ollama_provider_generate_raises_unavailable", "test_ollama_provider_test_connection_returns_false", "test_ollama_provider_check_availability_returns_unavailable"}
def src(rev, p):
    r = subprocess.run(["git", "show", f"{rev}:{p}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""
class Norm(ast.NodeTransformer):
    def visit_arg(self, n): n.annotation = None; return n
    def _fn(self, n):
        n.returns = None
        if n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str):
            n.body = n.body[1:] or [ast.Pass()]
        self.generic_visit(n); return n
    visit_FunctionDef = visit_AsyncFunctionDef = _fn
def norm(fn, drop_self):
    fn = Norm().visit(ast.parse(ast.unparse(fn)).body[0])
    if drop_self: fn.args.args = fn.args.args[1:]
    fn.name = "_"
    return ast.dump(fn)
files = subprocess.run(["git", "ls-tree", "-r", "--name-only", base, "tests/"], capture_output=True, text=True).stdout.split()
for p in sorted(f for f in files if f.rsplit("/", 1)[-1].startswith("test_") and f.endswith(".py")):
    tests = {n.name: n for n in ast.parse(src(base, p)).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")}
    if not tests: continue
    found = {}
    for c in ast.parse(src(head, p) or "").body:
        if isinstance(c, ast.ClassDef):
            for m in c.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name in tests: found[m.name] = (c, m)
    for name, fn in tests.items():
        if name not in found: print(f"MISSING {p} {name}"); continue
        c, m = found[name]
        if c.bases or c.keywords: print(f"NOT PLAIN {p}::{c.name}::{name}")
        if name not in ollama and norm(fn, False) != norm(m, True): print(f"CHANGED {p}::{c.name}::{name}")
```

**AC4.1 command**, run from the repository root with port 11434 free:

```python
import http.server, json, sys, threading
import pytest
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"models": [{"name": "mistral-7b:latest"}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = json.dumps({"response": "ok", "prompt_eval_count": 1, "eval_count": 1, "done_reason": "stop"}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 11434), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", "tests/test_provider_foundation.py", "-k",
    "test_ollama_provider_generate_raises_unavailable or test_ollama_provider_test_connection_returns_false or test_ollama_provider_check_availability_returns_unavailable"]))
```

Run as `python3 - <<'EOF'` with the block above, then `EOF`.

## 6. Test plan

- **Baseline before this work:** `1862 passed, 0 failed, 0 skipped`, with 1 xfailed and 3 xpassed, from a bare `pytest` at `043e8c5` (§2).
- **Expected after:** the same counts. No test is added or removed (AC2.1).
- **Test files:** the nine files §1 lists, changed as Steps 1 to 3 state. No test file is added.

## 7. Risks and rollback

- **A conflict resolution that keeps `402ec1a`'s moved copies leaves the five `f6667a2` bodies out.** The tests then build providers without the rate keys `BaseProvider` requires, and fail. AC2.2 names each such test, and AC3.1 fails on it.
- **Annotating a moved line could change a test.** AC2.2 removes annotations and docstrings before it compares, so any other change shows as `CHANGED`.
- **AC4.1 needs port 11434 free.** If an Ollama server is running on the machine, the stub can't bind and the command errors out instead of giving a result.
- **Rollback:** each step is one commit, and `git revert` of it restores the tests as they were. Reverting Step 1 also removes the contributor's commit from the branch, and #290 still holds it.

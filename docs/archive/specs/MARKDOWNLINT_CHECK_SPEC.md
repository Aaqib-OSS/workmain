# markdownlint Check on Changed Lines — Spec

**Status:** Shipped

**Author:** Spanner

**Date:** 20261125

**Read at:** 271f7ebf6ebe89419b8d19032390fdee2cd90f55

**Branch:** `chore/issue-308-markdownlint-check` (base: `docs/standards/2-git.md` §2.1)

**Target release:** none: a `chore/*` merge carries no version bump, `CHANGELOG.md` entry, tag or Release (§2.2)

**Originating item:** Issue #308

**Design study:** `../design/DESIGN_MARKDOWNLINT_CHECK.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261125 | Spanner | The engine is markdownlint-cli2, the one the editor runs (design study §4, F3) | DR1 |
| 20261125 | Spanner | The check runs inside `automation/style_check.py`, which gives it the changed-line filter, `SKIPPED` and every existing caller (design study §4, F7) | DR3, DR4 |
| 20261125 | Ray | The tools are pinned in `automation/package.json` with its lockfile and installed with `npm ci --prefix automation` (design study Q1, Option A) | DR1, DR2, Step 2, Step 3 |
| 20261125 | Ray | No rule is dropped from the set `.markdownlint.json` applies today (design study Q2) | DR7 |
| 20261125 | Ray | A markdownlint finding is also reported when the line before or after it is a changed line (design study Q3, option (b)) | DR4 |
| 20261125 | Ray | The new tests follow the inline `repo` harness; AC1 is restated (design study Q4) | §5 note on AC1 |
| 20261125 | Ray | The config file names every rule the check enforces, and the one-line-per-paragraph rule is `markdownlint-rule-single-line-paragraphs`, not a rule of our own (design study Q5) | DR6, DR7, Step 2 |
| 20261125 | Ray | Header fields are separated by a blank line (design study Q6) | DR9, Step 1 |
| 20261125 | Caliper | 4, Spec defect, blocking: DR2 and DR5 read exit 1 as "findings" without requiring that any finding was parsed, so a markdownlint-cli2 that fails while loading passes the check silently. `markdownlint-cli2-bin.mjs:5` loads `./markdownlint-cli2.mjs` with a static `import`, outside the `try`/`catch` at `:13-18` that turns errors into exit 2. Run 20261125 in the scratchpad: with `markdownlint` deleted from `node_modules` (a broken install), node exits 1, stderr holds only `ERR_MODULE_NOT_FOUND` and stdout is empty. As specified, that gives zero violations and `PASS`. A Node older than 22 failing at load would take the same path; this was not run. No criterion exercises the case, and AC1.8 and AC2.1 read green either way. Options: (a) exit 1 with no stderr line parsed as a finding stops with `SystemExit` naming stderr; (b) also require the stdout `Summary: <n> issue(s) in <m> file(s)` count to equal the number of findings parsed (forms seen in runs: `0 issues in 0 files`, `1 issue in 1 file`, `6 issues in 1 file`); (c) add `markdownlint-cli2-formatter-json`, which needs a second pinned package and an `outputFormatters` entry the editor ignores. Recommendation: (b), stated in DR2, with a criterion and test that runs a broken install and asserts `SystemExit`. | Accepted, Spanner 20261125. Option (b), widened: DR2 also requires the stdout `Linting:` count to equal the number of paths passed, so a run that linted fewer files than it was given stops too. A broken install, reproduced 20261125 (exit 1, empty stdout), stops with `SystemExit`. AC1.13 and its test added. The finding's "Ray rules on the options" is set aside: a spec defect is Spanner's to fix (`.claude/skills/session-start/SKILL.md` § Role 2) |
| 20261125 | Caliper | 2, Spec defect, non-blocking: Step 2's `repo` fixture links "the repository's `automation/node_modules`", which is the test file's `ROOT`. In a linked worktree that folder does not exist, so the markdownlint tests skip, and §6's "0 skipped" fails. DR2 finds the tool through `_main_worktree()`; the fixture should do the same. Separately, the config copy must be committed in the base commit, not left untracked: AC1.6's linked worktree only holds committed files, and without the config markdownlint-cli2 runs its own default rules. The spec states neither point. | Accepted. Step 2's fixture links `automation/node_modules` from the main working tree of the repository the test file is in, found as DR2 finds it, and commits the config copy in the base commit |
| 20261125 | Caliper | 2 (§1.2 "a criterion's check is one that can produce the answer"), Spec defect, non-blocking: AC1.8 asks for "this spec, the design study, the three templates and the results artifact among its changed files", but `main` prints only the number of changed files (`automation/style_check.py:412-415`). The check needs a command that lists them, such as `git diff --name-only <merge-base>` together with `git ls-files --others --exclude-standard`, or the clause comes out. `PASS` only shows markdownlint ran once the blocking finding above is resolved. | Accepted. AC1.8's check lists the changed files with `git diff --name-only $(git merge-base HEAD main)` and `git ls-files --others --exclude-standard` |
| 20261125 | Caliper | 1, Spec defect, non-blocking: on a `chore/*` (direct path) branch, §1.2 asks each step to quote the text it replaces. Step 2 quotes neither the docstring text DR8 replaces (`automation/style_check.py:6`, `:18`) nor its replacement. It also does not quote the `check` loop it rewrites (`:364-368`), which only §2 cites. Steps 3 and 4 do quote. Either quote these, or record in the Decision Log that this spec takes the full-path form for Step 2. | Accepted. Step 2 quotes the docstring text DR8 replaces and the two `check` blocks it rewrites, each with its replacement. The new `markdownlint_violations` and the deletion of `markdown_violations` and `_BLOCK_START` stay stated by contract and by symbol, as the direct path's precedent `docs/archive/specs/REAL_VALUE_CHECK_SPEC.md` Step 1 does for new code |
| 20261125 | Caliper | 2, Spec defect, non-blocking: the §2 callers row lists four results for the search it names, but the search also returns `docs/standards/3-code.md:5`, as the design study's §2 lists. That line's statement stays true; the row should list it so the evidence matches the search. | Accepted. §2 callers row lists `docs/standards/3-code.md:5` |
| 20261125 | Caliper | 1, Standards gap, non-blocking: §1.1 assumes every direct-path step only copies out text the spec quotes. No standard covers a `chore/*` step that writes new tooling code and its tests. | No issue, Ray 20261125: leave it |
| 20261125 | Caliper | 1, Standards gap, non-blocking: §7 names no location for linter or editor config at the repository root (`.markdownlint-cli2.jsonc`, as with `.markdownlint.json` and `pyproject.toml` today). Only `alembic.ini` has a row. | No issue, Ray 20261125: leave it; §7 had no row for `.markdownlint.json` either |
| 20261125 | Caliper | 1, Standards gap, non-blocking: §6.2 says "A test is a method of a plain class" without saying whether that covers the `automation/` suites. `automation/style_check_test.py` uses module-level functions, and the new tests follow it (design study Q4). | No issue, Ray 20261125: leave it |
| 20261125 | Caliper | 4, Existing defect, non-blocking: `changed_lines` records no line for a pure-deletion hunk: `+N,0` gives `range(N, N)` at `automation/style_check.py:105-107`. A finding a deletion causes is therefore never reported, for example `MD022` after deleting the blank line under a heading, or ruff's equivalent. DR4's next-line rule does not reach it. | No issue, Ray 20261125: leave it until it causes a problem |
| 20261125 | Caliper | Pass at 5a20638, full: 48 items checked, 1 blocking, 8 non-blocking. | n/a |
| 20261125 | Caliper | 2, Spec defect, non-blocking: §2 and DR2 give the stdout forms as `Linting: <n> file(s)` and `Summary: <k> issue(s) in <m> file(s)`. Version 0.24.2 actually prints `Linting: 1 file`, `Linting: 3 files`, `Summary: 0 issues in 0 files`, `Summary: 3 issues in 1 file` and `Summary: 4 issues in 2 files` (run 20261125 in the scratchpad, with Step 2's config, one to three paths). Older markdownlint-cli2 versions printed the `(s)` form literally. An implementer who matches it literally would match nothing and stop every Markdown run. AC1.1's test would fail on that straight away, which is why this doesn't block. The fix is to state the observed singular and plural forms in §2 and DR2. | Accepted. §2 and DR2 state the forms the tool prints: `Linting: 1 file` or `Linting: <n> files`, and `Summary: 1 issue in …` or `Summary: <k> issues in …`, with `<m> file` or `<m> files` after `in`. The first pass's resolution text is updated to match |
| 20261125 | Caliper | 2 (§1.2, a criterion names the property), Spec defect, non-blocking: DR2 now has three stop conditions: no `Linting:` line, `<n>` not equal to the paths passed, and `<k>` not equal to the findings parsed. AC1.13's stub exits 1 with nothing on stdout, so only the first condition fires. The `<k>` check is what catches a parser that misses findings, for example after a version bump changes the finding format. No criterion tests it or the `<n>` check, so an implementation that leaves both out still turns every criterion green. The fix is a second AC1.13 case: a stub that prints `Linting: 1 file` and `Summary: 1 issue in 1 file`, with a stderr line not in the finding form, and the test asserts `SystemExit`. If that adds a test, update AC1.10 and the §6 counts to match. | Accepted. AC1.13's test is parametrized over three stubs, one for each DR2 stop condition: nothing on stdout; `Summary` counting a finding that stderr does not hold in the finding form; `Linting` counting a file more than was passed. AC1.10 and §6 count 142 |
| 20261125 | Caliper | 1, Spec defect, non-blocking: Step 2 rewrites `check`'s filter (DR4) but leaves its docstring line `Every violation whose span includes a changed line, sorted by path and line.` (`automation/style_check.py:354`). That line becomes false for a markdownlint finding next to a changed line. On the direct path every replaced line is quoted, and Step 2 quotes neither this line nor its replacement. | Accepted. Step 2 quotes `check`'s `Returns:` line and its replacement |
| 20261125 | Caliper | Pass at f5a7f3b, changes since 5a20638: 21 items checked, 0 blocking, 3 non-blocking. | n/a |
| 20261125 | Caliper (post-implementation) | No findings. | n/a |

---

## 1. Scope

**In scope:**

- `.markdownlint-cli2.jsonc` replaces `.markdownlint.json`, naming every rule the check enforces, `single-line-paragraphs` among them.
- `automation/style_check.py` runs markdownlint-cli2 over the Markdown files a branch changed, and reports each finding on a changed line or next to one. Its own hard-wrap check, `markdown_violations`, is removed.
- `automation/package.json` and `automation/package-lock.json` pin the tools. `.gitignore` ignores `automation/node_modules/`.
- `automation/style_check_test.py` covers the check.
- The three `docs/dev/*/_TEMPLATE_*.md` and the 14 `automation/fixtures/closeout_*` Markdown files take the blank-line header form.
- `.github/workflows/tests.yml` job `style` installs Node and the tools before it runs the check.
- `docs/standards/1-workflow.md` §1.5 names the config file and the check.

**Out of scope:**

- The 96 markdownlint findings already in live Markdown (design study F5), the two real wraps in `automation/fixtures/standards_missing_label_pair.md` and `config/providers/_template/models/README.md` (F14), and everything in `docs/archive/` (F6). They are fixed when a branch touches them, as #297's design brings code up to the rules.
- Renamed files: a file the branch renamed and edited is not checked, by this check or any other in the module. That is #277.
- Running the `automation/` suite in CI (design study F12).
- `README.md`'s install steps. The check's stop message names the install command (DR2), as ruff's does.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `check(changes, values)` keeps a violation only where its span `(first, last)` includes a changed line, or where its file maps to `None` (new or untracked). `main` prints each kept violation as `<path>:<line> — <message>`, indented two spaces | `automation/style_check.py:342` `check`, `:416` `main` |
| `check` runs `markdown_violations` on every changed path ending `.md` that exists. `markdown_violations` and `_BLOCK_START` have no other caller; the tests call `markdown_violations` through `_wrapped` | `automation/style_check.py:48`, `:289`, `:364-368`; `git grep -n 'markdown_violations\|_BLOCK_START'` |
| `python_violations` finds ruff with `shutil.which`, stops with `SystemExit` when ruff is missing or exits other than 0 or 1, and runs only when there are Python paths | `automation/style_check.py:222-257` |
| `changed_lines` drops `SKIPPED` paths: `CHANGELOG.md`, `docs/archive/`, `scripts-deprecated/`, `staging/` | `automation/style_check.py:38`, `:112` |
| `_main_worktree()` returns the main working tree's root from any linked worktree; `main` reads `.env` from it | `automation/style_check.py:65`, `:408` |
| The module docstring states what is checked and `Requires git, ruff and python-dotenv.` | `automation/style_check.py:1-21` |
| `.markdownlint.json` is the repository's only markdownlint config, and §1.5 its only citation outside `docs/archive/` | `.markdownlint.json`; `git grep -n -i markdownlint -- . ':!docs/archive'` |
| markdownlint-cli2 0.24.2 (markdownlint 0.42.2) is what the editor runs, and needs Node 22 or later. It finds `.markdownlint-cli2.jsonc` in its working directory | design study F3, F4; `markdownlint-cli2 --help` |
| markdownlint-cli2 prints each finding to stderr as `<path>:<line>[:<column>] error <rule names> <description>[ [<detail>]]`, and progress to stdout. It exits 0 with no findings, 1 with findings, 2 on an error it catches. A failure while loading, such as a broken install, also exits 1, with nothing on stdout. A run that lints prints `Linting: 1 file` or `Linting: <n> files`, and `Summary: 1 issue in …` or `Summary: <k> issues in …` (`<m> file` or `<m> files` after `in`; `0 issues in 0 files` with none), to stdout. A path prefixed with `:` is read literally | run 20261125 in the scratchpad |
| The config Step 2 quotes, with `"default": false` and 48 rules named, reports the same 96 findings as `.markdownlint.json` over the live Markdown, line for line, plus `single-line-paragraphs` | design study F18 |
| `single-line-paragraphs` reports a soft-wrapped paragraph on its first line and on every continuation line, and reports consecutive `**Field:** value` header lines. With a blank line between fields it reports nothing | design study F14, F15 |
| Named by package in `customRules`, the rule is found next to the markdownlint-cli2 that runs it, from a worktree with no `node_modules`; a `modulePaths` entry that does not exist is not an error | design study F17 |
| Every reader of a header field reads one line, so a blank line between fields changes none of them | design study F16 |
| The `repo` test fixture builds a temporary repository at `tmp_path` and points `sc.ROOT` at it. Its base `docs/guide.md` holds a wrapped paragraph at lines 3–4. `test_a_wrapped_line_added_to_an_existing_document_is_reported` asserts the whole violation list | `automation/style_check_test.py:56`, `:69`, `:242` |
| The tests of `markdown_violations` alone: `test_a_paragraph_broken_across_lines_is_hard_wrapped`, `test_a_list_item_broken_across_lines_is_hard_wrapped`, `test_blocks_of_their_own_are_not_wrapping`, `test_fenced_code_and_front_matter_are_not_checked`, `test_a_line_after_an_explicit_break_is_not_wrapping` | `automation/style_check_test.py:130-161` |
| pytest's default `norecursedirs` and ruff's default exclusions both include `node_modules` | pytest and ruff defaults; `pyproject.toml:1-8` sets neither |
| `.github/workflows/tests.yml` job `style` sets up Python and installs ruff and python-dotenv; it sets up no Node | `.github/workflows/tests.yml:86-137` |
| `actions/setup-node` v7.1.0 is commit `949feb2413d6458794dcd2491c4babbbce0c15c1` | `gh api repos/actions/setup-node/git/ref/tags/v7.1.0`, 20261125 |
| Callers of `style_check.py`: `.claude/skills/closeout/SKILL.md:35` (P7), `.claude/skills/session-start/references/anvil.md:46` (step 5), `.claude/skills/session-start/references/caliper.md:52` (I6, `--base`, detached worktree), `.github/workflows/tests.yml:135`. `docs/standards/3-code.md:5` describes the module, and stays true. No caller's command line changes | `git grep -n style_check -- . ':!docs/archive' ':!automation/style_check*.py'` |
| `pytest automation/`: 138 passed, 0 failed, 0 skipped | run 20261125 |

## 3. Design rules

- **DR1 — The tools and their versions.** markdownlint-cli2 `0.24.2` and markdownlint-rule-single-line-paragraphs `0.2.0`, exact, in `automation/package.json` `devDependencies`, with the whole tree pinned by `automation/package-lock.json`.
- **DR2 — Where the tool is found.** `<main working tree>/automation/node_modules/.bin/markdownlint-cli2`, where the main working tree is `_main_worktree()`, so a linked worktree such as Caliper's I6 uses the main tree's install, as it uses the main tree's `.env`. When there are Markdown paths to check and that file does not exist, the check stops with `SystemExit("markdownlint-cli2 was not found (npm ci --prefix automation)")`. The check stops with `SystemExit` naming markdownlint-cli2's stderr when it exits other than 0 or 1, when its stdout `Linting: 1 file` or `Linting: <n> files` line is missing or its count is not the number of paths passed, or when its stdout `Summary: 1 issue` or `Summary: <k> issues` line is missing or its count is not the number of findings parsed. A markdownlint-cli2 that fails while loading exits 1 with nothing on stdout, so only these counts tell it from a run with findings (Decision Log, Caliper).
- **DR3 — Which files.** Every changed path ending `.md` that exists, after `SKIPPED`, passed in one run, each prefixed with `:`, with `ROOT` as the working directory, so markdownlint-cli2 reads `ROOT/.markdownlint-cli2.jsonc` as the editor does. No `--config` is passed.
- **DR4 — Which findings are reported.** A markdownlint finding is reported when its line, the line before it or the line after it is a changed line, or when its file is wholly changed. It is printed at the line markdownlint reports. Every other violation keeps the existing changed-line filter.
- **DR5 — The report.** Each finding is printed in the existing form, `<path>:<line> — <message>`, where `<message>` is markdownlint's text after `error` and the space that follows it. It counts in the summary line's violation total and in the exit code.
- **DR6 — One engine for Markdown.** `markdown_violations` and `_BLOCK_START` are removed. One line per paragraph is enforced by `single-line-paragraphs`.
- **DR7 — The config shows what is checked.** `.markdownlint-cli2.jsonc` sets `"default": false` and names every rule it enforces, each with its rule name in a comment. A rule not named there is not run. `.markdownlint.json` is deleted.
- **DR8 — The docstring states the dependency.** The module docstring says Markdown lines are checked with markdownlint-cli2 against `.markdownlint-cli2.jsonc`, and that the check requires Node 22 or later and the tools installed with `npm ci --prefix automation`.
- **DR9 — Header fields.** In a template or fixture this spec changes, each `**Field:** value` line that is followed by another is followed by a blank line instead. No field's text changes.

## 4. Steps

| Step | Deliverable | Files | ACs |
| --- | --- | --- | --- |
| 1 | The blank-line header form: DR9 | `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/design/_TEMPLATE_DESIGN.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, the 14 files `git ls-files 'automation/fixtures/closeout_*.md' 'automation/fixtures/closeout_*/*.md'` lists | AC1.11 |
| 2 | The pinned tools, the config, the check and its tests: DR1–DR8 | `automation/package.json`, `automation/package-lock.json`, `.gitignore`, `.markdownlint-cli2.jsonc`, `.markdownlint.json` (deleted), `automation/style_check.py`, `automation/style_check_test.py` | AC1.1–AC1.7, AC1.9, AC1.10, AC1.13 |
| 3 | CI installs Node and the tools | `.github/workflows/tests.yml` | AC2.1 |
| 4 | §1.5 names the config and the check | `docs/standards/1-workflow.md` | AC3.1 |
| 5 | The results artifact | `docs/dev/results/MARKDOWNLINT_CHECK_RESULTS.md` | AC1.8, AC1.12, all |

Step 1 comes first so that, once Step 2 turns the rule on, no file this branch adds or touches carries the old header form. Every addition lives in `automation/` or at the repository root beside the config it replaces: `docs/standards/7-file-placement.md` §7 assigns dev tooling to `automation/`, `docs/ARCHITECTURE.md` does not map it, and `automation/style_check.py` owns checking a branch's changed lines (design study §4).

**Step 1.** In each file Step 1 lists, insert a blank line after every line matching `^\*\*[^*]+:\*\*` whose next line also matches it, per DR9. `pytest automation/` stays at 138 passed.

**Step 2.**

- `automation/package.json`, per DR1:

  ```json
  {
    "private": true,
    "devDependencies": {
      "markdownlint-cli2": "0.24.2",
      "markdownlint-rule-single-line-paragraphs": "0.2.0"
    }
  }
  ```

- `automation/package-lock.json` is the file `npm install --prefix automation` writes from that `package.json`, committed unedited.
- `.gitignore` gains a section after its last line, `test_notes-*.md`:

  ```text

  # Node, for automation/ tooling
  automation/node_modules/
  ```

- `.markdownlint.json` is deleted. Its text, replaced in full:

  ```json
  {
      "default": true,
      "MD013": false,
      "MD007": {
          "indent": 2
      },
      "MD024": {
          "siblings_only": true
      },
      "MD033": false,
      "MD041": false
  }
  ```

- `.markdownlint-cli2.jsonc`, per DR7. Its 48 markdownlint rules are the 53 of markdownlint 0.42.2 less `MD013`, `MD033` and `MD041`, off today, and `MD043` and `MD044`, which check nothing without settings the repository does not give (design study F18):

  ```jsonc
  {
    "config": {
      "default": false,
      "MD001": true, // heading-increment
      "MD003": true, // heading-style
      "MD004": true, // ul-style
      "MD005": true, // list-indent
      "MD007": { "indent": 2 }, // ul-indent
      "MD009": true, // no-trailing-spaces
      "MD010": true, // no-hard-tabs
      "MD011": true, // no-reversed-links
      "MD012": true, // no-multiple-blanks
      "MD014": true, // commands-show-output
      "MD018": true, // no-missing-space-atx
      "MD019": true, // no-multiple-space-atx
      "MD020": true, // no-missing-space-closed-atx
      "MD021": true, // no-multiple-space-closed-atx
      "MD022": true, // blanks-around-headings
      "MD023": true, // heading-start-left
      "MD024": { "siblings_only": true }, // no-duplicate-heading
      "MD025": true, // single-title
      "MD026": true, // no-trailing-punctuation
      "MD027": true, // no-multiple-space-blockquote
      "MD028": true, // no-blanks-blockquote
      "MD029": true, // ol-prefix
      "MD030": true, // list-marker-space
      "MD031": true, // blanks-around-fences
      "MD032": true, // blanks-around-lists
      "MD034": true, // no-bare-urls
      "MD035": true, // hr-style
      "MD036": true, // no-emphasis-as-heading
      "MD037": true, // no-space-in-emphasis
      "MD038": true, // no-space-in-code
      "MD039": true, // no-space-in-links
      "MD040": true, // fenced-code-language
      "MD042": true, // no-empty-links
      "MD045": true, // no-alt-text
      "MD046": true, // code-block-style
      "MD047": true, // single-trailing-newline
      "MD048": true, // code-fence-style
      "MD049": true, // emphasis-style
      "MD050": true, // strong-style
      "MD051": true, // link-fragments
      "MD052": true, // reference-links-images
      "MD053": true, // link-image-reference-definitions
      "MD054": true, // link-image-style
      "MD055": true, // table-pipe-style
      "MD056": true, // table-column-count
      "MD058": true, // blanks-around-tables
      "MD059": true, // descriptive-link-text
      "MD060": true, // table-column-style
      "single-line-paragraphs": true // markdownlint-rule-single-line-paragraphs
    },
    "customRules": ["markdownlint-rule-single-line-paragraphs"],
    "modulePaths": ["automation/node_modules"]
  }
  ```

- `automation/style_check.py` gains `markdownlint_violations(paths: list[str]) -> list[Violation]`, which runs the tool per DR2 and DR3 and returns one `(path, line, line, message)` entry per finding with DR5's message, and an empty list for no paths without running the tool. `markdown_violations` and `_BLOCK_START` are removed (DR6). `check`'s and `main`'s signatures are unchanged.
- In `check`, replace:

  ```python
      for path in changes:
          if path.endswith(".md") and (ROOT / path).exists():
              found += markdown_violations(
                  path, (ROOT / path).read_text(encoding="utf-8")
              )
  ```

  with:

  ```python
      nearby = markdownlint_violations(
          [p for p in changes if p.endswith(".md") and (ROOT / p).exists()]
      )
  ```

  and replace its return:

  ```python
      return sorted(
          v
          for v in found
          if changes.get(v[0]) is None
          or any(n in changes[v[0]] for n in range(v[1], v[2] + 1))
      )
  ```

  with, per DR4:

  ```python
      def touched(v: Violation, reach: int) -> bool:
          lines = changes.get(v[0])
          return lines is None or any(
              n in lines for n in range(v[1] - reach, v[2] + reach + 1)
          )

      return sorted(
          [v for v in found if touched(v, 0)] + [v for v in nearby if touched(v, 1)]
      )
  ```

- In the module docstring, per DR8, replace:

  ```text
  Python lines are checked with ruff, configured in pyproject.toml. Python lines
  are also checked for citations of the process that produced them (§3). Markdown
  lines are checked for hard wrapping (docs/standards/1-workflow.md §1.5). Only
  lines the branch added or changed are checked, against the point where it left
  its base branch, so code is brought up to the rules as it is touched rather than
  all at once. Uncommitted and untracked files count as changed. CHANGELOG.md is
  history and is never checked.
  ```

  with:

  ```text
  Python lines are checked with ruff, configured in pyproject.toml. Python lines
  are also checked for citations of the process that produced them (§3). Markdown
  lines are checked with markdownlint-cli2 against .markdownlint-cli2.jsonc
  (docs/standards/1-workflow.md §1.5). Only lines the branch added or changed are
  checked, against the point where it left its base branch, so code is brought up
  to the rules as it is touched rather than all at once; a markdownlint finding on
  the line next to a changed line counts as well. Uncommitted and untracked files
  count as changed. CHANGELOG.md is history and is never checked.
  ```

  In `check`'s docstring, replace `Every violation whose span includes a changed line, sorted by path and line.` with `Every violation whose span includes a changed line, and every markdownlint finding on or next to one (DR4), sorted by path and line.`

  In the module docstring, also replace `Requires git, ruff and python-dotenv.` with `Requires git, ruff, python-dotenv, and Node 22 or later with the tools npm ci --prefix automation installs.`
- `automation/style_check_test.py`:
  - The `repo` fixture writes a copy of the repository's `.markdownlint-cli2.jsonc` into the temporary repository and commits it in the base commit, so a linked worktree of it holds the config. It links `automation/node_modules` from the main working tree of the repository the test file is in, found with `git rev-parse --path-format=absolute --git-common-dir` as DR2 finds it, into the temporary repository's `automation/`, ignored there, so every test runs the real tools against the real config, including when the suite runs in a linked worktree. The base `docs/guide.md` keeps a wrapped paragraph from before the branch, placed so that no test's added lines sit next to it unless the test means them to.
  - The five tests of `markdown_violations` alone that §2 names are removed with it, together with their helper `_wrapped`.
  - `test_a_wrapped_line_added_to_an_existing_document_is_reported`, `test_a_wrapped_line_that_predates_the_branch_is_not_reported` and `test_main_exits_1_on_a_violation_and_0_without` keep their names and what they test, now through `single-line-paragraphs`.
  - Tests that run markdownlint are skipped when it is not installed in the repository, as the ruff tests are skipped without ruff.
  - The new tests are those §5 names.

**Step 3.** In `.github/workflows/tests.yml` job `style`, replace:

```yaml
      # ruff from requirements-dev.txt; python-dotenv at the version requirements.txt pins.
      - name: Install ruff and python-dotenv
        run: |
          pip install -r requirements-dev.txt "$(grep -oE '^python-dotenv==[^ #]+' requirements.txt)"
```

with:

```yaml
      # ruff from requirements-dev.txt; python-dotenv at the version requirements.txt pins.
      - name: Install ruff and python-dotenv
        run: |
          pip install -r requirements-dev.txt "$(grep -oE '^python-dotenv==[^ #]+' requirements.txt)"

      - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version: "24"

      # markdownlint-cli2 and its rule at the versions automation/package-lock.json pins.
      - name: Install markdownlint-cli2
        run: npm ci --prefix automation
```

**Step 4.** In `docs/standards/1-workflow.md` §1.5 **Writing.**, replace:

```text
- **Markdown is written one line per paragraph**, per list item and per table row, and the editor wraps it. `.markdownlint.json` is set to match, and governs all formatting.
```

with:

```text
- **Markdown is written one line per paragraph**, per list item and per table row, and the editor wraps it. `.markdownlint-cli2.jsonc` governs all formatting, and `automation/style_check.py` checks it on every line a branch changes.
```

**Step 5.** The results artifact, per `docs/standards/1-workflow.md` §1.1.

### Authorization points

None.

## 5. Acceptance criteria

Each test named below is in `automation/style_check_test.py`.

AC1 is restated (§1.2; design study Q4). The issue's criterion names `.markdownlint.json`, which DR7 replaces with `.markdownlint-cli2.jsonc`, and its check reads "tests in `automation/` with fixture files", where these tests write their Markdown inline in the `repo` fixture's temporary repository, as the existing tests do. Restated: *a changed Markdown line that breaks a rule `.markdownlint-cli2.jsonc` names is reported by `style_check.py`, and an unchanged line is not; checked by tests in `automation/style_check_test.py`*. The issue body needs that edit at close-out.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A changed Markdown line that breaks a rule the config names fails the style check, and the output names the file, line and rule | `pytest automation/style_check_test.py` passes, including `test_a_markdownlint_finding_on_a_changed_line_is_reported`, which runs `main` on a branch adding a fenced block with no language and asserts exit 1 and `<path>:<line> — MD040/` in the output |
| AC1.2 | A finding on a line the branch did not change, and not next to one, is not reported, so the existing findings do not fail a branch | `test_a_markdownlint_finding_on_an_untouched_line_is_not_reported` passes, with the finding in the base commit and the branch changing a line at least two lines away |
| AC1.3 | A finding reported on the line next to a changed line is reported, so a paragraph added under an existing heading fails | `test_a_markdownlint_finding_next_to_a_changed_line_is_reported` passes, with a paragraph added directly under a heading from the base commit, asserting an `MD022` violation at the heading's line |
| AC1.4 | A rule the config does not name is not run | `test_a_rule_the_config_does_not_name_is_not_reported` passes, with changed lines that only `MD013` (a line over 80 characters) and `MD033` (inline HTML) would report, asserting no violation |
| AC1.5 | With Markdown to check and markdownlint-cli2 not installed, the check stops and names the install command | `test_the_check_stops_when_markdownlint_cli2_is_not_installed` passes, asserting `SystemExit` with `npm ci --prefix automation` in its message |
| AC1.6 | Run in a linked worktree, as Caliper's I6 runs it, the check uses the main working tree's install, `single-line-paragraphs` included | `test_markdownlint_is_found_from_a_linked_worktree` passes, running `main` with `--base` from a linked worktree that has no `automation/node_modules`, on a branch adding a wrapped paragraph, and asserting a `single-line-paragraphs` violation |
| AC1.7 | A paragraph the branch writes across two lines is reported, and one written before the branch is not | `test_a_wrapped_line_added_to_an_existing_document_is_reported` passes, asserting `single-line-paragraphs` violations at the added lines only, and `test_a_wrapped_line_that_predates_the_branch_is_not_reported` passes |
| AC1.8 | On this repository the check runs the config on this branch's Markdown | `npm ci --prefix automation`, then `python3 automation/style_check.py` on this branch prints `PASS`, and `git diff --name-only $(git merge-base HEAD main)` with `git ls-files --others --exclude-standard` lists this spec, the design study, the three templates and the results artifact |
| AC1.9 | Every rule the check reports is one the config names | `node automation/node_modules/.bin/markdownlint-cli2` run from the repository root over every tracked `.md` outside `SKIPPED` reports only rule names that appear as keys in `.markdownlint-cli2.jsonc` |
| AC1.10 | The style-check suite passes, the removed tests being exactly the five §2 names | `pytest automation/` reports 142 passed, 0 failed, 0 skipped: 138, less the five, plus the six AC1.1–AC1.6 name and AC1.13's three cases |
| AC1.11 | No template or closeout fixture holds two consecutive header field lines | `node automation/node_modules/.bin/markdownlint-cli2` over the 17 files Step 1 lists reports no `single-line-paragraphs` finding, and `pytest automation/` passes |
| AC1.12 | The editor reports what the check reports | Ray opens a Markdown file in VS Code, adds a paragraph wrapped across two lines and a fenced block with no language, and reads a `single-line-paragraphs` and an `MD040` warning |
| AC1.13 | A markdownlint-cli2 run whose output does not account for every file and finding stops the check instead of passing it | `test_a_markdownlint_cli2_that_fails_to_load_stops_the_check` passes, parametrized over three stub tools, each exiting 1, asserting `SystemExit` for each: one with nothing on stdout; one printing `Linting: 1 file` and `Summary: 1 issue in 1 file` with a stderr line not in the finding form; one printing `Linting: 2 files` for one path passed |
| AC2.1 | The CI `style` job runs markdownlint as part of the check | The `style` job's log on this branch's pull request shows the `npm ci --prefix automation` step and `automation/style_check.py exit 0` |
| AC3.1 | §1.5 names the config that governs Markdown formatting and the check that enforces it | Ray reads `docs/standards/1-workflow.md` §1.5 **Writing.**, first item, for `.markdownlint-cli2.jsonc` and `automation/style_check.py` |

The command line is the only entry path to the check (§2 callers). AC1.1 and AC1.6 run it through `main`, without and with `--base`; AC2.1 runs it in CI. The editor is a second reader of the config, which AC1.12 covers.

## 6. Test plan

- **Baseline before this work:** `automation/`: 138 passed, 0 failed, 0 skipped (§2). `tests/`: unchanged by this work, which touches nothing under `workmain/` or `tests/`; close-out runs it.
- **Expected after:** `automation/`: 142 passed, 0 failed, 0 skipped, with ruff and the Node tools installed (AC1.10).
- **Test files:** `automation/style_check_test.py`, changed as Step 2 states. Step 1's fixture edits are exercised by the existing `automation/closeout_acs_test.py`.

## 7. Risks and rollback

- **A branch editing a file with existing findings fails on one next to its edit** (DR4). That is the rule working; the line is fixed on the branch. The 7 live files in design study F5 are where this is likeliest.
- **The tools are missing on a machine.** DR2's stop names the install command. After this merges, `npm ci --prefix automation` runs once in the main working tree.
- **A version bump adds rules the config does not name.** With `"default": false` they stay off until named, so a bump changes nothing silently; naming a new rule is a reviewed change to `.markdownlint-cli2.jsonc`.
- **The rule package is young, with one maintainer** (design study F14). It is pinned by the lockfile. If it is abandoned, the pinned version keeps working, and replacing it touches `automation/package.json` and one line of the config.
- **The editor drifts from the check** when the extension updates its bundled markdownlint-cli2. The check follows `automation/package.json`; matching the editor is a version change there.
- **Known limitation: a renamed file is not checked** (§1 Out of scope, #277).
- **Rollback:** revert the step commits. `.markdownlint.json` returns with Step 2's revert, and no caller's command line changes.

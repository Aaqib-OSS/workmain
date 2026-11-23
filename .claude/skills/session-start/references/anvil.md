# Anvil session open

**Role:** `SKILL.md` § Role 3. **Target:** a spec path, required.

## Reads, in order

1. The spec at the target path, end to end.
2. The spec's `**Status:**` field.
3. `git status --porcelain`
4. `git branch --show-current`, against the first backtick-quoted name in the spec's `**Branch:**` field.
5. Every reference the spec makes, at the cited location. A reference resolves when the location holds what the spec says it holds:
   - **Path** — exists on the current branch.
   - **Symbol** — defined in the file the spec names, as a `def`, a `class` or an assignment, with the signature the spec gives where it gives one.
   - **Line or line range** — holds the text or symbol the spec says it holds.
   - **Quoted text a step replaces or edits** — occurs verbatim in the file named, as many times as the step says, and once where it does not say.
   - **Section** — the file named has the heading, and the section says what the spec says it says.
   - **Reference to another part of the spec** — a step's citation of another section of the same spec, or of an item that section gives an ID: the section exists, and each item cited is there and is what the step says it is.
   - **Claim about existing behaviour** — a §2 row, or a statement of what code does: the evidence it cites is read and shows the claim.
   - **Test node** — `pytest --collect-only -q <node>` collects it.
   - **Issue** — `gh issue view <N>` returns it, in the state the spec gives where it gives one.
   - **Command** — run only if it only reads, such as `grep`, `git grep`, `git show` or `gh issue view`, and resolved when it exits 0, 1 from `grep` or `git grep`, which means no match, or the exit status the spec states it gives before the work. Any other exit status is a discrepancy. Its output is compared with the spec only where the spec says what it prints before the work; output a criterion states for after the work waits for that criterion's check. A command that writes is resolved through each path, symbol and test node it names, under this list.

   A path, symbol or test node that a step creates resolves against that step's deliverable instead, and is a discrepancy if it already exists.
6. `docs/standards/README.md`, then every section its § Sections table names for the work the spec's steps do, end to end.

## Emits

- **Steps** — the spec's §4 step table, as written.
- **Discrepancies** — each of these that holds, or `none`:
  - `Status:` is not `Approved`
  - the working tree is not clean, with each path `git status --porcelain` lists
  - the current branch is not the spec's `**Branch:**`
  - a reference that does not resolve, or resolves to something other than what the spec says is there

Every read runs, and the run reports every discrepancy it finds. What happens next — waiting for Ray's go-ahead, and what it authorizes — is `SKILL.md` § Role 3.

## Working rules

These hold for the whole Anvil session.

- **Each step runs in this order.** A difference from the contract that any check finds is a departure, and stops the step under `SKILL.md` § Role 3.
  1. Before the step's first change, re-read the step's row and text in the spec, and every design rule and acceptance criterion that governs it.
  2. Make the change. Each decision below the contract, with what else was considered and why, goes into the body of the step's commit (`docs/standards/2-git.md` §2.4). For a defect fix, the test that shows the defect is run before the fix, where it fails, and after it, where it passes, and the commit body records both runs. The results artifact copies both from the step commits at the last step.
  3. Stage only the files written for the step (`docs/standards/2-git.md` §2.4), and compare `git diff --cached --name-only` with the step's entry in the Files column. A staged file the entry does not name, or a named file that is not staged, is a difference.
  4. Read `git diff --cached` against the step's text. Anything the step delivers that the diff does not, or a change to the contract the step does not name, is a difference.
  5. Run `python3 automation/architecture_check.py` and `python3 automation/style_check.py`. A new architecture finding is a departure; a style violation is fixed before the commit.
  6. Commit when checks 3 to 5 all pass.
  
# <Title> — Implementation Results

**Status:** Active | Shipped | Superseded
**Author:** Anvil (Role 3) | Spanner (Role 1)
**Date:** YYYYMMDD
**Spec:** `../specs/<file>_SPEC.md`
**Released as:** vX.Y.Z (tag vX.Y.Z) | `n/a`

> Delete this block before use.
>
> **Filename:** `<SUBJECT>_RESULTS.md`, named as `docs/standards/1-workflow.md` §1.5 states.
>
> The implementing role writes this file as its last implementation step (§1.1 Implementation); it records what actually happened, where the spec records what was intended.
>
> **Released as:** the version and tag, which close-out computes from §2.5 and `workmain/__version__.py` before the merge commits this file. `n/a` on `chore/*`, which §2.2 gives no release. The PR number, the Release URL and the confirmed restart timestamp come later, and the issue's closing comment carries them.
>
> Templates are advisory (§1.5).

---

## 1. Summary

What shipped, in a paragraph, stating plainly whether the work is complete or partial. Partial is a legitimate outcome, reported as partial.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | | | +N |
| 2 | | | +N |

## 3. Acceptance criteria

Every AC on the **approved spec**, by identifier, checked against **delivered code**. Close-out checks that every spec AC has a row and that every row is `Met`, or `Carried` with its follow-up issue, and takes the implementer's judgement as recorded. A check that names Ray stays `Not met`, with `Awaiting Ray` as its evidence, until he records it (§1.2).

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met / **Not met** / Carried | `pytest ...` output, file:line, or command result |
| AC1.2 | **Not met** | `Awaiting Ray`: <what he reads or runs> |

Close-out reads every three-column table under `## 3.` as AC rows (`automation/closeout_acs.py`), so this section holds the AC table alone. A supporting table goes under `## 5. Verification`, and the AC row cites it.

Each unmet AC is listed here and carried to an issue, cited by its number: an open issue that already covers it where one exists (§1.3).

## 4. Deviations and decisions

Every departure (`.claude/skills/session-start/SKILL.md` § Role 3) is listed here with how it was handled and resolved, and who resolved it. `Step stopped at` holds one of three values:

- **The step number** — the implementer stopped there, before the step's commit. `Resolution` is what Ray decided; `Resolved by` is `Ray, <date>`.
- **`within approved meaning`** — Role 1 only, on its own direct-path spec: a wording or mechanical change made within the meaning, scope and file set Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules). `Resolution` is the change; `Resolved by` is `Role 1, <date>`.
- **`none`** — the change was made without the stop it required, an unstopped departure (§1.1 Implementation review). It is listed so the record shows it. `Resolution` is what was done; when the row is written, and what `Resolved by` holds, is `SKILL.md` § Role 3.

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

**Decisions below the contract.** Each choice the spec left to the implementer (`.claude/skills/session-start/SKILL.md` § Role 3), recorded as it was made.

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |

## 5. Verification

Counts are recorded in the form `docs/standards/6-testing.md` §6 states. Close-out completes the suite results and live verification (`.claude/skills/closeout/SKILL.md`).

- **Test suite:** <passed> passed, <failed> failed, <skipped> skipped (baseline: the spec's §6 baseline).
- **Defect shown before the fix** (defect fixes only, `.claude/skills/session-start/references/anvil.md` § Working rules): each test that shows the defect, with its run before the fix (failed) and after (passed).
- **Live verification:** what was exercised against the running system, and when.

## 6. Follow-ups

Issues this work created or added to, including findings parked or joined to an open issue (§1.3 Findings and parked issues), and any item deliberately left for later.

| Item | Description | Why deferred |
| --- | --- | --- |

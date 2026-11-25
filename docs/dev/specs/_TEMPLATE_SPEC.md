# <Title> — Spec

**Status:** Draft | Approved | Shipped | Superseded

**Author:** Spanner

**Date:** YYYYMMDD

**Read at:** <commit SHA §2 was verified at>

**Branch:** `<type>/issue-<N>-<slug>` (base: `docs/standards/2-git.md` §2.1)

**Target release:** vX.Y.Z

**Originating item:** Issue #N

**Design study:** `../design/<file>.md` | `n/a` (direct path, where no recon ran)

> Delete this block before use.
>
> **Filename:** `<SUBJECT>_SPEC.md`, named and pointed to as `docs/standards/1-workflow.md` §1.5 states.
>
> **Direct path** (`chore/*`, §1.1): §2 Verified current state is left out, and each step quotes the text it replaces inline. §6 Test plan is optional where every file the change touches lies outside `tests/`, `automation/`, `workmain/`, `config/` and `templates/`; close-out runs the suites regardless. Every other section stays, in this one template.
>
> Templates are advisory (§1.5).

---

## Decision Log

Decisions and review findings, each with its resolution (§1.5). Record a finding that was rejected, and why, so the next reviewer sees it settled.

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| YYYYMMDD | <one of: Ray, Spanner, Caliper, Caliper (post-implementation), Anvil> | | Accepted / **Not taken** — <why> |

Source is written exactly as listed: §1.1's done conditions match `Caliper` and `Caliper (post-implementation)` by their exact text.

---

## 1. Scope

**In scope:** what this spec changes, specific enough that an implementer can tell whether a given file is covered.

**Out of scope:** what it leaves as it is, and why. Caliper checks scope creep against this list, so each nearby area the work could reach is named here.

## 2. Verified current state

What exists today, verified against source at the **Read at:** commit, citing file and symbol (§1.2). Where a claim was carried in from an earlier document rather than re-checked, mark it as carried in.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Call sites of `<symbol>`, found by `grep -rn '<pattern>' --include='*.py' .` | each `file:line` the search returns that is confirmed a call site |

The call-sites row is for a contract change (§1.2).

## 3. Design rules

Numbered invariants the implementation holds to. A step that cannot hold a design rule, and a case no design rule decides, are departures, handled as §1.1 Implementation states.

- **DR1 —**
- **DR2 —**

## 4. Steps

Written as §1.2 states, run as §1.1 Implementation states. Each step states its contract and the owner of each new thing it adds (`.claude/skills/session-start/SKILL.md` § Role 1); what is below the contract is the implementer's.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | | |
| 2 | | |

### Authorization points

Each authorization point this spec contains (§1.4), with the step it falls in and exactly what will happen. Where there are none, write `None`.

## 5. Acceptance criteria

Each criterion is a property of the delivered system, checked by running something or, for a property of a document, by Ray's stated reading (§1.2). Sub-ACs map to the originating issue's ACs as `ACn.m`. A criterion that verifies changed behaviour names the entry path it exercises (§1.2).

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | <property of the delivered system> | `pytest tests/test_x.py` passes, with a test showing <behaviour> |
| AC1.2 | Every Python module under `workmain/` leaves version history to git (`docs/standards/3-code.md` §3.1) | `grep -rn '^Version:' workmain/ --include='*.py'` returns zero hits |
| AC1.3 | <property of a document> | Ray reads <section> for <what> |

Naming the property is what makes AC1.2 reviewable: renaming the header to `Ver:` passes the check and fails the property.

## 6. Test plan

Counts are recorded in the form `docs/standards/6-testing.md` §6 states.

- **Baseline before this work:** <passed> passed, <failed> failed, <skipped> skipped, from a bare `pytest` at the **Read at:** commit.
- **Expected after:** <passed> passed, <failed> failed, <skipped> skipped.
- **Test files:** the proposed files to add or change, and what each covers, written as §6.2 states and placed as §7 states.

## 7. Risks and rollback

What could go wrong, what the blast radius is, and how to undo each step.

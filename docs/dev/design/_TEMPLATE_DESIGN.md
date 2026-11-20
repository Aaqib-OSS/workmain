# <Title> — Design Study | Recon

**Status:** Active | Shipped | Superseded
**Kind:** Design study | Recon
**Author:** Spanner (Role 1)
**Date:** YYYYMMDD
**Read at:** <commit SHA the read was taken at>
**Originating item:** Issue #N | Ray request, YYYYMMDD

> Delete this block before use.
>
> **Filename:** `DESIGN_<SUBJECT>.md` for a design study, `RECON_<SUBJECT>.md` for a recon, named as `docs/standards/1-workflow.md` §1.5 states.
>
> **Two kinds, one template.** A recon reports findings (§1.1 Recon). A design study adds §4, the governing rules and the options with a recommendation. Pick one in the Kind field and keep the sections it uses.
>
> Templates are advisory (§1.5).

---

## 1. Purpose

The question this document answers, and why it is asked now. One paragraph. A recon states its read-only contract here (§1.1 Recon).

## 2. Scope of the read

What was examined, named as files, trees and surfaces, with the searches §1.1 Recon runs. Name each area left out, so a reader can tell an area covered from one unexamined.

## 3. Findings

Verify each finding against source at the **Read at:** commit (§1.2). Each claim the issue body makes is a finding to re-check (§1.3).

- Quote verbatim where the exact wording matters.
- Where a finding cites two files, say which one has the problem and which is there for contrast.

| # | Finding | Evidence (file:line, symbol) |
| --- | --- | --- |
| F1 | | |

Mark a claim the read could not verify as unverified, so the reader sees the gap.

## 4. Governing rules and options *(design study)*

**Governing rules.** The owner `docs/ARCHITECTURE.md` names for what changes, and each standard that applies, cited. The options are judged against these.

For each option that survives the findings and the governing rules: what it is, what it costs, and what it closes off.

### Option XX — <name>

- **Approach:**
- **Pros:**
- **Cons:**

**Recommendation:** <which, and why>, argued from the governing rules above.

## 5. Open questions

Numbered, so answers can be cited later (`Q3 answered YYYYMMDD: ...`). Each is a question whose answer changes the work, and it says whether the problem it asks about is real before framing it.

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | | |

## 6. Disposition

What happened to this study. Filled in when the work lands:

- Promoted to: <`../specs/<file>_SPEC.md`, a change to `docs/ARCHITECTURE.md`, or issue #N>
- Superseded by: <filename, if applicable>

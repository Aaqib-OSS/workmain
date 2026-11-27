# A check that displays as written — Design Study

**Status:** Active

**Kind:** Design study

**Author:** Spanner

**Date:** 20261127

**Read at:** 48419d5e982239ac9d8cb6475b7e55c3b14ba692

**Originating item:** Issue #284

---

## 1. Purpose

GitHub displays an issue's body as Markdown, and a check written outside backticks can display differently from what it states: escapes, placeholders and emphasis markers vanish. A reader who copies the displayed check runs a different command. This study answers the three questions in #284's Fix in mind:

- how `automation/issue_validator.py` judges how a check will display
- whether the rule "a check's command is written in backticks" is enforced by the validator, or left to the written rule and review
- what the one-time sweep of open issues covers

The body of #284 was rewritten on 20261127, to the §1.3 form, before this study was re-based on it. The body it replaced was written before `a7b8fe7` (20261119) rewrote §1, and cited §1.2 text that no longer exists. GitHub's edit history holds the earlier body.

The read was read-only. The only things run were `gh issue list`, `gh api -X POST /markdown` over each open issue's body, and measurement scripts kept in the session scratchpad.

## 2. Scope of the read

- **Source the work changes:**
  - `automation/issue_validator.py`, `automation/issue_validator_test.py`, `automation/fixtures/`
  - `docs/standards/1-workflow.md` §1.2
  - `docs/dev/specs/_TEMPLATE_SPEC.md` §5
  - the bodies of open issues
- **Checks that enforce a rule the work touches** (§7 locations): `automation/issue_validator.py` `validate_criterion_rule` enforces the §1.2 criterion rule on an issue file. No file in `.github/workflows/` or `.githooks/` reads issue text. `automation/closeout_acs.py` reads a spec's criteria at close-out, not an issue's checks.
- **Every statement of the rule:** `git grep -n -i "checked by" -- docs/standards .claude docs/dev` returns `docs/standards/1-workflow.md:59` (the §1.2 criterion form), `docs/standards/1-workflow.md:60` and `docs/dev/specs/_TEMPLATE_SPEC.md:79`. Every caller of the validator: `git grep -n issue_validator -- . ':!docs/archive'` returns `docs/standards/1-workflow.md:90` (§1.3, issue creation) and the validator's own test.
- **Issues by file** (§1.3):
  - `automation/issue_validator.py` → #284
  - `automation/issue_validator_test.py` → #284
  - `docs/dev/specs/_TEMPLATE_SPEC.md` → #245, #284. #245 asks how a direct-path spec quotes replacement text, which this work does not touch.
  - `docs/standards/1-workflow.md` → 24 issues. They cite §1 sections, mostly from inside their own checks, and none is about how a check displays. #295 is the one `parked` issue among them (Q4).

  The term searches `backticks` and `"Checked by" render` add nothing beyond #284.
- **Measurement:**
  - **Snapshot:** all 135 open issues, taken at the read commit's time. Each body was rendered through `gh api -X POST /markdown -f mode=gfm -f context=lockdwn20/workmain`.
  - **Comparison:** each check's rendered text against its source with backticks removed, in both forms (F3).
  - **The two standard files:** the lines of `docs/standards/1-workflow.md` §1.2 and `docs/dev/specs/_TEMPLATE_SPEC.md` §5 were rendered the same way.
- **Left out:** closed issues; artifacts in `docs/archive/`; Markdown elsewhere in the repository. GFM's emphasis rules were not read beyond what the measurement exercised (F7).

## 3. Findings

| # | Finding | Evidence (file:line, symbol) |
| --- | --- | --- |
| F1 | The validator judges an issue **file** before creation, and enforces one rule on criteria. A criterion with no word outside its code spans is refused. It does not read `check`. `render_body` writes each check verbatim after the `Checked by:` label. Creation through the validator is the only way §1.3 opens an issue. | `automation/issue_validator.py` `validate_criterion_rule`, `_CODE_SPAN_RE`, `render_body`; `docs/standards/1-workflow.md:90` |
| F2 | The validator already needs the network and `gh`. `main` calls `gh_live_labels` and `gh_live_milestones` (`check=True`) and `gh_issue_state` before it reports anything. The tests replace these through the seams `validate_issue` takes (`get_issue_state`) and `monkeypatch`. | `automation/issue_validator.py` `main`, `validate_issue`; `automation/issue_validator_test.py` `fake_issue_state` |
| F3 | Checks come in two forms. **`Checked by:` form:** a child bullet. 58 issues carry it, 273 checks in all. **Inline form:** "… — checked by …" inside the criterion bullet. 21 issues carry it, 42 checks found by `— checked by` / `check is`. 12 issues carry no AC section. The remaining 44 carry checkbox criteria with no check. | measurement |
| F4 | 41 checks in 21 issues display differently from their source. 38 are in the `Checked by:` form, in #205, #207–#216, #219, #230, #255, #256, #295, #298 and #299. 3 are in the inline form, in #158, #159 and #169. | measurement |
| F5 | Two forms account for every altered check. A backslash before punctuation, dropped as an escape (`\.`, `\(`), appears in 36 checks. `\b` survives, because `b` is not punctuation. A `<placeholder>` read as an HTML tag and dropped appears in 5. #299's `git -C <live tree> rev-parse HEAD` displays as `git -C rev-parse HEAD`. No open issue holds a double-underscore name. The census of 20261114 found one, and AC1 keeps that case. | measurement |
| F6 | What gets altered is not always a command. #295's `ConfigurationError naming providers.<name>.<key>` displays as `providers..`. It is a config key path in prose. What a reader is harmed by is display, not command shape. | #295 body |
| F7 | An offline detector for the constructs that alter display matches the API exactly on the live set. Outside code spans, it looks for four things: a backslash before ASCII punctuation, a tag-shaped `<…>`, a matched emphasis delimiter pair (`*`, `**`, `_`, `__`, `~~`) not inside a word, and `[text](url)`. It flags the same 41 checks as F4, with 0 missed and 0 extra. It uses the standard library only. No Markdown library is in `requirements*.txt`. It is an approximation of GitHub's renderer, and cases the live set does not contain are untested. | measurement script; `requirements.txt`, `requirements-dev.txt` |
| F8 | Displaying unchanged does not mean the command is quoted. 97 checks in 47 issues begin with a command word outside backticks (`pytest` 43, `git` 32, `python3` 11, `grep` 9, `gh` 1, `for` 1). 42 checks begin with a backtick. | measurement |
| F9 | Telling a command from prose misjudges in both directions. A first-word rule needs a hand-kept list of command words, and on the live set refuses #284's own prose check, "for each edited issue, …". A wider shape rule refuses flag names in prose: #251 "under --force", "clients set active --help", #222 "--format". | measurement |
| F10 | A command mid-sentence escapes a first-word rule. Examples: #298 "asks for git commit -am …", #299 "reads journalctl --user -u workmain-notify". Those that hold an altering construct are among F4's 41. | measurement |
| F11 | The standard and the template it cites show the defect. `docs/standards/1-workflow.md:59` writes the criterion form as ``"*<property>*, checked by `<command>`"``, and GitHub displays it as `"<em></em>, checked by <command>"`. `docs/dev/specs/_TEMPLATE_SPEC.md` §5 writes `<property of the delivered system>`, `<behaviour>`, `<property of a document>`, `<section>` and `<what>` outside backticks. Its two criterion cells render empty. | `gh api -X POST /markdown` of `docs/standards/1-workflow.md:59` and `docs/dev/specs/_TEMPLATE_SPEC.md:77-90` |
| F12 | No check contains a literal backtick or a double-backtick span, so AC3's and AC4's "compared with backticks removed" is exact. Each sweep edit is a `gh issue edit --body-file` on a body the session did not author, so `CLAUDE.md` § Common Pitfalls' destructive-write checks apply to every one. | measurement; `CLAUDE.md` § Common Pitfalls |

## 4. Governing rules and options

**Governing rules.**

- **Owner:** `docs/ARCHITECTURE.md` names no owner for `automation/`, which is non-application tooling (`docs/standards/7-file-placement.md` §7). `automation/issue_validator.py` owns the rules on an issue file that the schema cannot express (its module docstring).
- **§1.2:** a criterion is a property, and its check is the evidence for it.
- **§1.5:** a rule has one home, and a change to a rule finds every statement of it.
- **`.claude/skills/session-start/references/spanner.md` § Working rules:** build only what the issue asks for, and offer only the options that survive.

**The command rule (Fix in mind, second question).** Enforcing "a check's command is written in backticks" in the validator needs a hand-kept list of command words, and misjudges prose in both directions (F9, F10). So the validator does not enforce it, and enforces display, which is the harm #284 names (F6). No rule is written for it either (Q2): writing a command in backticks is standard Markdown practice, and the standards do not restate standard practice. §1.2 changes only where its own text displays altered (F11). AC2's first half, a reading of §1.2 for how to write a check, is restated in the spec's §5 to keep only its display half, and the issue body is edited at close-out (§1.2).

**How the validator judges display (Fix in mind, first question).** Two options survive.

### Option A — Render through GitHub and compare

- **Approach:** a new rule renders each check through `gh api -X POST /markdown -f mode=gfm` and refuses a check whose rendered text differs from its source with backticks removed. The renderer is passed to `validate_issue` as a seam, as `get_issue_state` is, so the tests stay offline.
- **Pros:** exact by construction, because the renderer that displays the issue is the one judging it. There is no reading of GFM to keep current, and nothing to maintain. It adds no dependency: `main` already calls `gh` (F2).
- **Cons:** one API call per check at validation. The rule cannot run without the network, as the validator's other live checks already cannot.

### Option B — Detect display-altering constructs offline

- **Approach:** a pure function refuses a check whose text outside code spans holds any of F7's four constructs.
- **Pros:** offline and fast. It matched the API on all 41 live cases (F7).
- **Cons:** an approximation of GitHub's renderer, and it can drift from it in either direction: refusing text GitHub displays as written, or passing text it alters. Its construct list is maintained by hand.

**Recommendation:** Option A. It is the only option whose judgement is exact, and it needs nothing the validator does not already use (F2). Option B's only advantage is working offline, and the validator cannot run offline anyway.

**The sweep (Fix in mind, third question).** The sweep covers both sets (Q3): the 41 checks that display altered (F4) and the 97 unquoted commands that display correctly (F8), in 49 issues. Choosing which text in a check is the command is a reading, done once per check. Every edited check is listed in the results artifact for Ray's review. Before the first edit, every open issue's body is backed up, and the changes are checked against that backup by AC3 and AC4. Where the backup is kept is Q5.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Does the validator judge display by rendering through GitHub (Option A) or offline (Option B)? Recommended: A (§4). | Q1 answered 20261127: Option A. |
| Q2 | Is "a check's command is written in backticks" left to the written rule in §1.2 and to review, with the validator enforcing display only? This is the only surviving option (§4, F9, F10). | Q2 answered 20261127: no rule is written. Backticks around a command are standard Markdown practice, and recording standard practice as a rule is what the standards exist to avoid. The validator enforces display only. |
| Q3 | Does the sweep cover only the 41 checks that display altered, in 21 issues (F4), or also the 97 unquoted commands that display correctly, in 49 issues together (F8)? | Q3 answered 20261127: all of them, with a backup of every open issue taken before the sweep and the changes checked against it. |
| Q4 | #295 is `parked` and names `docs/standards/1-workflow.md` (§1.3). Its finding, provider defaults written in code, is unrelated to this work. Only its checks are in the sweep (F4). Fold it in, or leave it parked? Recommended: leave it parked. | Q4 answered 20261127: leave it parked. |
| Q5 | Where is the sweep's backup kept? §7 names no home for it, and the scratchpad does not survive a reboot. Recommended: a JSON file of every open issue's number, title and body, written by `gh issue list` before the first edit to a path outside the repository that Ray names. Its path and SHA-256 go in the results artifact. A body is restored from it with `gh issue edit --body-file`. GitHub's own edit history is a second copy. | |

## 6. Disposition

- Promoted to:
- Superseded by:

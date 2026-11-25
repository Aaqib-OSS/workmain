# A check's command in backticks — Design Study

**Status:** Active

**Kind:** Design study

**Author:** Spanner

**Date:** 20261125

**Read at:** 48419d5e982239ac9d8cb6475b7e55c3b14ba692

**Originating item:** Issue #284

---

## 1. Purpose

An issue's check is rendered as GitHub-flavoured Markdown, so a command written outside backticks can display altered: escapes, placeholders and emphasis markers vanish, and a reader who copies the displayed check runs a different command. This study decides how `automation/issue_validator.py` recognizes a command outside backticks, where `docs/standards/1-workflow.md` §1.2 states the rule, and what the one-time sweep of open issues covers. §1.2 requires a rule that refuses authored text to be run over the live set it will judge before it is specified. §3 is that run. The read was read-only. The only things run were `gh issue list`, `gh api -X POST /markdown` over each open issue's body, and measurement scripts kept in the session scratchpad. `git status` showed the tree unchanged apart from this file.

## 2. Scope of the read

- **Source the work changes:** `automation/issue_validator.py`, `automation/issue_validator_test.py`, `automation/fixtures/`, `docs/standards/1-workflow.md` §1.2, and the bodies of open issues.
- **Checks that enforce a rule the work touches** (§7 locations): `automation/issue_validator.py` `validate_criterion_rule` enforces the §1.2 criterion rule on an issue file. No file in `.github/workflows/` or `.githooks/` reads issue text. `automation/closeout_acs.py` reads a spec's criteria at close-out, not an issue's checks.
- **Every statement of the rule:** `git grep -n "checked by" -- docs/standards .claude docs/dev` returns `docs/standards/1-workflow.md:59` (the §1.2 criterion form) and `docs/dev/specs/_TEMPLATE_SPEC.md:79`. Every caller of the validator: `git grep -n issue_validator -- . ':!docs/archive'` returns `docs/standards/1-workflow.md:90` (§1.3, issue creation) and the validator's own test.
- **Issues by file** (§1.3): `automation/issue_validator.py` → #284. `automation/issue_validator_test.py` → #284. `.github/ISSUE_TEMPLATE/issue.schema.json` → none. `docs/standards/1-workflow.md` → 24 issues. They cite §1 sections, mostly from inside their own checks, and none is about how a check displays. #295 is the one `parked` issue among them (Q5). The term searches `backticks` and `"Checked by" render` add nothing beyond #284.
- **Measurement:** all 135 open issues, snapshotted at the read commit's time. Each body was rendered through `gh api -X POST /markdown -f mode=gfm -f context=lockdwn20/workmain`. Each check's rendered text was compared with its source with backticks removed. Checks were read in both forms (F3).
- **Left out:** closed issues; spec and design artifacts in `docs/archive/`; Markdown elsewhere in the repository (F11). GFM's emphasis rules were not read beyond what the measurement exercised (F7).

## 3. Findings

| # | Finding | Evidence (file:line, symbol) |
| --- | --- | --- |
| F1 | The validator judges an issue **file** before creation, and enforces one rule on criteria. A criterion with no word outside its code spans is refused. It does not read `check`. `render_body` writes each check verbatim after the `Checked by:` label. | `automation/issue_validator.py` `validate_criterion_rule`, `_CODE_SPAN_RE`, `render_body` |
| F2 | The validator already needs the network. `main` calls `gh_live_labels` and `gh_live_milestones` (`check=True`) and `gh_issue_state` before it reports anything. The tests replace these through the seams `validate_issue` takes (`get_issue_state`) and `monkeypatch`. | `automation/issue_validator.py` `main`, `validate_issue`; `automation/issue_validator_test.py` `fake_issue_state` |
| F3 | Checks come in two forms. **Field form:** a `- Checked by: …` child bullet. 58 issues carry it, 273 checks in all. **Inline form:** "… — checked by …" inside the criterion bullet. 21 issues carry it, the set the issue names except that #89 is in and #155 is not, with 42 checks found by `— checked by` / `check is`. 12 issues carry no AC section. The remaining 44 carry checkbox criteria with no check. | measurement |
| F4 | The issue's census reproduces, with drift. 38 field-form checks in 18 issues display differently: #205, #207–#216, #219, #230, #255, #256, #295, #298, #299. #206 and #224 have since closed. #295, #298 and #299 are newer than the census. 3 inline-form checks display differently: #158, #159, #169. | measurement; `gh issue view 206`, `224` → `CLOSED` |
| F5 | Two forms account for every altered check. Backslash before punctuation (`\.`, `\(`, `\b` survives because `b` is not punctuation) appears in 36 checks. A `<placeholder>` read as an HTML tag and dropped appears in 5. #299's `git -C <live tree> rev-parse HEAD` displays as `git -C rev-parse HEAD`. #256's `session_param_check.py <the service module>` loses its argument. No live check holds a double-underscore name. That AC1 test case guards a form the census of 20261114 found, not one live today. | measurement |
| F6 | What gets altered is not always a command. #295's `ConfigurationError naming providers.<name>.<key>` displays as `providers..`. It is a config key path in prose, and its check is altered the same way. What a reader is harmed by is display, not command shape. | #295 body |
| F7 | An offline detector for the constructs that alter display matches the API exactly on the live set. Outside code spans, it looks for four things: a backslash before ASCII punctuation, a tag-shaped `<…>`, a matched emphasis delimiter pair (`*`, `**`, `_`, `__`, `~~`) not inside a word, and `[text](url)`. It flags 41 checks in 21 issues, with 0 missed and 0 extra against F4. It uses the standard library only. `cmarkgfm` is not installed, and no Markdown library is in `requirements*.txt`. | measurement script; `requirements.txt`, `requirements-dev.txt` |
| F8 | Displaying unchanged does not mean the command is quoted. 97 checks in 47 issues begin with a command word outside backticks (`pytest` 43, `git` 32, `python3` 11, `grep` 9, `gh` 1, `for` 1), matching the issue's 97. 42 checks begin with a backtick. Only one leading-command check already carries a code span (#214, around a citation). | measurement |
| F9 | A first-word rule refuses correct prose once in the live set. The `for` hit is #284's own check, "for each edited issue, the body before and after compared…". Requiring `for <name> in` removes it. A wider shape rule, matching command words anywhere or a `--flag` anywhere, also hits flag names in prose: #251 "under --force", "clients set active --help", #222 "--format". | measurement |
| F10 | A command mid-sentence escapes a first-word rule. Examples: #298 "asks for git commit -am …", #299 "reads journalctl --user -u workmain-notify", "runs systemctl --user restart …". Those that hold an altering construct are caught by F7. Those that do not, display correctly and pass. The issue's own census calls its count a floor for this reason. | measurement |
| F11 | The rule's natural home in §1.2 shows the defect itself. Line 59 writes the criterion form as ``"*<property>*, checked by `<command>`"``. GitHub renders `<property>` as a tag and drops it, so the sentence displays as `"<em></em>, checked by <command>"`. | `docs/standards/1-workflow.md:59`; `gh api -X POST /markdown` of that line |
| F12 | The sentence the issue names as the rule's anchor no longer exists: "`automation/issue_validator.py` refuses a criterion that states only a command". Commit `a7b8fe7` removed it on 20261119, five days after the issue was written. No live sentence in §1 cites the validator's criterion rule. §1.3 cites the validator only for creation (`:90`). | `git log -S"refuses a criterion that states only a command" -- docs/` → `a7b8fe7`; `docs/standards/1-workflow.md:90` |
| F13 | The sweep set, taken as F7 together with F8's first-word rule, is 49 issues. No check contains a literal backtick or a double-backtick span, so AC4's "compare with every backtick removed" is exact. Each edit is a `gh issue edit --body-file` on a body the session did not author, so `CLAUDE.md` § Common Pitfalls' destructive-write checks apply to every one. | measurement; `CLAUDE.md` § Common Pitfalls |

## 4. Governing rules and options

**Governing rules.**

- **Owner:** `automation/` is non-application tooling (`docs/standards/7-file-placement.md` §7). `automation/issue_validator.py` owns the rules on an issue file that the schema cannot express (its module docstring). No `workmain/` owner is involved.
- **§1.2:** a criterion is "*property*, checked by *command*". A rule that refuses authored text is run over the live set before it is specified (§3 above).
- **§1.5:** a rule has one home, and a change to a rule finds every statement of it.
- **`spanner.md` § Working rules:** build only what the issue asks for.

### Option A — Render through GitHub and compare

- **Approach:** `validate_check_rule` renders each check through `gh api /markdown` behind a seam (a `render` callable, as `get_issue_state` is). It refuses a check whose rendered text differs from its source with backticks removed.
- **Pros:** exact by definition, with no reading of GFM to keep current. The network cost is small, because `main` already calls `gh` (F2).
- **Cons:** passes the 97 unquoted commands that display unchanged (F8), so the issue's AC1 fourth case cannot be met and must be restated (§1.2). One API call per check at validation.

### Option B — A command-shape pattern

- **Approach:** refuse a check whose text outside code spans matches a command's shape: a known command word, a `--flag`, shell or regex metacharacters.
- **Pros:** offline. Catches unquoted commands whatever they display.
- **Cons:** refuses correct prose, measured in F9 (flag names in prose, `for each`). It still misses commands mid-sentence (F10) and command words not on its list. Of the three options, this is the reading §1.2 warns about.

### Option C — Display-altering constructs, plus a leading command

- **Approach:** two refusals over the text of a check outside its code spans:
  - **C1:** the four constructs in F7, which alter display.
  - **C2:** a check whose first token is a command word, or `for <name> in`.

  Both are pure functions over the string, using the standard library.
- **Pros:** offline. C1 matched the API exactly on the live set (F7). C2 covers the 97 leading-form checks (F8) with no false refusal once `for` is narrowed (F9). Together they meet all four AC1 cases. The rule reads simply: the §1.2 form puts the command first, in backticks.
- **Cons:** C1 approximates GFM, so an emphasis edge case could drift from GitHub in either direction: refusing text GitHub displays as written, or passing text it alters. The live set exercised neither (F7). C2's command-word list is maintained by hand, and has no live source to read it from. A command mid-sentence that displays unchanged still passes (F10), as the issue's census already accepts.

**Recommendation:** Option C. It is the only option that meets every AC1 case without refusing correct prose on the live set (F7, F9), and it keeps validation offline. A cuts the AC that covers an unquoted command displaying unchanged. B refuses prose and still misses mid-sentence commands. C1's drift risk is bounded: the sweep's AC3 check renders every open issue through the API, so a divergence on the live set is caught there.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | How does the validator recognize a command outside backticks? A (render and compare), B (shape pattern) or C (display-altering constructs plus a leading command)? Recommended: C (§4). | |
| Q2 | The anchor sentence the issue names was removed on 20261119 (F12). Where does the rule go in §1.2? Recommended: in the "A criterion names a property" bullet (`:59`), which already shows the form. Fix F11 in the same edit by putting `<property>` in backticks. Name the validator as the rule's enforcement for issues. AC2's "beside the sentence that cites the validator" is restated in the spec's §5 (§1.2). | |
| Q3 | The validator judges a file before creation (F1). AC3 asks for its rule to be run over every open issue's checks, which live in bodies, and 21 of those issues use the inline form (F3). Recommended: the rule is a function over a check string. The results artifact records a run of that function over checks extracted from each live body, by a script kept in the scratchpad, so no new validator mode ships. Both forms are in the sweep, as the issue's census includes them. The alternative ships a body-reading mode, a mechanism the issue does not name. | |
| Q4 | §1.2 governs a criterion wherever it is written, spec §5 as well as an issue. Does the new sentence state the rule for every check, with the validator enforcing it on issues only? Or does it state the rule for issues alone? Recommended: every check, since `docs/dev/specs/` holds only the template today, so no spec needs sweeping. The template's §5 example is checked as part of the §1.5 rule-change search. | |
| Q5 | #295 is `parked` and names `docs/standards/1-workflow.md` (§1.3). Its finding, provider defaults in code, is unrelated to this work. Only its checks are in the sweep (F4). Fold it in, or leave it parked? Recommended: leave it parked. The sweep edits its checks' backticks and nothing else. | |

## 6. Disposition

- Promoted to:
- Superseded by:

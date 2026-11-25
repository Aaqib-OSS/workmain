## 1. Development Workflow

### 1.1 Two paths through the cycle

**The branch type decides the path.** The direct path has fewer checks because a document is easy to fix after the fact; application code is not, so the branch type decides the path, not the size of the change. §2.7 step 3 makes the branch type the first decision of any session, so the path is settled before work starts.

- **`feature/*` and `hotfix/*` → the full path.** The change alters application behaviour.
- **`chore/*` → the direct path.** §2.2 defines what it covers.

**The stages each path runs**, in this order:

| Stage | Full path | Direct path |
| --- | --- | --- |
| Recon | Required | Where the change must find every site of a rule, or spans documents that may contradict each other |
| Analysis | Required | Where Recon ran |
| Spec | Required | Required |
| Review | Required | Ray decides at the start |
| Approval | Required | Required |
| Implementation | Required, by Anvil | Required, by Spanner |
| Implementation review | Required | Where Review ran |
| Close-out | Required | Required |

**What shows each stage done.** Each stage is done when its artifact or field shows it. The condition is the same on both paths unless the stage says otherwise.

- **Recon** — Spanner reads, read-only, what the work will touch, and records what it finds verbatim in `docs/dev/design/`. It reads the source the work will change, every check that enforces a rule the work touches in the locations §7 names, and the issues §1.3's search by file returns for every file the work will change, and lists each in its findings. Where the findings turn up options, a trade-off, or questions whose answers change the work, the artifact is a design study (`docs/dev/design/_TEMPLATE_DESIGN.md`): it adds the options with a recommendation, and the open questions. A fix recon finds belongs to the spec.
  - *Done when* a `docs/dev/design/` artifact names the issue in its `**Originating item:**` field.
  - Where no recon runs, the spec's `**Design study:**` field reads `n/a`, which `/closeout`'s `P5a` accepts on a `chore/*` spec alone.
- **Analysis** — Ray and Spanner answer the design artifact's open questions. Each decision in the spec's Decision Log cites the question it answers.
  - *Done when* every row of that artifact's §5 Open questions carries an answer.
- **Spec** — written to `docs/dev/specs/` from its template. The template states which sections a direct-path spec may omit, and §1.2 how it verifies existing state.
  - *Done when* a `docs/dev/specs/` artifact names the issue in its `**Originating item:**` field.
- **Review** — Caliper reviews the spec in pass (`.claude/skills/session-start/SKILL.md` § Role 2), and its findings go to Spanner.
  - *Done when* the spec's last `Caliper` row, by its position in the Decision Log, is a pass row (`.claude/skills/session-start/references/caliper.md` § Emits) that reports no blocking finding and names the commit the pass read, and every blocking `Caliper` finding has a resolution. A non-blocking finding is resolved or recorded, and Review stays done. A `Caliper` row is one whose Source is exactly `Caliper`.
  - On the direct path, the stage is `n/a` where the spec's `**Status:**` is `Approved` and it carries no `Caliper` row.
- **Approval** — Ray approves the spec explicitly. Implementation starts from an approved spec.
  - *Done when* the spec's `**Status:**` is `Approved`. Where the spec carries a `Caliper` row, `**Status:**` is first set to `Approved` only when `git diff <commit> -- <spec path>`, run before that edit with the commit the Review stage's pass row names, shows changes only to Decision Log rows and the resolutions of that pass's non-blocking findings.
  - An edit to the spec while `**Status:**` is `Approved`, other than a Decision Log row, a change to the `**Status:**` field itself, and the amendment a Keep ruling makes (§1.1 Implementation review), sets `**Status:**` back to `Draft` in the same commit, and Ray approves it again.
- **Implementation** — step by step, from the approved spec. On the full path Anvil implements. On the direct path Spanner implements in the session that wrote the spec: each step quotes its exact replacement text, so a separate implementer would only transcribe it. Each step ends with a commit, and the next step begins. A departure stops the step before its commit: Anvil stops on every departure (`.claude/skills/session-start/SKILL.md` § Role 3), and Spanner on one that changes the meaning, scope or file set Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules).
  - *Done when* a results artifact in `docs/dev/results/` names the spec in its `**Spec:**` field. The implementing role writes it as its last implementation step, checking every acceptance criterion against the delivered code.
- **Implementation review** — on Ray's request, Caliper reviews the delivered branch against the spec and its results artifact, in a session of its own. `.claude/skills/session-start/references/caliper.md` § Post-implementation review states its reads and checks. Findings go to Spanner.
  - **An unstopped departure** is a change on the branch that skipped the stop it required: a change outside the spec, a results §4 row whose `Step stopped at` is `none`, or a `within approved meaning` change that altered the meaning, scope or file set Ray approved. Ray rules on each one with one of two outcomes:
    - **Revert** — the change is reverted on the branch, and carried to an issue under §1.3 if it is still wanted.
    - **Keep** — the spec is amended so the change traces to it.
  - The ruling's home is the resolution of the finding's Decision Log row. Spanner writes it there and writes the outcome into the spec, and the implementing role carries it out.
  - *Done when* the spec's Decision Log carries at least one `Caliper (post-implementation)` row, and every one has a resolution. A clean pass is the `No findings.` row the review emits for one.
  - On the direct path, the stage is `n/a` where the spec carries no `Caliper` row.
- **Close-out** — Ray runs the `/closeout` skill (`.claude/skills/closeout/SKILL.md`), the same run on both paths. Posting the issue's closing comment and closing the issue are Ray's, on the same principle as merging the `dev → main` PR.
  - *Done when* the spec's `**Status:**` is `Shipped`, and the artifact set is in `docs/archive/`.

### 1.2 Spec authoring rules

- **Every claim about existing behaviour is verified against source at authoring time**, citing file and symbol. The spec measures the defect's full extent itself — every site, every condition — and treats the issue's list as a starting point.
  - **Full path:** the §2 verified-current-state table carries the citations.
  - **Direct path:** the text being replaced is quoted inline in the step that replaces it. The quote is the verification: a quote that no longer matches the file is caught the moment the edit is applied.
- **A contract change enumerates its call sites.** Where a spec changes a signature, a required input, or an invariant of something already called elsewhere, its §2 table lists every call site found by a search of the whole repository — `tests/` and `automation/` included — together with the search that found them, and an acceptance criterion covers the whole enumerated set. A call site that bypasses the usual entry point is still a call site. A call site found by a name search is confirmed by reading what the call is made on: a caller calls the changed object itself. A claim that a method has no caller states that references by name (getattr, a method passed uncalled) were also searched.
- **Steps are ordered, and each one leaves the suite green.** Each step is committed on its own, so it can be reviewed and reverted on its own. A step that changes a signature, a required input or an invariant updates every caller in that step, or keeps the old call working.
- **A revision is surgical, and finds every statement of what it changes.** A change to a spec, including the resolution of a review finding, edits the statements that change. It searches the whole spec for every other statement of what it changes and every reference to an ID it adds, removes or alters, and changes each one, so the spec keeps agreeing with itself. §1.5 states the same duty across the document set for a rule change.
- **An issue's acceptance criteria validate the work.** They are written before the design exists, so the design is made on its merits. Where the design makes a criterion wrong, the spec restates it in its §5, says the issue body needs the edit, and the edit is made at close-out. A conflict between the design and an issue's criterion is settled this way, as a restated criterion. A criterion's check is one that can produce the answer the criterion states: a search covers every form of what it counts.
- **A criterion names a property of the delivered system, and the command is the evidence for it.** Write it as "*<property>*, checked by `<command>`". A command is a proxy, and a proxy has many ways to read green, only one of which is the change that was wanted. Naming the property is what tells a reviewer, and an implementer, which of those ways is the work. `docs/dev/specs/_TEMPLATE_SPEC.md` §5 shows an example.
- **Each criterion is checked by running something, or, for a property of a document, by a stated reading by Ray.** A reading names the section and what it is read for. A check that names Ray is his sign-off: the implementer records its results row as `Not met`, with `Awaiting Ray` as its evidence, and once he has checked it the row becomes `Met` with evidence in the form `Ray, <YYYYMMDD>: <what he read or ran>`.
- **A criterion that verifies changed behaviour names the entry path it exercises.** Where more than one entry path reaches the change, the criteria cover the set, or state which paths are omitted and why.
- **Sub-ACs map to the issue's ACs** by the numbering `ACn.m`, which lets close-out read the set mechanically. Every sub-AC maps to an AC on the originating issue.

### 1.3 Issue discipline

Work is tracked in GitHub Issues, called an issue and cited by its number. State is GitHub's own: open or closed. "Backlog", "backlog item" and "item number" are retired terms; a quote of existing text, and the filename `docs/archive/FEATURE_BACKLOG.md`, stay as they are.

**What an issue holds.** An issue records a problem, and the design study designs the fix. The issue's `context` field holds the first four parts below, and its `acs` field the criteria.

- **Problem** — what is wrong, in plain language: what a person sees or what breaks, and who notices.
- **Where** — the owner `docs/ARCHITECTURE.md` names, and each file and symbol by name. Names survive edits; line numbers move with the next commit.
- **Found** — where and when the problem was found, so a reader can tell how old the evidence is.
- **Fix in mind** — where the finder has one, it is written as a question for the design study to weigh.
- **Acceptance criteria** — properties of the delivered system, written as §1.2 states.

The design study reads an issue body as dated evidence. It re-checks each claim against current source, and decides the design from `docs/ARCHITECTURE.md` and these standards.

**Labels and milestones.**

- Labels carry area, and `defect`/`gap` is the label pair that says what an unscheduled issue is. An issue with no milestone carries exactly one of them.
  - A **defect** is work the project asserted already worked — a spec acceptance criterion, a CHANGELOG entry, a man page — and does not. A **gap** is work never planned, documented, or designed.
  - The pair stays when an issue is later pulled into a milestone. A milestone carrying one means that work came from the unscheduled pool rather than being planned as part of it.
- What each area label means is its description on GitHub, readable with `gh label list`.
- A milestone carries the exit condition that closes it, and that condition must cover every issue in it.

**Opening an issue.**

- An issue must be independently verifiable on its own: split into sub-issues only where each piece leaves the repository in a coherent state its own acceptance criteria can verify. Where steps are strictly sequential and individually meaningless, they stay inline as steps in one issue.
- **A new issue carries only what the open issues leave uncovered.** Before any issue is opened — while planning, at close-out, or to carry a finding or an unmet acceptance criterion forward — the open issues are searched for one covering the same defect or gap: `gh issue list --state open --search "<term>"` once for each symbol, file and behaviour the new issue would name, and every result read. A finding an open issue already covers is added to that issue's context or acceptance criteria, and a new issue carries only the rest.
- **An issue is opened when its body is written, it is on the board, and its dependencies are linked.** It is created with `python3 automation/issue_validator.py <file> --create`, which adds it to the `WorkmAIn Queue` project and links each issue in its `blocked_by` and `blocking` fields as a GitHub dependency. Every real dependency goes in those fields, whichever way it runs: the new issue may wait on an open one, or an open one may wait on it. The board reads dependencies from those fields alone, so each is verified by reading it back: `gh issue view <N> --json projectItems` for the board, and, in both directions, `gh api repos/lockdwn20/workmain/issues/<blocked>/dependencies/blocked_by` and `gh api repos/lockdwn20/workmain/issues/<blocker>/dependencies/blocking`.
- **An issue split by its design study takes its findings with it.** When a design study shows that its issue must be split into several issues, each new issue's write-up carries the study's findings and settled answers for that issue, so it stands on its own, and each new issue gets a design study of its own. The originating issue's study is narrowed to the work that issue keeps. If the originating issue is left as a parent with no work of its own, its study is deleted, and git keeps its history. A spec cites only a design study written for its own issue, because `/closeout` archives a spec's design study along with the spec (§1.5).

**Findings and parked issues.**

- **A finding outside the work in hand is reported to Ray in one line.** It becomes an issue only when he says so. Its finder then writes it as **What an issue holds** above states, and it joins an open issue that already covers it, found by the search above, or it is parked.
- **A parked finding is opened as its own issue.** When the search above finds no open issue covering it, it is opened as an issue labelled `parked`, after Ray approves it. Its **Where** names every file by path, because that is how recon finds it again. A parked issue sits on the board outside the scheduled work. The board walk passes over it (`.claude/skills/session-start/references/spanner.md` read 1). Ray schedules one by removing the label and placing it on the board.
- **Recon finds parked work by file.** For each file the work will change, recon runs `gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" --search "\"<path>\" in:body" --json number,title,labels`, and lists every issue it returns in its findings. Each `parked` issue found is one open question: fold it into this issue, or leave it parked. The recommendation states the finding's size, read from the code. Folding removes the `parked` label, and the finding joins this issue's scope and acceptance criteria. A search by file can return extra issues, and finds every issue that names the file.

### 1.4 Authorization points

An authorization point is an action that is irreversible or reaches outside the working tree. It is a property of the action, whatever the size of the work. Whoever is about to take it — the implementing role during Implementation, or the `/closeout` run during Close-out — states what is about to happen and waits for Ray's explicit approval. Every other action is a step.

| Action | Usually comes up in |
| --- | --- |
| Executing a DB migration against the live database. Ray approves it when it is about to run, separately from his approval of the spec that contains it. Building the test database from the migrations is a step. | Implementation, as a spec step |
| Merging to `main` | Close-out |
| Deleting a GitHub object: an issue, label, milestone, release, or a branch on `origin`. Deleting a local branch is a step (§2.3). | Close-out for a branch; any stage for the rest |
| Force-pushing any branch | Any stage |
| Changing the run state of a live service. The post-merge service restart is a step: §2.6 requires it after every `feature/*` and `hotfix/*` merge to `dev`, so close-out performs it. Every other change is an authorization point. | Close-out |

### 1.5 Documentation rules

**Artifacts.**

- Dev artifacts live where §7 places them. Each `docs/dev/` subdirectory holds a `_TEMPLATE_*.md` starting point; templates are advisory, and Caliper reviews the content.
- **Git is the version record.** A filename carries the subject alone, and an artifact is edited in place, so filenames and citations stay stable.
- **Every artifact carries exactly one `Status:` field, in its header block.**
  - Specs carry `Draft`, `Approved`, `Shipped` or `Superseded`.
  - Design and results artifacts carry `Active`, `Shipped` or `Superseded`.
- **An artifact stays in `docs/dev/` while its work is live.** When its issue closes out, `/closeout` moves the set to `docs/archive/<type>/`, which mirrors `docs/dev/<type>/`.
- **`docs/dev/` is authoritative; the archive is history.** An archived artifact records the system as it was when its work shipped, and later work may have changed it. A current decision rests on the standards, `docs/ARCHITECTURE.md` and current source.
- **A pointer within a set is relative; every other path starts from the repository root.** A set is a spec, its design study and its results artifact, which are archived together: **Design study:** `../design/<file>.md` from a spec, **Spec:** `../specs/<file>_SPEC.md` from a results artifact.
- **Specs carry a Decision Log** of decisions and review findings, each with its resolution.

**Writing.**

- **Markdown is written one line per paragraph**, per list item and per table row, and the editor wraps it. `.markdownlint-cli2.jsonc` governs all formatting, and `automation/style_check.py` checks it on every line a branch changes.
- **A document is written for a reader who comes to it cold.** An issue, a criterion and a design study's open question each stand alone and state the facts they depend on. What breaks, and who notices, is spelled out. A rule is stated in a sentence, and another document is cited as its checklist. A reason is stated in terms the reader can check, and an issue number may follow it as the record. An example is set out separately from the rule, and is checked against the rest of the standards before it goes in.
- **A bare `§` is a section of the `docs/standards/` set**, whose numbers are unique across its files. A section of any other document is cited with that document's name.
- **An item that has a name of its own is cited by that name:** a test by its pytest node ID, a file by its path, a function or class by its symbol. An ID names an item that has no other name, such as a design rule, a criterion, a finding or an open question. It is used inside the file that defines it; anywhere else it is cited in full.
- **State is derived from its live source.** A document, a spec step, a criterion or a script states the rule and reads the list, count, status or version from where it lives: `pytest --collect-only -q`, `gh issue list`, `gh label list`, `workmain/__version__.py`. An operational bound, such as a `--limit`, is derived the same way, and a list found in a document is replaced by its source. A dated measurement with its evidence, such as a recon's suite count at recon time, is a record and stays.

**Rules.**

- **A rule has one home:** `CLAUDE.md`, a `docs/standards/` file, or a role's skill reference, as `CLAUDE.md`'s opening states. Everywhere else cites it. Text that ships alongside code follows `docs/standards/3-code.md`.
- **A new rule or standard requires Ray's approval.** The method a fix used stays in that fix's own artifacts.
- **A change to a rule searches the whole document set** — `CLAUDE.md`, the standards, the skills, the templates, and the locations §7 names — for every statement, check and citation of it, and corrects each one. A historical citation in `docs/archive/` stays as written; a live, forward-looking reference is repointed.

### 1.6 Sequencing

**The GitHub Project Board is the order.** Every issue joins the `WorkmAIn Queue` project at creation (§1.3), and its position there is the sequence. What comes next is the first open issue on the board whose sub-issues are all closed, passing over any `parked` issue (§1.3): a parent waits for its children. The board is read as `.claude/skills/session-start/references/spanner.md` read 1 states.

Ordering is Ray's, set in the Web UI. Adding a new issue to the board (§1.3) is the repository's one write to it, and it places the issue without ordering it. The project's `Status` field is auto-populated by GitHub and is left unread.

**Preemption is a move on the board.** Work that preempts the schedule is moved to the top of the board. Ray decides each case.

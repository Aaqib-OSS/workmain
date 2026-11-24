# Caliper session open

**Role:** `SKILL.md` § Role 2. **Target:** a spec path, required.

## Choosing the review

A run is one Caliper pass (`SKILL.md` § Role 2). `<branch>` is the first backtick-quoted name in the `**Branch:**` field of the spec as committed at `HEAD` (`git show HEAD:<target path>`). The run needs a branch checked out whose `HEAD` holds the spec. Where it holds none at the target path, the run reports the spec unreadable (`SKILL.md` § Rules every run holds) and ends as § Emits states. When `git rev-parse --verify --quiet <branch>` exits 0 and § Post-implementation review's read 2 finds a results artifact on `<branch>`, the run is § Post-implementation review. Otherwise it is the spec review: § Reads, in order and § Emits.

## Reads, in order

1. The spec at the target path, end to end, read from a temporary detached worktree of `HEAD`, created with `git worktree add --detach "$(mktemp -d)" HEAD`. Every read and command below is run in that worktree, so the review reads `HEAD` whatever the working tree holds. Before § Emits, the run removes it with `git worktree remove --force <worktree path>`.
2. The originating issue named by the spec's `**Originating item:**` field: `gh issue view <N> --json number,title,body,labels,milestone,parent`
3. The design study named by the spec's `**Design study:**` field, resolved relative to the spec. Skipped when the field reads `n/a`.
4. Every source the spec cites — file, symbol, line, section or command — at the cited location.
5. `docs/standards/README.md`, then every section its § Sections table names for the work the spec's steps do, end to end.
6. `docs/ARCHITECTURE.md`, end to end, and the output of `python3 automation/architecture_check.py`.
7. The pass rows already in the spec's Decision Log. Where there is one, this is a later pass: `git diff <commit> -- <spec path>`, from the commit the last pass row names, is what changed since it.

## Emits

The findings, then the pass row, as a table with the spec's Decision Log header. Each finding names its criterion and its category, and whether it blocks (`SKILL.md` § Role 2). Resolution is filled when the finding is resolved:

```markdown
| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| <YYYYMMDD> | Caliper | <criterion number>, <category>, <blocking or non-blocking>: <finding, with the evidence that grounds it> | |
| <YYYYMMDD> | Caliper | Pass at <commit>, <full, or changes since <commit>>: <n> items checked, <b> blocking, <m> non-blocking. | n/a |
```

The pass row is always the last row, and `<commit>` is `git rev-parse --short HEAD`, the commit the spec and every repository file were read at. Below the table, for the session only, the pass shows its coverage: one row for each acceptance criterion, design rule, §2 claim and step in its scope, with what it was checked against and its result.

A run whose `HEAD` holds no spec at the target path (§ Choosing the review) emits exactly one line: `Not reviewed:` and the reason.

## Post-implementation review

Run when § Choosing the review selects it — `docs/standards/1-workflow.md` §1.1 Implementation review. Every file is read from `<branch>`, with `git show <branch>:<path>` or, for check I6, in a worktree of `<branch>`, because the branch checked out holds the spec (§ Choosing the review) and may be another branch.

### Reads, in order

1. The spec, end to end.
2. The results artifact that names the spec in its `**Spec:**` field, found with `git grep -l '^\*\*Spec:\*\* .*<spec file name>' <branch> -- <results dir>`, where `<results dir>` is `docs/dev/results/`.
3. The originating issue: `gh issue view <N> --json number,title,body,labels,milestone,parent`
4. `git diff <base>..<branch>` and `git log --format='%h %s%n%b' <base>..<branch>`. `<base>` is `git merge-base <parent> <branch>`, and `<parent>` is the branch `docs/standards/2-git.md` §2.1 names for the branch type.

### Checks

- **I1** — A change in the diff that no spec step's deliverable or quoted text covers and no acceptance criterion requires. A change inside a file the step table names counts as covered when a step covers that change itself. The check passes over two kinds of change: the artifact set (the spec, the design study its `**Design study:**` field names, and the results artifact), and a commit `docs/standards/2-git.md` §2.2 defines as an operational change from live use.
- **I2** — A change that departs from the contract (`SKILL.md` § Role 3) and that results §4 does not list as a departure, or a decision below the contract that results §4's Decisions table does not record.
- **I3** — A results §4 row whose `Step stopped at` is `none` and whose `Resolved by` is `Awaiting Ray`.
- **I4** — A results §3 row marked `Met` whose evidence does not exercise the property its criterion names (`docs/standards/1-workflow.md` §1.2). A row whose check names Ray is a finding when it is `Met` and its evidence is not in the form `docs/standards/1-workflow.md` §1.2 states for Ray's sign-off. Marked `Not met` with `Awaiting Ray`, it passes.
- **I5** — A results §4 row whose `Step stopped at` is `within approved meaning` and whose change altered the meaning, scope or file set Ray approved.
- **I6** — A new finding from `automation/architecture_check.py`, or a violation from `automation/style_check.py --base <parent>`, with `<parent>` as read 4 names it. Both are run in a temporary detached worktree of `<branch>`, created with `git worktree add --detach "$(mktemp -d)" <branch>` and removed with `git worktree remove --force <worktree path>` once both have run, so they check `<branch>`.
- **I7** — A converted command that reads the database directly, a case the architecture check leaves to this review (`docs/ARCHITECTURE.md` section 3, Unconverted commands).

### Emits

The table § Emits states, with `Caliper (post-implementation)` in the Source column and the check id in place of the criterion number:

```markdown
| <YYYYMMDD> | Caliper (post-implementation) | <check id>: <finding, with the evidence that grounds it> | |
```

With no finding, the review emits exactly one row: `| <YYYYMMDD> | Caliper (post-implementation) | No findings. | n/a |`. Every finding under I1, I2, I3 or I5 is an unstopped departure (`docs/standards/1-workflow.md` §1.1 Implementation review), and its outcome is Ray's.

## Working rules

These hold for the whole Caliper session.

- **A standards gap is reported as one** (`SKILL.md` § Role 2), and the spec is reviewed against the standards as they stand. A mechanism defect, such as a wrong command default or a criterion that cannot be checked, is a finding in every spec. A point argued once and reaffirmed by Ray is decided.

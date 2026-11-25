---
name: closeout
description: "Perform an issue's close-out — merge the branch where its type requires, bump the version, cut the tag and Release, restart the daemon, mark the spec and design artifact Shipped, and complete the docs/dev/results/ artifact. Re-enterable: the resume point is read from the repository on every run. Stops at the merge to main."
disable-model-invocation: true
user-invocable: true
---

# `/closeout`

User-initiated only. This skill **performs** the necessary branch close-out steps. `/closeout` merges, bumps, tags, releases, restarts and completes the results artifact for whatever issue's branch is currently checked out. It composes the closing comment and prints the command that posts it. Posting and closing the issue are Ray's (`docs/standards/1-workflow.md` §1.1 Close-out).

## When this runs

Once the last implementation commit lands on the branch being closed out, before that branch has merged anywhere. `--branch <name>` is the escape hatch for an issue whose branch has already merged and been deleted (§2.3) — in that case the branch is resolved from the merge commit instead, and every file read below comes from its second parent, `git show <merge>^2:<path>`. The run has these two modes, and states which one it is in before reporting a single row.

**Base ref.** Anything asking what this branch changed diffs against `git merge-base main <branch>`, because a branch cut before a later change landed on `main` differs from it without having touched it.

## Preflight — read-only, every row, every run

Run every row below, in order, every time. **Preflight only reads.** The first write follows a full preflight pass, so a failing run leaves the repository exactly as it found it and is re-runnable with nothing to undo.

Every row is reported `pass`, `fail`, or `n/a`, **with its reason**, on every run — a failing run as much as a passing one. A check that could not be evaluated is a failure. Each failure is reported once, with its remedy.

`P5` and `P6` both report, always. When the results artifact named by `P5` is absent, `P6` fails too, reading `not evaluated — the artifact named by P5 is absent`. P6 reports this failure on its own line: two failures for one cause is correct, because they carry different remedies.

| # | Check | `n/a` when | Remedy on failure |
| --- | --- | --- | --- |
| P1 | `git status --porcelain` prints nothing | never | Commit or stash before running close-out |
| P2 | The branch resolves — `git branch --show-current`, or `--branch <name>` for an already-merged branch | never | Check out the branch being closed out, or pass `--branch` |
| P3 | The branch prefix is one of `chore`, `feature`, `hotfix` | never | `docs/standards/2-git.md` §2.1 defines three; a fourth is a mistake or a standards change this table has yet to reflect |
| P4 | Exactly one spec names this branch in its `**Branch:**` field — searching `docs/dev/specs/` then `docs/archive/specs/` — and its `**Status:**` is `Approved` or `Shipped` | never | No spec: `docs/standards/1-workflow.md` §1.1 permits no implementation without one. Several: the `**Branch:**` fields collide and one is wrong. `Shipped` is **not** a failure — it means an earlier run reached the artifact step, and § Resume point decides where this one starts. Resolving from `docs/archive/specs/` is **not** a failure either — it means an earlier run reached the archive step |
| P5 | The results artifact exists in the `results/` directory of the root holding the spec `P4` resolved, and its `**Status:**` is one `docs/standards/1-workflow.md` §1.5 defines | never | The implementing role writes it from `_TEMPLATE_RESULTS.md` as its last implementation step. Close-out sets it to `Shipped`, so a re-entered run finds it at either status |
| P5a | The design artifact named by the spec's `**Design study:**` field exists, resolved relative to the spec itself (`docs/standards/1-workflow.md` §1.5 makes an intra-set pointer relative, so it lands in whichever root the spec was found in), and its `**Status:**` is one `docs/standards/1-workflow.md` §1.5 defines | the branch prefix is `chore` and the spec's `**Design study:**` field reads `n/a` — the direct path with no recon, `docs/standards/1-workflow.md` §1.1 | No field at all, or `n/a` on a `feature/*` or `hotfix/*` branch: `docs/standards/1-workflow.md` §1.1 requires a recon on the full path and permits `n/a` only in the direct path's stated form. Missing file: the citation is broken and the spec cannot be verified against what it was built from |
| P6 | `python3 automation/closeout_acs.py --branch <name>` exits `0` — every spec AC id has a row, every row is `Met` or a `Carried` citing `#N`, every `Met` row has evidence, and no row carries an id the spec lacks, and the spec's §5 carries at least one `ACn.m` id — the sub-AC mapping `docs/standards/1-workflow.md` §1.2 defines | never | The module names the offending id on stderr. Fill the missing row, or carry the AC to a follow-up issue and cite it. This skill does not judge whether the disposal is right |
| P7 | `python3 automation/architecture_check.py` and `python3 automation/style_check.py` both exit `0` | `--branch` mode: the branch has merged and its tree is not checked out, so neither check can read it | Fix it on the branch. A new architecture finding is a departure (`.claude/skills/session-start/SKILL.md` § Role 3) that implementation should have stopped on; take it to Ray |
| P8 | `pytest` passes | never | Fix the failures; close-out proceeds on a green suite |
| P9 | `pytest automation/` passes | the branch changed no path under `automation/`, diffed against the merge base | Fix the failures |
| P10 | `python3 automation/check_release_integrity.py` exits `0` | never | Repo-wide, so a `chore/*` branch can meet it without having caused it; the fix is the missing Release or `CHANGELOG.md` section it names |
| P11 | Against the merge base: `workmain/__version__.py` is unchanged, no `CHANGELOG.md` section was added, and no tag points at the branch | branch type is `feature` or `hotfix`, where all three are required rather than forbidden | `docs/standards/2-git.md` §2.2 makes a `chore/*` merge no release. **On a `chore/*` branch this asserts absence, and reports `pass` or `fail`** |

**Where the artifacts are read from.** Only `P4` searches two roots, live first: `docs/dev/specs/` then `docs/archive/specs/`. It has to, because a close-out starts from a branch name and the spec could be in either. Everything else follows from the spec once found — the results artifact sits in the `results/` directory of the spec's own root, and the design artifact is named by a pointer relative to the spec — so neither needs a search.

An artifact found in the archive is a normal result: the archive step below is what puts it there, so a run that re-enters after that step must still resolve everything it resolved before. Whether the move has happened is the archive step's own **Done when**. A spec present in *both* roots is a half-finished move and fails `P4` as a collision.

A spec written before §1.5 required the relative form carries a repo-root `**Design study:**` path. Accept it as written, from the repository root.

If any row fails, the run stops here, before the first write, and prints the remedy for each failure.

## Resume point

Close-out is re-enterable. **The resume point is read from the repository on every run**, so a run ended by a declined prompt, a closed terminal, or a crash all re-enter the same way.

After preflight and before the first write, walk the variant's steps in order and find the first whose **Done when** observable is not yet true. That step is where this run starts. State the resume point before writing anything — which steps are already done, and which one is next.

The resume point comes from each step's **Done when** observable alone. A `**Status:** Shipped` spec means step 1 ran; the walk above decides what is left.

If every step's observable is already true, the close-out is complete. Say so and stop.

## Choosing the variant

Reached only when every preflight row passed. Read `P3`'s branch prefix and load exactly one reference file, and follow it from the file:

- `chore/*` → `references/chore.md`
- `feature/*` → `references/feature.md`
- `hotfix/*` → `references/hotfix.md`

Each carries that type's full perform sequence: what gets committed on the branch before the first merge, the merge order, the authorization point, and — where the type carries one — the post-merge daemon restart.

## The stop

Every close-out crosses one authorization point (`docs/standards/1-workflow.md` §1.4): **merging this branch to `main`** — which takes the shape of waiting for Ray to merge the pull request to `main` — `dev → main` on `feature/*`, the branch itself on `chore/*` and `hotfix/*` — since `docs/standards/2-git.md` §2.2 requires the pull request and he merges it himself. It is one `AskUserQuestion` call stating what is about to happen, and stopping ends the run naming what has already happened and what has not. A `feature/*` close-out also waits for Ray to merge its pull request into `dev`. That merge is not an authorization point, but it takes the same shape: one `AskUserQuestion` call, and *defer* exits cleanly.

A working branch on `origin` is expected (`docs/standards/2-git.md` §2.3); Ray deletes it when he merges the pull request. Close-out only deletes local branches (`docs/standards/1-workflow.md` §1.4). Every other step of the variant runs without stopping (`docs/standards/1-workflow.md` §1.4).

**A failing check stops the run.** The wait steps run `gh pr checks <N> --watch`. When any check fails, the run reports each failing check and its failed log lines (`gh run view <run-id> --log-failed`), and stops. The pull request stays open and the branch stays. The implementing role fixes the failure on this branch and records it in the spec's decision log and the results artifact. Ray then re-runs `/closeout`, whose resume point is the push step.

## The closing comment

Composed once the variant's last step is done, and printed as `gh issue comment <N> --body-file -` with the body inline, so posting is one paste.

The body carries, in this order, every item that applies to the branch type:

- the merge commit SHA on `main`, and the branch it merged
- the path to the results artifact — its archived path, since the comment is composed after the archive step has moved it
- the AC verdict from `automation/closeout_acs.py` — the verdict line it prints
- the version, the tag, and the Release URL — `feature/*` and `hotfix/*` only (`docs/standards/2-git.md` §2.2)
- the confirmed ActiveEnterTimestamp — `feature/*` and `hotfix/*` only (`docs/standards/2-git.md` §2.6)
- the PR numbers — every branch type has one; `feature/*` has two, into `dev` and `dev → main`

The body carries only the items that apply to the branch type.

**Anything else, stop and surface to Ray.**

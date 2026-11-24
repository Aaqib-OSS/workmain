# `chore/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `chore/*` branch. The steps below take the branch to `main` through a pull request, archive the set, and merge it to `dev`, as `docs/standards/2-git.md` §2.2, §2.3 and §2.6 define for a `chore/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | `git push origin <branch>`, with no `-u` — `docs/standards/2-git.md` §2.3 | `git ls-remote origin refs/heads/<branch>` returns the local tip |
| 2 | `gh pr create --base main --head <branch>`. Its number is `<N>` in the steps below — `docs/standards/2-git.md` §2.2 | `gh pr list --base main --head <branch> --state all` returns it |
| 3 | Wait for the pull request's checks: `gh pr checks <N> --watch`. A failing check stops the run (`SKILL.md`, *A failing check stops the run*) | `gh pr checks <N>` exits `0`, and the pull request's head commit equals the local tip |
| 4 | Set the spec, the design artifact **where the spec names one**, and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:** n/a`, §5 suite results, the criteria step 3's run checked, and live verification. Commit on the branch, before any merge — `docs/standards/2-git.md` §2.2 | The branch tip carries the spec, the results artifact, and any design artifact the spec names, each at `Shipped`, and the results artifact's §5 is complete |
| 5 | `git mv` this branch's artifact set — the spec `P4` resolved, the results artifact `P5` resolved, and the design artifact `P5a` resolved where the spec names one — from `docs/dev/<type>/` to `docs/archive/<type>/`, in a commit of its own, before any merge, subject `docs(closeout): archive the issue #<N> artifact set`. The pointers within the set are relative (`docs/standards/1-workflow.md` §1.5), so the move is a pure rename — `docs/standards/2-git.md` §2.2 | The branch tip carries the set only under `docs/archive/<type>/`, `git status --porcelain` prints nothing, and the commit is a pure rename: `git show --stat` lists each file as a rename with 0 lines changed |
| 6 | `git push origin <branch>`, then wait for the pull request's checks: `gh pr checks <N> --watch`. A failing check stops the run (`SKILL.md`, *A failing check stops the run*) | `gh pr checks <N>` exits `0`, and the pull request's head commit equals the local tip |
| 7 | ⏸ **Authorization — Ray merges the pull request.** Answers: *merged*, or *defer*, which exits cleanly | `gh pr view <N> --json state` reads `MERGED` |
| 8 | `git checkout main && git pull --ff-only` — `docs/standards/2-git.md` §2.2 | `git merge-base --is-ancestor <branch> main` succeeds and `main` equals `origin/main` |
| 9 | `git checkout dev && git merge --no-ff <branch>`; push `dev`. Its run is the confirmation, and close-out does not wait for it — `docs/standards/2-git.md` §2.1, §2.3 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 10 | `git branch -d <branch>`; `git fetch --prune` — `docs/standards/2-git.md` §2.3 | `git rev-parse --verify <branch>` fails |

**Notes.**

- **Once the pull request reads `MERGED`, steps 1–6 count as done.** Ray deletes the remote branch when he merges, so step 1's observable no longer holds after the merge. A re-entered run must not push the branch again.
- **The artifacts are set to Shipped and archived after the first green run** (steps 4–5), so a fix for a failing check lands in `docs/dev/` and is recorded in the spec's decision log and the results artifact, not in the archive.
- **Step 6 waits again** because steps 4 and 5 change Markdown that the style check reads.
- **The push has no `-u`,** so `git branch -d` at step 10 checks the branch against `HEAD`, not against a remote branch Ray has deleted.

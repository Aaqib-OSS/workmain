# `hotfix/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `hotfix/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | Bump `workmain/__version__.py` by a patch — both `__version__` and `__version_info__` — and add its `CHANGELOG.md` section — `docs/standards/2-git.md` §2.5 | Both differ from `git merge-base main <branch>` and name the same version, and `python3 automation/check_release_integrity.py --no-remote` exits 0 on the branch |
| 2 | `git push origin <branch>`, with no `-u` — `docs/standards/2-git.md` §2.3 | `git ls-remote origin refs/heads/<branch>` returns the local tip |
| 3 | `gh pr create --base main --head <branch>`. Its number is `<N>` in the steps below — `docs/standards/2-git.md` §2.2 | `gh pr list --base main --head <branch> --state all` returns it |
| 4 | Wait for the pull request's checks: `gh pr checks <N> --watch`. A failing check stops the run (`SKILL.md`, *A failing check stops the run*) | `gh pr checks <N>` exits `0`, and the pull request's head commit equals the local tip |
| 5 | Set the spec, the design artifact and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:**` with step 1's version and tag, §5 suite results, the criteria step 4's run checked, and live verification. Commit all of it on the branch, before any merge — `docs/standards/2-git.md` §2.2 | The branch tip carries all three at `Shipped` and §5 is complete |
| 6 | `git mv` this branch's artifact set — the spec `P4` resolved, the results artifact `P5` resolved, and the design artifact `P5a` resolved where the spec names one — from `docs/dev/<type>/` to `docs/archive/<type>/`, in a commit of its own, before any merge, subject `docs(closeout): archive the issue #<N> artifact set`. The pointers within the set are relative (`docs/standards/1-workflow.md` §1.5), so the move is a pure rename — `docs/standards/2-git.md` §2.2 | The branch tip carries the set only under `docs/archive/<type>/`, `git status --porcelain` prints nothing, and the commit is a pure rename: `git show --stat` lists each file as a rename with 0 lines changed |
| 7 | `git push origin <branch>`, then wait for the pull request's checks: `gh pr checks <N> --watch`. A failing check stops the run (`SKILL.md`, *A failing check stops the run*) | `gh pr checks <N>` exits `0`, and the pull request's head commit equals the local tip |
| 8 | ⏸ **Authorization — Ray merges the pull request.** Answers: *merged*, or *defer*, which exits cleanly | `gh pr view <N> --json state` reads `MERGED` |
| 9 | `git checkout main && git pull --ff-only` — `docs/standards/2-git.md` §2.2 | `git merge-base --is-ancestor <branch> main` succeeds and `main` equals `origin/main` |
| 10 | `git tag v<version>` on `main`; push the tag; `gh release create v<version> --generate-notes` — `docs/standards/2-git.md` §2.2 | `git ls-remote --tags origin v<version>` returns the tag and `gh release view v<version>` exits `0` |
| 11 | `git checkout dev && git merge --no-ff <branch>`; push `dev`. Its run is the confirmation, and close-out does not wait for it — `docs/standards/2-git.md` §2.1, §2.3 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 12 | `systemctl --user restart workmain-notify.service` — `docs/standards/2-git.md` §2.6 | `ActiveEnterTimestamp` postdates the step 11 merge commit |
| 13 | `git branch -d <branch>`; `git fetch --prune` — `docs/standards/2-git.md` §2.3 | `git rev-parse --verify <branch>` fails |

**Notes.**

- **Once the pull request reads `MERGED`, steps 2–7 count as done.** Ray deletes the remote branch when he merges, so step 2's observable no longer holds after the merge. A re-entered run must not push the branch again.
- **The version bump comes first** (step 1), so the pull request's checks run on the commit that will be released.
- **The artifacts are set to Shipped and archived after the first green run** (steps 5–6), so a fix for a failing check lands in `docs/dev/` and is recorded in the spec's decision log and the results artifact, not in the archive. A fix that changes the release keeps step 1's version, because the version has not been tagged yet.
- **Step 7 waits again** because steps 5 and 6 change Markdown that the style check reads.
- **The push has no `-u`,** so `git branch -d` at step 13 checks the branch against `HEAD`, not against a remote branch Ray has deleted.

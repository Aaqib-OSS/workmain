# `feature/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `feature/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | `git push origin <branch>`, with no `-u` — `docs/standards/2-git.md` §2.3 | `git ls-remote origin refs/heads/<branch>` returns the local tip |
| 2 | `gh pr create --draft --base dev --head <branch>`. Its number is `<N>` in the steps below — `docs/standards/2-git.md` §2.2 | `gh pr list --base dev --head <branch> --state all` returns it |
| 3 | Wait for the pull request's checks: `gh pr checks <N> --watch`. A failing check stops the run (`SKILL.md`, *A failing check stops the run*) | `gh pr checks <N>` exits `0`, and the pull request's head commit equals the local tip |
| 4 | Set the spec, the design artifact and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:**` with the minor version and tag derived under `docs/standards/2-git.md` §2.5, §5 suite results, the criteria step 3's run checked, and live verification. Commit on the branch, before any merge — `docs/standards/2-git.md` §2.2 | The branch tip carries all three at `Shipped` and §5 is complete |
| 5 | `git mv` this branch's artifact set — the spec `P4` resolved, the results artifact `P5` resolved, and the design artifact `P5a` resolved where the spec names one — from `docs/dev/<type>/` to `docs/archive/<type>/`, in a commit of its own, before any merge, subject `docs(closeout): archive the issue #<N> artifact set`. The pointers within the set are relative (`docs/standards/1-workflow.md` §1.5), so the move is a pure rename — `docs/standards/2-git.md` §2.2 | The branch tip carries the set only under `docs/archive/<type>/`, `git status --porcelain` prints nothing, and the commit is a pure rename: `git show --stat` lists each file as a rename with 0 lines changed |
| 6 | `git push origin <branch>`, then wait for the pull request's checks: `gh pr checks <N> --watch`, then `gh pr ready <N>`. A failing check stops the run (`SKILL.md`, *A failing check stops the run*) | `gh pr checks <N>` exits `0`, the pull request's head commit equals the local tip, and `gh pr view <N> --json isDraft` reads `false` |
| 7 | ⏸ **Ray merges the pull request into `dev`.** Answers: *merged*, or *defer*, which exits cleanly | `gh pr view <N> --json state` reads `MERGED` |
| 8 | `git checkout dev && git pull --ff-only` — `docs/standards/2-git.md` §2.2 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 9 | Bump `workmain/__version__.py` by a minor — both `__version__` and `__version_info__` — and add its `CHANGELOG.md` section, committed on `dev` and, once the check below passes, pushed — `docs/standards/2-git.md` §2.2, §2.5 | Both on `dev` name the version recorded at step 4, and `python3 automation/check_release_integrity.py --no-remote` exits 0 on `dev`, and `dev` equals `origin/dev` |
| 10 | `systemctl --user restart workmain-notify.service` — `docs/standards/2-git.md` §2.6 | `ActiveEnterTimestamp` postdates the merge commit of step 7 |
| 11 | `git branch -d <branch>`; `git fetch --prune` — `docs/standards/2-git.md` §2.3 | `git rev-parse --verify <branch>` fails |
| 12 | `gh pr create --base main --head dev`. Its number is `<M>` in the steps below — `docs/standards/2-git.md` §2.2 | `gh pr list --base main --head dev --state all` returns it |
| 13 | Wait for the pull request's checks: `gh pr checks <M> --watch`. A failing check stops the run (`SKILL.md`, *A failing check stops the run*) | `gh pr checks <M>` exits `0`, and the pull request's head commit equals `origin/dev` |
| 14 | ⏸ **Authorization — Ray merges the `dev → main` pull request.** Answers: *merged*, or *defer*, which exits cleanly | `gh pr view <M> --json state` reads `MERGED` |
| 15 | Fetch `main`; `git tag v<version>` on `main`; push the tag; `gh release create v<version> --generate-notes` — `docs/standards/2-git.md` §2.2 | `git ls-remote --tags origin v<version>` returns the tag and `gh release view v<version>` exits `0` |

## Why this order

- **The branch reaches `dev` through a pull request,** so the checks run on the branch before it merges. A failing check is fixed on the branch, and recorded in the spec's decision log and the results artifact.
- **The pull request stays a draft until step 6,** so it becomes ready to merge once steps 4 and 5 are on it.
- **The archive step comes after the first green run and before the merge.** Archiving after the first green run keeps a fix out of the archive. Archiving before the merge lets the rename ride the merge commit; archiving afterwards would mean editing documents directly on `dev` or `main`, where §2.2 allows only merges and the release bump.
- **Step 6 waits again** because steps 4 and 5 change Markdown that the style check reads.
- **Once the pull request into `dev` reads `MERGED`, steps 1–6 count as done,** because it leaves draft only at step 6. Ray deletes the remote branch when he merges, so a re-entered run resumes at step 8.
- **The version is recorded at step 4 and bumped at step 9.** §2.5 makes the minor bump deterministic from the current `workmain/__version__.py`, so the version and tag are known before they exist.
- **The restart is at step 10, before the `dev → main` pull request.** `dev` carries the code from step 7, so a *defer* at step 14 leaves `dev` deployed.
- **The branch is deleted at step 11.** Its only merge happened at step 7; steps 12–15 work on `dev` and `main`.
- **The push of the release bump at step 9 runs the workflow on `dev`.** That run is a confirmation, and close-out continues to step 10 once the push lands. The `dev → main` pull request's checks at step 13 cover the same commit.
- **The pull request numbers reach the issue through the closing comment.** `<N>` first exists at step 2, and `<M>` at step 12.
- **The push has no `-u`,** so `git branch -d` at step 11 checks the branch against `HEAD`, not against a remote branch Ray has deleted.

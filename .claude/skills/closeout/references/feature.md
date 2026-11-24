# `feature/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `feature/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | Set the spec, the design artifact and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:**` with the minor version and tag derived under `docs/standards/2-git.md` §2.5, §5 suite results, live verification. Commit on the branch, before any merge — `docs/standards/2-git.md` §2.2 | The branch tip carries all three at `Shipped` and §5 is complete |
| 2 | `git mv` this branch's artifact set — the spec `P4` resolved, the results artifact `P5` resolved, and the design artifact `P5a` resolved where the spec names one — from `docs/dev/<type>/` to `docs/archive/<type>/`, in a commit of its own, before any merge, subject `docs(closeout): archive the issue #<N> artifact set`. The pointers within the set are relative (`docs/standards/1-workflow.md` §1.5), so the move is a pure rename — `docs/standards/2-git.md` §2.2 | The branch tip carries the set only under `docs/archive/<type>/`, `git status --porcelain` prints nothing, and the commit is a pure rename: `git show --stat` lists each file as a rename with 0 lines changed |
| 3 | `git checkout dev && git merge --no-ff <branch>`; push `dev` — `docs/standards/2-git.md` §2.1, §2.3 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 4 | Bump `workmain/__version__.py` by a minor — both `__version__` and `__version_info__` — and add its `CHANGELOG.md` section, committed on `dev` and, once the check below passes, pushed — `docs/standards/2-git.md` §2.2, §2.5 | Both on `dev` name the version recorded at step 1, and `python3 automation/check_release_integrity.py --no-remote` exits 0 on `dev`, and `dev` equals `origin/dev` |
| 5 | `systemctl --user restart workmain-notify.service` — `docs/standards/2-git.md` §2.6 | `ActiveEnterTimestamp` postdates the step 3 merge commit |
| 6 | `git branch -d <branch>` — `docs/standards/2-git.md` §2.3 | `git rev-parse --verify <branch>` fails |
| 7 | `gh pr create` for `dev → main` — `docs/standards/2-git.md` §2.2 | `gh pr list --base main --head dev --state all` returns it |
| 8 | ⏸ **Authorization — Ray merges the PR.** Answers: *merged*, or *defer*, which exits cleanly | `gh pr view --json state` reads `MERGED` |
| 9 | Fetch `main`; `git tag v<version>` on `main`; push the tag; `gh release create v<version> --generate-notes` — `docs/standards/2-git.md` §2.2 | `git ls-remote --tags origin v<version>` returns the tag and `gh release view v<version>` exits `0` |

## Why this order

Five things about it that this file explains.

- **The archive step comes before the merge.** The set moves on the branch so the rename rides the merge commit; archiving afterwards would mean editing documents directly on `dev` or `main`, where §2.2 allows only merges and the release bump.
- **The version is recorded at step 1 and bumped at step 4.** §2.5 makes the minor bump deterministic from the current `workmain/__version__.py`, so the version and tag are known before they exist.
- **The PR number reaches the issue through the closing comment.** It first exists at step 7, after the results artifact is committed.
- **The restart is at step 5, before the PR.** `dev` carries the code from step 3, so a *defer* at step 8 leaves `dev` deployed.
- **The branch is deleted at step 6.** Its only merge happened at step 3; steps 7–9 work on `dev` and `main`.

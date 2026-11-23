# `chore/*` perform sequence

Reached only after every `SKILL.md` preflight row has passed for a `chore/*` branch. The steps below merge and archive the set, as `docs/standards/2-git.md` §2.2 and §2.6 define for a `chore/*` branch.

| # | Step | Done when |
| --- | --- | --- |
| 1 | Set the spec, the design artifact **where the spec names one**, and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:** n/a`, §5 suite results, live verification. Commit on the branch, before any merge — `docs/standards/2-git.md` §2.2 | The branch tip carries the spec, the results artifact, and any design artifact the spec names, each at `Shipped`, and the results artifact's §5 is complete |
| 2 | `git mv` this branch's artifact set — the spec `P4` resolved, the results artifact `P5` resolved, and the design artifact `P5a` resolved where the spec names one — from `docs/dev/<type>/` to `docs/archive/<type>/`, in a commit of its own, before any merge, subject `docs(closeout): archive the issue #<N> artifact set`. The pointers within the set are relative (`docs/standards/1-workflow.md` §1.5), so the move is a pure rename — `docs/standards/2-git.md` §2.2 | The branch tip carries the set only under `docs/archive/<type>/`, `git status --porcelain` prints nothing, and the commit is a pure rename: `git show --stat` lists each file as a rename with 0 lines changed |
| 3 | ⏸ **Authorization — merge this branch to `main`** | — |
| 4 | `git checkout main && git merge --no-ff <branch>`; push `main` — `docs/standards/2-git.md` §2.1, §2.3 | `git merge-base --is-ancestor <branch> main` succeeds and `main` equals `origin/main` |
| 5 | `git checkout dev && git merge --no-ff <branch>`; push `dev` — `docs/standards/2-git.md` §2.1, §2.3 | `git merge-base --is-ancestor <branch> dev` succeeds and `dev` equals `origin/dev` |
| 6 | `git branch -d <branch>` — `docs/standards/2-git.md` §2.3 | `git rev-parse --verify <branch>` fails |

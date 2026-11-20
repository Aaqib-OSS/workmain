## 2. Git Workflow

### 2.1 Branch strategy

```text
main       — released code. Every release is tagged here.
dev        — integration branch. All feature work merges here first.
feature/*  — new or changed application behaviour: gaps, capability, refactors. From dev, merges to dev.
hotfix/*   — a fix to released behaviour (a `defect`, §1.3). From main, merges to main AND dev.
chore/*    — documentation/process/tooling only. From main, merges to main AND dev.
```

**Branch names are `<type>/issue-<N>-<slug>`.** The issue number is what links a merge commit back to its issue once §2.3 deletes the branch. Every branch serves an issue.

**One branch, one kind of work.**

### 2.2 Branch rules

**`main`**

- Changes arrive only by merge.
- Receives merges from `dev`, `hotfix/*` and `chore/*`.
  - `dev` reaches `main` through a pull request — the `dev` block below.
  - **A `hotfix/*` or `chore/*` branch is merged into `main` locally, and `main` is pushed.** The repository ruleset `main-pr-required` requires a pull request for every change to `main`. This push passes it through the ruleset's bypass for the repository admin role, so GitHub prints `remote: - Changes must be made through a pull request.` and accepts the push. That line is expected on these two branch types; the push succeeded. Only an account with the admin role can make this push.
- **A merge carrying application code — from `dev` or `hotfix/*` — is a release.** It bumps `workmain/__version__.py`, updates `CHANGELOG.md`, is tagged `v<version>`, and gets a GitHub Release. `/closeout` performs all four.
- **A `chore/*` merge skips all four.** It leaves application behaviour unchanged, so its version stays the same.

**`dev`**

- Always equal to, or one feature ahead of, `main`.
- One direct commit: the release bump `/closeout` makes after a feature merge (§2.5).
- **`dev → main` goes through a GitHub PR.**
  - `/closeout` opens the PR and stops. **Ray merges the PR himself**.

**`hotfix/*`**

- Fixes one defect in released behaviour, with one traceable root cause.
- A fix with more than one root cause, or bundled with another concern, is `feature/*`.

**`chore/*`**

- For `docs/**`, standards documents, `.claude/`, and dev tooling that leaves application behaviour unchanged (`.gitignore`, `.githooks/`, `.github/`, `automation/`, editor/CI config).
- **Exception:** a change to `workmain/**`, `tests/**`, or `scripts/**` may use `chore/*` if it is mechanically proven behaviour-neutral (e.g. AST-equality) *and* the governing spec states the proof method.
- Scope: One tightly-related set of files edited for a single reason.

**Operational changes from live use.**

- WorkmAIn is in daily use while it is developed, and some `workmain` commands write tracked files as part of normal operation — `workmain providers set default`, for example, writes `config/ai_settings.json`. The change appears uncommitted on whichever branch is checked out, and sits outside that branch's work.
- It is committed on the next branch to be completed, of any type, before `/closeout` runs: one commit, separate from the branch's own work, typed `chore(config)` or `chore(templates)`, whose body states that it is an operational change made through the CLI.
- It is exempt from spec and acceptance criteria, and sits outside the scope of the branch's issue.
- The merge keeps the release status of its branch type.
- It covers only a file a `workmain` command wrote. A hand edit to `config/` or `templates/` is development, and takes the branch its change requires.

### 2.3 Branch deletion

- `main` and `dev` are the only branches on `origin`. **Working branches stay local** (`feature/*`, `hotfix/*`, `chore/*`) — feature branches merge to `dev` locally.
- A working branch is deleted locally once it has merged everywhere §2.1 sends it. Close-out deletes the local branch only.
**Every merge is `--no-ff`.**

- `--no-ff` guarantees a merge commit.
- The merge commit is the permanent record of the branch: its subject names the branch, and its second parent is the tip.
- Tags, `CHANGELOG.md` and merge commits are the record that outlasts the branch ref.

### 2.4 Commit messages

```text
<type>(<scope>): <short description>
 
<body — what and why. Files changed, decisions made, expected test count.>
 
Co-Authored-By: Claude <model> <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.

- This is the **only** commit format. The subject describes the change; step context goes in the body — `feat(notes): converge write path` with `Step 3 of 7` in the body.
- **Every commit runs the hooks.** `--no-verify` skips them.
- **Stage by path** — `git add <path>`. Ray edits live `config/` in the working tree mid-session, and `git commit -a` sweeps his edit in under your message. Check `git status --short` first; stage only your own files and mention any others.
- **Enforced by `.githooks/commit-msg`.** Enable it once per clone; `.git/hooks/` is outside version control:

```bash
git config core.hooksPath .githooks
```

- The hook exempts merge, revert, and fixup/squash subjects, which git generates itself.
- It validates format; the scope and description are the author's check.

### 2.5 Version bumps

| Merge type | Change | Example |
| --- | --- | --- |
| Hotfix → main | Patch | 1.3.0 → 1.3.1 |
| Feature/phase → dev → main | Minor | 1.3.1 → 1.4.0 |

A release (§2.2 `main`) updates these together:

- `workmain/__version__.py`: `__version__` and `__version_info__`
- `CHANGELOG.md`
**The pre-push hook (`.githooks/pre-push`, running `automation/check_release_integrity.py`) accepts a push only when they agree.**

### 2.6 Deployment

`workmain-notify.service` (systemd `--user`) runs the code checked out in the repository's working tree at the moment it starts (`deploy/workmain-notify.service` `WorkingDirectory`). `/closeout` restarts it with `dev` checked out, so production runs `dev`. A start at any other time, including systemd's `Restart=on-failure`, runs whatever branch is checked out then.

**Every `feature/*` and `hotfix/*` branch ends with a service restart.** The daemon loads code once at process start, so a merge to `dev` deploys at restart.

`/closeout` performs it. A merge is deployed once the service's `ActiveEnterTimestamp` postdates the merge commit.

**The CLI runs the checked-out branch immediately.** `workmain` is an editable install from the repository, so every `workmain` command runs whatever branch is checked out, in its own process. A live check made through the CLI passes on the working branch: where a spec has one that Ray runs, he runs it there, before `/closeout`. Only what the daemon runs — the T1–T6 triggers (`CLAUDE.md` § Trigger Terminology) and Slack Socket Mode — waits for the restart.

### 2.7 Session start checklist

**Work on a working branch, created before the first edit.**

1. `git status` — working directory clean.
2. `git branch` — confirm where you are.
3. Choose the branch type for the work, and its base, from §2.1.
4. `git fetch` — pull requests merge on GitHub, so a local branch falls behind `origin`.
5. `git switch --no-track -c <branch> origin/<base>`, where `<base>` is the branch step 3 names.
   - `--no-track` leaves the branch without an upstream, so `git status`, `git pull` and `git push` act on the working branch alone.

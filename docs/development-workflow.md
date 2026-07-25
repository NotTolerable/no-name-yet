# Verilly Development Workflow

This workflow keeps two-developer collaboration explicit without adding process that does not improve correctness or conflict avoidance.

## Step 1 — Select work

- Choose one PR-sized item from `ROADMAP.md`.
- Create or select one GitHub issue.
- Assign one primary owner and workstream.
- Record dependencies on earlier PRs.
- Declare files that may change and files that must not change.
- Record acceptance criteria, required tests, risks, and explicit non-goals.
- Check that no active issue or branch owns the same architectural boundary.

## Step 2 — Prepare a branch

```powershell
git switch main
git pull
git switch -c feat/<issue-name>
```

Use the applicable `feat/`, `fix/`, `docs/`, or `test/` prefix described in [../CONTRIBUTING.md](../CONTRIBUTING.md).

## Step 3 — Give Codex repository context

Start implementation requests with:

```text
Read AGENTS.md, ROADMAP.md, README.md, docs/architecture.md,
docs/domain-model.md, docs/invariants.md,
docs/development-workflow.md, and docs/workstreams.md before proceeding.

Inspect the current worktree before editing.

Owner:
Issue:
PR:
Goal:
Files allowed:
Files prohibited:
Acceptance criteria:
Required tests:
Non-goals:
```

The remainder of the request should state exact required behavior, including failure behavior and compatibility constraints. Repository documents override assumptions from earlier chat history.

## Step 4 — Implement and verify

- Run focused tests while developing.
- Run the full relevant test suite before completion.
- Run `git diff --check`.
- Run `git diff --stat`.
- Run `git diff --name-only`.
- Inspect the complete diff for secrets, generated files, unrelated changes, unsafe defaults, and accidental boundary violations.
- Report every required command that was not run or did not pass.

Use the repository-specific backend and frontend commands in `AGENTS.md`. External Supabase behavior is not verified by in-memory adapter tests.

## Step 5 — Commit intentionally

```powershell
git status --short
git add <intentional-files>
git diff --cached --stat
git diff --cached
git commit -m "feat(core): add versioned control catalog"
```

Do not use `git add .`. A commit should contain only the files needed for its stated purpose.

## Step 6 — Push and open a PR

```powershell
git push -u origin HEAD
```

Complete the pull-request template with:

- the issue reference;
- summary;
- architectural boundary;
- files changed;
- tests and verification;
- risks;
- explicit non-goals; and
- reviewer notes.

## Step 7 — Review

The other developer reviews:

- behavioral correctness;
- architectural boundaries;
- invariant preservation;
- test quality and negative cases;
- accidental scope expansion;
- duplicated policy or domain logic;
- unsafe defaults; and
- documentation accuracy.

Changes to domain semantics or architectural invariants require both developers to review and agree before merge.

## Step 8 — Merge and synchronize

After merge:

```powershell
git switch main
git pull
git branch -d <merged-branch>
```

Delete the remote branch through GitHub or the chosen merge flow. Do not start dependent work from an outdated branch.

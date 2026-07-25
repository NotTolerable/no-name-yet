# Contributing to Verilly

Verilly is maintained by two developers. The process is intentionally lightweight: one issue, one primary owner, one focused branch, and review by the other developer.

## Before starting

1. Pull the latest `main`.
2. Read `AGENTS.md`, `ROADMAP.md`, `README.md`, `docs/architecture.md`, `docs/domain-model.md`, `docs/invariants.md`, `docs/development-workflow.md`, and `docs/workstreams.md`.
3. Select or create one GitHub issue with PR-sized scope and one primary owner.
4. Record the architectural boundary, allowed files, prohibited files, acceptance criteria, tests, dependencies, and non-goals.
5. Confirm no other active branch is editing the same shared contract or architectural files.

Trivial fixes still need clear scope and verification, but do not require a separate design document.

## Branch naming

Use:

```text
feat/<short-feature-name>
fix/<short-fix-name>
docs/<short-documentation-name>
test/<short-test-name>
```

Examples:

```text
feat/control-catalog
feat/control-assessment
feat/workflow-contracts
feat/langgraph-orchestration
docs/team-development-workflow
```

## Commit conventions

Make small, intentional commits. Use a prefix that identifies the affected boundary:

```text
feat(core):
feat(workflow):
feat(api):
feat(ui):
fix(core):
test(core):
docs:
```

Stage named files or paths intentionally. Do not use `git add .`.

## Pull requests

Every pull request must:

- correspond to one issue;
- have one primary owner;
- stay within the declared file scope;
- include tests for changed behavior;
- identify affected architectural boundaries;
- list explicit non-goals;
- update documentation when contracts change;
- receive review from the other developer; and
- avoid unrelated formatting, cleanup, or generated files.

Domain semantics and architectural invariants require review from both developers. Resolve scope overlap before implementation rather than during merge conflict resolution.

## Merge rules

The recommended workflow is:

- open pull requests into `main`;
- do not push implementation changes directly to `main`;
- squash-merge small focused PRs, or use a regular merge when meaningful commits should remain visible;
- delete merged branches; and
- update local `main` before starting the next branch.

These are repository conventions. GitHub branch protection is not currently documented as configured and must be enabled separately if the maintainers want enforcement.

See [docs/development-workflow.md](docs/development-workflow.md) for the full lifecycle and [docs/workstreams.md](docs/workstreams.md) for ownership boundaries.

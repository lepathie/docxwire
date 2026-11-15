# Proposal

## Why

The dispatch-based CI re-trigger works (verified on the openspec-v2 PR) but is fragile by construction: the PR's checks view is bound to the check suite created by the `pull_request` event, so a `workflow_dispatch` run only surfaces its checks if it races the event-suite lifecycle correctly — two incidents (PRs #12, #13) and a `GH_REPO` workaround were the price. The standard GitHub pattern removes the race entirely: run `ci.yaml` natively on `pull_request`. Then the PR's checks *are* the event run's own check runs — no dispatch, no mirroring, no suite-binding fragility.

## What Changes

- `ci.yaml`:
  - Gains a `pull_request: { branches: [main] }` trigger; PRs get their checks natively.
  - The `publish-pr-checks` mirroring job is removed (it existed only to surface the dispatched run's conclusions on the PR).
  - `lint-pr-title` runs natively on PRs (title from `github.event.pull_request.title`) instead of via a `workflow_dispatch` input; `workflow_dispatch` remains, bare, for manual re-runs.
- `pr-orchestrator.yaml`:
  - The `retrigger-ci` job and the `Re-trigger CI` step are removed; the `pushed`-tracking outputs and step ids go with them.
  - `post-upgrade-tasks` becomes a pure auto-fix job: it keeps the fix steps and the fix-loop guard, drops the `actions: write` permission, and no longer re-triggers anything — the fix push's `synchronize` event gives the PR its checks natively.
- Fork PRs now also get native CI (no secrets are involved in the CI jobs); the auto-fix remains non-fork only.

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

(None)

## Impact

- Workflow files only: `.github/workflows/ci.yaml`, `.github/workflows/pr-orchestrator.yaml`. No product code, Makefile, or branch-protection changes; the required-check names (`lint`, `test`, `check-specs`, `check-deps`, `lint-pr-title`) are unchanged and now satisfied natively.
- Runner usage is of the same order as today (PRs already got a re-triggered CI run); fork PRs add runs.
- Rollback is a revert of the two workflow files.

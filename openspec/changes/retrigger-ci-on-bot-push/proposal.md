# Proposal

## Why

GitHub's PR checks view is bound to the check suite created by the PR's `pull_request` event — not the most recent suite for the head commit. When the PR Orchestrator pushes an auto-fix to a PR branch (e.g. regenerating stale OpenSpec skill files after a Renovate bump of `@fission-ai/openspec`), the CI re-trigger is dispatched from the *first* orchestrator run — before the new head's event suite exists (the `synchronize` webhook from the bot push is processed seconds later). All CI check runs therefore land in orphaned suites that are invisible to the PR. The *second* orchestrator run — whose event suite is the one the PR displays — is skipped entirely by the fix-loop guard and never re-triggers CI, so the PR shows only a skipped `post-upgrade-tasks` check. Observed on PR #12: every CI job passed on the final head, yet none were reported on the PR, the required checks were never satisfied, and the merge stayed blocked. Manual `gh workflow run` re-triggers cannot repair the display, because a `workflow_dispatch` run always creates its own suite.

## What Changes

- Split the CI re-trigger out of `post-upgrade-tasks` so it always happens in the **last** orchestrator run for a given PR head:
  - New `retrigger-ci` job: runs when the run is the bot's own fix push (non-fork PR, `github.actor == 'github-actions[bot]'`) and re-triggers `ci.yaml` on the PR branch.
  - `post-upgrade-tasks`: its re-trigger step becomes conditional on **no fix having been pushed** (tracked via job outputs); when it does push a fix, the incoming `synchronize` run performs the re-trigger instead.
- Net effect: in the fix flow the re-trigger is dispatched from the run for the new head, while that head's `pull_request` event suite is open, so the CI check runs land in the suite the PR displays. Exactly one CI dispatch per head SHA in the common single-fix case, and the PR's checks view shows the complete CI result.

## Capabilities

### New Capabilities

- `pr-checks`: Every pull request to `main` has its CI check runs reported in the PR's checks view, including after the orchestrator pushes an auto-fix to the PR branch.

### Modified Capabilities

(None)

## Impact

- `.github/workflows/pr-orchestrator.yaml`: job split (`post-upgrade-tasks` + `retrigger-ci`), actor guard moved from job level to the fix steps, new job outputs gating the re-trigger.
- No changes to `ci.yaml`, the Makefile, or product code.
- Bot-push runs additionally surface a `retrigger-ci` check in the PR's checks view.
- Verification: the next PR in which the orchestrator pushes a fix must show the full CI checks and be mergeable; PR #12 is unblocked by a trivial push to its branch, which re-runs the existing (working) no-fix path.

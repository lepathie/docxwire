# Design

## Context

See proposal.md for motivation. The current (verified) design re-triggers `ci.yaml` via `gh workflow run` from the PR Orchestrator. It works but depends on a timing property: the PR's checks view is bound to the check suite created by the `pull_request` event, and a dispatched run's check runs only appear on the PR if they land in that suite while it is open. That is the source of the PR #12 / #13 incidents and the `GH_REPO` workaround. `ci.yaml` currently triggers on `push: main` and `workflow_dispatch` only — it does not run natively on PRs, which is why the re-trigger exists at all.

## Goals / Non-Goals

**Goals:**

- PRs get their CI checks from a native `pull_request` run, so the checks are the event suite's own runs — no dispatch, no mirroring, no suite race.
- The orchestrator shrinks to a pure auto-fix job.
- Required-check names stay identical so branch protection is unaffected.

**Non-Goals:**

- Changing which make targets run, their tooling, or the `ci` / `check` aggregation.
- Changing branch-protection configuration.
- Restricting CI from fork PRs (accepted to run natively; see Risks).

## Decisions

1. **Add `pull_request: { branches: [main] }` to `ci.yaml`.** This is the standard pattern and the core of the simplification. A PR's head gets a native check suite whose runs are exactly the PR's checks; a bot fix push (a `synchronize`) creates a new suite for the new head and runs natively against it. The dispatch and its fragility disappear.
2. **Remove `publish-pr-checks`.** It existed solely to mirror a dispatched run's job conclusions onto the PR as check runs. With a native run, the real check runs are already on the PR, so the mirror is redundant and is deleted (along with its `checks: write` permission).
3. **Rework `lint-pr-title` to run natively on PRs.** Its `if` becomes `github.event_name == 'pull_request'` and the title comes from `github.event.pull_request.title`. The `workflow_dispatch` `pr_title` input is dropped; a bare `workflow_dispatch` remains for manual re-runs (on a manual dispatch there is no PR, so `lint-pr-title` is simply skipped).
4. **Reduce the orchestrator to pure auto-fix.** Delete the `retrigger-ci` job and the `Re-trigger CI` step. `post-upgrade-tasks` keeps its two fix steps and the fix-loop guard, drops the `actions: write` permission (no `gh workflow run` anymore) and the `pushed`-tracking outputs/step ids. A fix push triggers `synchronize`, and the native `ci.yaml` run gives the PR its checks on the fixed head.
5. **Let fork PRs run CI natively.** The CI jobs need no secrets, so there is no read-only-token problem for *running* them (that problem only applied to the orchestrator pushing fixes). Fork PRs therefore get native CI; `post-upgrade-tasks` still skips forks because it must push.

## Risks / Trade-offs

- [CI now also runs on fork PRs] → No secrets are consumed by these jobs; this is standard practice and the runner cost is acceptable for this repo. The auto-fix (the only secret/push-sensitive part) remains non-fork only.
- [A merged PR triggers both a final `pull_request` run and a `push: main` run] → Harmless duplication, same as today's re-trigger plus the push run.
- [Removing the re-trigger changes when a fix push gets its checks] → The `synchronize` from the fix push now triggers the native run directly, so the fixed head is checked without any extra dispatch — strictly more direct than before.

## Migration Plan

- Two workflow-file edits; take effect on the next `pull_request` / `push` event. No data migration.
- Validate on the next PR (e.g. the next Renovate bump): the PR shows native checks, and a bot fix push produces a new native run on the fixed head with no `retrigger-ci` job.
- Rollback: revert the two workflow files.

## Open Questions

(None)

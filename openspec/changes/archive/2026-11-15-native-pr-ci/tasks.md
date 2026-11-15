# Tasks

## 1. `ci.yaml` — native PR checks

- [x] 1.Add a `pull_request: { branches: ["main"] }` trigger; reduce `workflow_dispatch` to bare (drop the `pr_title` input)
- [x] 1.Remove the `publish-pr-checks` job (and its `checks: write` permission)
- [x] 1.Rework `lint-pr-title` to run natively: `if: github.event_name == 'pull_request'`, title from `github.event.pull_request.title`
- [x] 1.Update the header comment: PRs get their checks natively from the `pull_request` trigger

## 2. `pr-orchestrator.yaml` — pure auto-fix

- [x] 2.Remove the `retrigger-ci` job
- [x] 2.In `post-upgrade-tasks`: remove the `Re-trigger CI` step, the `pushed`-tracking outputs and step ids, and the `actions: write` permission
- [x] 2.Update the header comment: the orchestrator only auto-fixes stale generated files; PRs get their checks natively (a fix push's `synchronize` event runs `ci.yaml` on the fixed head)

## 3. Verification

- [x] 3.1 Both workflow files parse as valid YAML; walk the trigger matrix: (a) human PR → native `ci.yaml` run, no orchestrator re-trigger; (b) bot fix push → `synchronize` → native `ci.yaml` run on the fixed head, `post-upgrade-tasks` skipped; (c) fork PR → native CI runs, `post-upgrade-tasks` skipped
- [x] 3.2 On the next PR (e.g. the next Renovate bump), verify the PR shows native checks and, if the orchestrator pushes a fix, the fixed head is checked natively with no `retrigger-ci` job

## Workflow follow-up

- Archive this change once 3.2 is confirmed on a live PR.

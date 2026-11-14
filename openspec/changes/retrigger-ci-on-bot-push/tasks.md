# Tasks

## 1. Workflow change (`.github/workflows/pr-orchestrator.yaml`)

- [x] 1.Add a `retrigger-ci` job: `if: github.event.pull_request.head.repo.fork == false && github.actor == 'github-actions[bot]'`, `permissions: actions: write`, single step running `gh workflow run ci.yaml --ref "$BRANCH" -f "pr_title=$PR_TITLE"` with `BRANCH` / `PR_TITLE` / `GH_TOKEN` env (no checkout — branch and title come from the event payload)
- [x] 1.Give the two fix steps explicit ids (`regenerate`, `bump`) and have each write `echo "pushed=true" >> "$GITHUB_OUTPUT"` in its push branch
- [x] 1.Gate the `Re-trigger CI` step in `post-upgrade-tasks` on no fix having been pushed: `if: ${{ steps.regenerate.outputs.pushed != 'true' && steps.bump.outputs.pushed != 'true' }}`
- [x] 1.Update the workflow's header comment to document the placement rule: the re-trigger always happens in the last orchestrator run for a PR head (in-sync run, or the bot's own fix-push run)

## 2. Verification

- [x] 2.Validate the YAML parses (e.g. `python3 -m yaml ... ` / `openspec`-independent parse) and walk the trigger matrix by hand: (a) in-sync human PR → one re-trigger from `post-upgrade-tasks`; (b) fix push → re-trigger only from the bot-push run's `retrigger-ci`; (c) fork PR → no fix, no re-trigger
- [x] 2.Unblock PR #12: push a trivial commit (e.g. empty commit) to `renovate/fission-ai-openspec-1.x` and verify the PR's checks view then shows all CI checks (lint, test, check-specs, check-deps, lint-pr-title) green and the PR becomes mergeable
- [ ] 2.3 On the next PR in which the orchestrator pushes a fix, verify the PR's checks view shows the full CI result for the fixed head and the PR is mergeable without manual intervention

## Workflow follow-up

- Archive this change (move to `changes/archive/` + spec sync) once 2.3 is confirmed on a live fix-flow PR.

# Design

## Context

See proposal.md for the motivation. The constraints that shape the approach:

- GitHub's PR checks view (`statusCheckRollup`) is bound to the **check suite created by the PR's `pull_request` event** for the head commit — not the most recent suite. A re-triggered CI run's check runs only become visible in the PR when they land in *that* suite, which requires the suite to be open when the CI run starts. A `workflow_dispatch` run whose dispatch missed the open window always creates its own (orphaned) suite.
- The `pull_request` event suite for a new head is created with a few seconds of webhook latency after the push. The orchestrator run for that head, by contrast, starts immediately and stays alive (checkout → setup-node → `npm ci` → …) well beyond that window; its event suite stays open at least until the run's job completes.
- Empirical timing (this repo, Nov 2026):
  - PR #9 (worked): event suite created `01:10:41`; re-trigger dispatched `01:10:53` from the in-sync run; suite closed `01:10:57`. The CI check runs landed in the event suite → full checks visible.
  - PR #12 (broke): run #1 dispatched the CI at `02:47:52` for a head whose event suite was only created `02:47:56` → CI runs orphaned. Run #2 (owner of the visible event suite) was skipped by the fix-loop guard → no re-trigger → PR showed only a skipped `post-upgrade-tasks`.
- `ci.yaml` runs on `push: main` + `workflow_dispatch` only; the orchestrator's `gh workflow run ci.yaml --ref <branch>` is the only way PRs get CI runs. The branch ref resolves to the branch's current head at dispatch time.

## Goals / Non-Goals

**Goals:**

- In the auto-fix flow, the CI re-trigger is dispatched from the run for the new head, while that head's event suite is open, so the CI check runs land in the suite the PR displays.
- Exactly one CI dispatch per head SHA in the common single-fix case; no push loop; fork PRs untouched.

**Non-Goals:**

- Changing `ci.yaml`'s job layout or the `publish-pr-checks` mirroring (the cosmetic duplication of mirrored check runs in orphaned suites is accepted).
- Changing branch-protection configuration.
- Guaranteeing visibility in edge cases where GitHub's suite-attachment timing changes server-side.

## Decisions

1. **Re-trigger in the last run for the head — implemented as a job split in `pr-orchestrator.yaml`:**
   - New `retrigger-ci` job, `if: fork == false && github.actor == 'github-actions[bot]'`: a single step running `gh workflow run ci.yaml --ref "$BRANCH" -f "pr_title=$PR_TITLE"`. Needs `permissions: actions: write`.
   - `post-upgrade-tasks` keeps the fix steps, but its re-trigger step becomes `if:`-gated on **no fix having been pushed** (see decision 3).
   - Rationale: the re-trigger from the bot-push run is dispatched ~15–30 s after the event suite is created, while the suite is still open (it stays open at least until the run's job completes, which is after the re-trigger step — the last step of the job). PR #9 demonstrates this timing works in practice.
   - Alternative considered: keep one job and make the job-level guard `actor != bot`-only while moving the re-trigger into a step that also runs for bot-actor runs. Rejected: one job cannot express "fix steps skipped, re-trigger runs" for bot-actor runs without step-level guards on every step, which is less readable than two jobs with clear one-line `if:`s.

2. **The actor guard stays at job level; `retrigger-ci` is deliberately minimal.** `post-upgrade-tasks` keeps its current job-level `if:` (non-fork, non-bot) — the fix steps only ever run for non-bot runs, so no step-level guards are needed. `retrigger-ci` is the only job that runs for bot-actor runs and is deliberately cheap: a single `gh workflow run` step with no checkout / setup-node / `npm ci` (the branch name and PR title come from the event payload, not the workspace).

3. **Push tracking via step outputs.** Each fix step writes `echo "pushed=true" >> "$GITHUB_OUTPUT"` when it commits and pushes. The re-trigger step's condition is `if: ${{ steps.regenerate.outputs.pushed != 'true' && steps.bump.outputs.pushed != 'true' }}` (the two step outputs OR-combined), so a run that pushed a fix leaves the re-trigger to the incoming `synchronize` run.

4. **Accepted duplication when both fix steps push.** Two pushes → two `synchronize` runs → two `retrigger-ci` dispatches. The two fixes are mutually exclusive in practice (documented in the `centralize-node-version` design); if both ever fire, the last dispatch targets the final head and wins the PR display. No deduplication mechanism is added.

## Risks / Trade-offs

- [Inherent race: the event suite closes when the run's job check run is recorded, which happens shortly after the re-trigger step dispatches the CI] → The dispatch happens while the suite is open by construction (re-trigger is the last step); PR #9 shows the CI check runs registering inside the window. If GitHub changes suite-attachment semantics, the PR display regresses — caught by the verification task on the next fix-flow PR.
- [The PR's checks view gains a `retrigger-ci` check on bot-push runs] → Cosmetic; it is informative (shows the re-trigger happened) and its conclusion does not gate merging as long as branch protection lists the CI check names.
- [A `retrigger-ci` run with a failed `gh workflow run` (e.g. API rate limit) leaves the PR without CI] → Same failure mode as today's re-trigger step; no additional handling in this change.

## Migration Plan

- Workflow-file-only change; takes effect on the next `pull_request` event. No data migration.
- Interim unblock for PR #12 (pre-merge): a trivial push to its branch (e.g. an empty commit) re-runs the existing, proven no-fix path — the in-sync run re-triggers CI while the new head's event suite is open, restoring the visible checks and the merge.
- Rollback: revert the workflow file; the previous behavior (and its failure mode) is restored.

## Open Questions

(None)

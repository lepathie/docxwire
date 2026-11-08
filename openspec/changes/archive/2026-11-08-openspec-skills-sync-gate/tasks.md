# Tasks

## 1. Verify sync precondition

- [x] 1.1 Verify the committed generated files are in sync with the pinned CLI: `./node_modules/.bin/openspec update --dry-run --json` reports `"changes": []`, so the gate is green on merge

## 2. CI pipeline (`ci.yaml`)

- [x] 2.1 Add the `Check generated OpenSpec files are in sync` step (exact text in design.md) after `Validate OpenSpec artifacts` in the `openspec` job of `.github/workflows/ci.yaml`, and verify the workflow YAML still parses and the step asserts `jq '.changes | length'` equals 0
- [x] 2.2 Change the `on:` block of `.github/workflows/ci.yaml`: remove the `pull_request` trigger and add a `workflow_dispatch:` with a `pr_title` input (string, not required); verify the workflow YAML still parses
- [x] 2.3 Move the `lint-pr-title` job from `.github/workflows/commitlint.yaml` into `ci.yaml` (exact text in design.md): gated on `workflow_dispatch` with a non-empty `pr_title`, title fed from the input; verify the workflow YAML still parses
- [x] 2.4 Verify the gate fires: in a scratch copy of the repo (never the real one), modify a generated `.agents/skills/openspec-*/SKILL.md` file and confirm the new step's command fails there, and passes in the unmodified copy

## 3. Commit lint (`commitlint.yaml`)

- [x] 3.1 Remove the `lint-pr-title` job and the `pull_request` trigger from `.github/workflows/commitlint.yaml` (the job moved to `ci.yaml` in 2.3); verify the workflow YAML still parses and the `lint-commits` push-to-`main` job is intact

## 4. Auto-regeneration

- [x] 4.1 Add `.github/workflows/openspec-regenerate.yaml` (exact text in design.md) and verify it parses: `pull_request` (opened/synchronize/reopened) to `main`, fork + bot-actor guard, `contents: write` + `actions: write`, `head_ref` checkout, scoped `git add .agents/skills`, conventional commit message, and the unconditional retrigger step passing `pr_title`
- [x] 4.2 Verify the no-op path in a scratch copy of the repo (never the real one): with the generated files in sync, no commit and no push happen, but the retrigger step still dispatches the pipeline with the PR title
- [x] 4.3 Verify the fix path live on GitHub: in a scratch PR, bump `@fission-ai/openspec` (or simulate staleness by hand-editing a generated file) and confirm: the regenerate job pushes a bot commit to the PR branch → the pipeline is triggered on the updated head → all three checks (`lint-and-test`, `openspec`, `lint-pr-title`) are green there → the PR is mergeable — verified on PR #9 (`renovate/fission-ai-openspec-1.x`, 1.16.0 → 1.16.1): bot commit landed, pipeline retriggered on the fixed head, all three checks green and attributed; the only remaining gate is the repo's own `renovate/stability-days` (7-day `minimumReleaseAge`), which releases the automerge on its schedule

## 5. Integration

- [x] 5.1 Run `make ci` and `openspec validate --all`, and verify both exit 0
- [x] 5.2 Verify (no change needed) that the branch-protection required set `{lint-and-test, openspec, lint-pr-title}` is intact and is satisfied by the retriggered pipeline on the fixed head

## 6. Fresh-environment gate fix (found on first live run)

- [x] 6.1 Filter the gate (`ci.yaml`) and the staleness condition (`openspec-regenerate.yaml`) to in-repo paths — `jq '[.changes[] | select(.path | startswith("~") | not)] | length'` — because in a fresh CI environment the CLI's first run plans to create the machine-global `~/.config/openspec/config.json` (profile/delivery are machine-global; no project-level config exists for them), which the unfiltered count reported as a change on every run
- [x] 6.2 Verify in fresh-environment simulations: in sync → 0 counted changes, stale → exactly the seven `.agents/skills/**` paths; a real `openspec update` in a fresh environment touches nothing (in sync) or only `.agents/skills/**` (stale) — no command files, no extra workflows
- [x] 6.3 Record in design.md the filter decision (machine-global config, `~/**` paths excluded) and the core-scoping guarantee (scoped `git add .agents/skills` + `core` profile default)

## 7. Retrigger auth fix (found on first live PR)

- [x] 7.1 Set `GH_TOKEN: ${{ github.token }}` on the retrigger step of `openspec-regenerate.yaml` — the first live run failed with `gh: … set the GH_TOKEN environment variable` because `gh` in an Actions run authenticates from `GH_TOKEN`, not the job's `GITHUB_TOKEN`; the token carries the `actions: write` scope from the job's `permissions:` block

## 8. PR check attribution fix (found on first live PRs)

- [x] 8.1 Add a `publish-pr-checks` job to `ci.yaml` that mirrors the three job conclusions (`lint-and-test`, `openspec`, `lint-pr-title`) as explicit check runs on the PR head — `POST /repos/{owner}/{repo}/check-runs` with `head_sha` = the dispatched head SHA and conclusions mapped from `needs['<job>'].result` — because per GitHub's docs, checks from a `workflow_dispatch` run are never attributed to a PR's required checks, while an explicit check-run POST on an open PR's head is

## 9. Wrap-up (cosmetics + risk, found on first merged PR #9)

- [x] 9.1 Rename the workflow to `PR Orchestrator` (file `pr-orchestrator.yaml`) and its job to `openspec-skills-sync`, with a comment explaining the job's role; verify the workflow YAML still parses
- [x] 9.4 Rename the `openspec` job in `.github/workflows/ci.yaml` to `openspec-validate` and update the `publish-pr-checks` `needs:`/env references; verify the workflow YAML still parses
- [x] 9.5 Rename the mirrored check to `openspec-validate` in the `publish-pr-checks` job so every PR check line matches a real job name; the branch-protection required entry `openspec` is renamed to `openspec-validate` by the owner in a one-off manual update done in sync with the merge
- [x] 9.2 Update the `pr_title` input description in `.github/workflows/ci.yaml` to reference the PR Orchestrator workflow
- [x] 9.3 Record in design.md the suite-folding display decision (the PR UI groups the mirrored CI checks under the workflow's name; the display name is the only safe lever) and the PR #9 risk (bot-fix head: API rollup green and attributed, UI/rollup divergence unexplained, manual rebase the known workaround)

## Workflow follow-up

- Archive the change once the project's review requirements are satisfied (per repo rules, the archive is the owner's own commit).

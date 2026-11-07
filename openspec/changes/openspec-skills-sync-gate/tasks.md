# Tasks

## 1. Verify sync precondition

- [ ] 1.1 Verify the committed generated files are in sync with the pinned CLI: `./node_modules/.bin/openspec update --dry-run --json` reports `"changes": []`, so the gate is green on merge

## 2. CI pipeline (`ci.yaml`)

- [ ] 2.1 Add the `Check generated OpenSpec files are in sync` step (exact text in design.md) after `Validate OpenSpec artifacts` in the `openspec` job of `.github/workflows/ci.yaml`, and verify the workflow YAML still parses and the step asserts `jq '.changes | length'` equals 0
- [ ] 2.2 Change the `on:` block of `.github/workflows/ci.yaml`: remove the `pull_request` trigger and add a `workflow_dispatch:` with a `pr_title` input (string, not required); verify the workflow YAML still parses
- [ ] 2.3 Move the `lint-pr-title` job from `.github/workflows/commitlint.yaml` into `ci.yaml` (exact text in design.md): gated on `workflow_dispatch` with a non-empty `pr_title`, title fed from the input; verify the workflow YAML still parses
- [ ] 2.4 Verify the gate fires: in a scratch copy of the repo (never the real one), modify a generated `.agents/skills/openspec-*/SKILL.md` file and confirm the new step's command fails there, and passes in the unmodified copy

## 3. Commit lint (`commitlint.yaml`)

- [ ] 3.1 Remove the `lint-pr-title` job and the `pull_request` trigger from `.github/workflows/commitlint.yaml` (the job moved to `ci.yaml` in 2.3); verify the workflow YAML still parses and the `lint-commits` push-to-`main` job is intact

## 4. Auto-regeneration

- [ ] 4.1 Add `.github/workflows/openspec-regenerate.yaml` (exact text in design.md) and verify it parses: `pull_request` (opened/synchronize/reopened) to `main`, fork + bot-actor guard, `contents: write` + `actions: write`, `head_ref` checkout, scoped `git add .agents/skills`, conventional commit message, and the unconditional retrigger step passing `pr_title`
- [ ] 4.2 Verify the no-op path in a scratch copy of the repo (never the real one): with the generated files in sync, no commit and no push happen, but the retrigger step still dispatches the pipeline with the PR title
- [ ] 4.3 Verify the fix path live on GitHub: in a scratch PR, bump `@fission-ai/openspec` (or simulate staleness by hand-editing a generated file) and confirm: the regenerate job pushes a bot commit to the PR branch → the pipeline is triggered on the updated head → all three checks (`lint-and-test`, `openspec`, `lint-pr-title`) are green there → the PR is mergeable

## 5. Integration

- [ ] 5.1 Run `make ci` and `openspec validate --all`, and verify both exit 0
- [ ] 5.2 Verify (no change needed) that the branch-protection required set `{lint-and-test, openspec, lint-pr-title}` is intact and is satisfied by the retriggered pipeline on the fixed head

## Workflow follow-up

- Archive the change once the project's review requirements are satisfied (per repo rules, the archive is the owner's own commit).

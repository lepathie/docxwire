# Tasks

## 1. Single source of truth

- [x] 1.1 Add `.nvmrc` at the repo root containing `26`; verify the file exists and its only content is `26`

## 2. CI workflows read the file

- [x] 2.1 In `.github/workflows/ci.yaml`, replace every `node-version: 22` with `node-version-file: .nvmrc`, keeping `cache: npm`; verify the YAML still parses and every `setup-node` step references the file
- [x] 2.2 In `.github/workflows/commitlint.yaml`, replace `node-version: 22` with `node-version-file: .nvmrc`; verify the YAML still parses
- [x] 2.3 In `.github/workflows/pr-orchestrator.yaml`, replace `node-version: 22` with `node-version-file: .nvmrc`; verify the YAML still parses

## 3. Correct the engines floor

- [x] 3.1 Change `engines.node` in `package.json` from `>=22` to `>=22.12.0`; verify the value equals the strictest minimum in `package-lock.json` (recompute the max lower bound across all `engines.node` entries and confirm it is `22.12.0`)

## 4. Guard the engines floor (CI)

- [x] 4.1 Add `semver` to `devDependencies` in `package.json` (exact `7.8.6`, matching the repo's pin convention) and update `package-lock.json`; verify `npm ls semver` resolves it as a direct devDependency
- [x] 4.2 Add `scripts/check-node-engines.mjs` with a **check** mode (exit non-zero, naming the offending package, when the declared floor is lower than the lockfile's strictest minimum via `semver.minVersion`) and a **fix** mode (`--fix`: rewrite `engines.node` to the computed floor, exit 0); verify check mode exits 0 on the current tree and fix mode corrects a lowered floor in a scratch copy
- [x] 4.3 Break the `Makefile` into per-check targets — `lint`, `check-specs` (`openspec validate --all` + generated-files-in-sync), `check-deps` (engines guard) — with `check` aggregating them and `ci` = `check` + `test`; restructure `.github/workflows/ci.yaml` to one job per target (`lint`, `test`, `check-specs`, `check-deps`, in parallel) replacing the monolithic-`make ci` `lint-and-test` job and the `openspec-validate` / `check-dependencies` jobs, and update `publish-pr-checks` needs/mirror to the five check jobs; verify `make ci` passes and the workflow YAML still parses
- [x] 4.4 Verify the guard fires: in a scratch copy of the repo (never the real one), lower `engines.node` below the tree floor and confirm check mode exits non-zero naming the offender, then restore

## 5. Auto-bump the engines floor (PR orchestrator)

- [x] 5.1 In `.github/workflows/pr-orchestrator.yaml`, add a "Bump `engines.node` if stale" step to the sync job — run the check; on failure run `--fix`, `git add package.json`, commit (`chore(deps)`), and push — placed before the shared re-trigger step; verify the YAML still parses
- [x] 5.2 Rename the job `openspec-skills-sync` → `post-upgrade-tasks` (after Renovate's postUpgradeTasks) and update the workflow's header comment to cover both the skills regeneration and the floor bump; verify the YAML still parses and the re-trigger remains a single shared step (one `ci.yaml` dispatch per PR)
- [ ] 5.3 Verify the auto-bump live: in a scratch PR that raises the floor (bump a floor-raising dep, or simulate by lowering `engines.node`), confirm the job pushes a bot commit raising `engines.node` and the re-triggered `ci.yaml` run is green

## 6. Integration

- [x] 6.1 Run `make ci` and verify it exits 0 (the local aggregate of all the CI checks: `lint`, `check-specs`, `check-deps`, `test`)
- [ ] 6.2 Verify the Node jobs resolve Node 26 from `.nvmrc`: the push-to-`main` `ci.yaml` run (or a manual `workflow_dispatch`) is green with the `check-specs` / `check-deps` / `lint-pr-title` jobs executing `make check-specs` / `make check-deps` / commitlint on Node 26

## 7. Superseded PRs

- [ ] 7.1 Close Renovate PRs #5 (→24) and #6 (→26) as obsolete; verify both report closed
- [ ] 7.2 In sync with the merge, update the branch-protection required checks: `lint-and-test` → `lint` + `test`, `openspec-validate` → `check-specs` (`check-deps` optional); verify the setting

## Workflow follow-up

- Archive the change once the project's review requirements are satisfied (per repo rules, the archive is the owner's own commit).

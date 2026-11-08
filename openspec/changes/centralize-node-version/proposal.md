# Proposal

## Why

The Node.js version is declared in four independent places — a hardcoded `node-version: 22` in each of the three workflow files (`ci.yaml` ×2, `commitlint.yaml`, `pr-orchestrator.yaml`) — with no single source of truth, and the `engines.node` floor in `package.json` (`>=22`) is looser than the locked dependency tree actually requires (the `@commitlint/*` 21.x family needs `>=22.12.0`). With Renovate about to bump the CI Node major (PRs for 24 and 26 both in flight), the duplicated literals will drift from each other and from the real floor. Consolidating on one file now makes the version a single value that CI and local dev share and that Renovate keeps current. Relatedly, nothing keeps the `engines.node` floor truthful: a dependency bump that raises the tree's Node minimum would silently leave the declared floor too low. This change adds a CI guard for that invariant and auto-heals it through the PR orchestrator, mirroring the existing OpenSpec-skills auto-regeneration.

## What Changes

- Add `.nvmrc` containing `26` as the single source of truth for the Node.js version.
- Replace the hardcoded `node-version: 22` with `node-version-file: .nvmrc` in all three workflow files (all four Node jobs in `ci.yaml`, `commitlint.yaml`, `pr-orchestrator.yaml`), so every CI job reads the version from the one file.
- Correct `engines.node` in `package.json` from `>=22` to `>=22.12.0` — the strictest minimum actually required by the locked dependency tree.
- Add `scripts/check-node-engines.mjs` (using the canonical `semver` package's `minVersion()`; `semver` added as a devDependency) in two modes: **check** — fails when the declared `engines.node` floor is lower than the strictest Node minimum in `package-lock.json` (runs as the `make check-deps` target, invoked by the `check-deps` job in `ci.yaml`; `--fix` wired into `make fix`); and **fix** — rewrites `engines.node` to the computed floor.
- Break the `Makefile` down into per-check targets — `lint`, `test`, `check-specs` (OpenSpec artifact validation + generated-files-in-sync), `check-deps` (engines floor) — with `make check` aggregating them and `make ci` = `check` + `test`, so local `make ci` runs exactly what CI runs. `ci.yaml` calls those targets from one job each (`lint`, `test`, `check-specs`, `check-deps`, running in parallel), replacing the monolithic-`make ci` `lint-and-test` job and the `openspec-validate` / `check-dependencies` jobs; `publish-pr-checks` mirrors the five check jobs.
- Auto-bump the floor in the PR orchestrator: the `pr-orchestrator.yaml` sync job gains a "bump `engines.node` if stale" step (fix mode → commit → push to the PR branch) alongside its existing OpenSpec-skills regeneration, before its single shared CI re-trigger. The job is renamed `openspec-skills-sync` → `post-upgrade-tasks` (after Renovate's postUpgradeTasks) to reflect that it now performs both fixes.
- Supersedes the two in-flight Renovate node PRs (#5 → 24, #6 → 26): both edit the `node-version` literals this change removes, so both are closed as obsolete.

## Capabilities

### New Capabilities

(None — tooling change, `skip_specs: true`)

### Modified Capabilities

(None)

## Impact

- Files: new `.nvmrc` and `scripts/check-node-engines.mjs`; `node-version` → `node-version-file` in `.github/workflows/ci.yaml` (4 jobs), `.github/workflows/commitlint.yaml`, and `.github/workflows/pr-orchestrator.yaml`; `ci.yaml` restructured to one job per make target (`lint`, `test`, `check-specs`, `check-deps`) with `publish-pr-checks` mirroring the five check jobs; a new auto-bump step plus a job rename (`openspec-skills-sync` → `post-upgrade-tasks`) in `pr-orchestrator.yaml`; `engines.node` and a new `semver` devDependency in `package.json` (and `package-lock.json`); `Makefile` broken down into `lint` / `check-specs` / `check-deps` targets (aggregated by `check`, `ci` = `check` + `test`), the old `check` / `openspec-validate` / `check-node-engines` targets replaced, and `--fix` + `openspec update` wired into `make fix`.
- Effect: CI and local dev read one Node version; future Renovate node bumps update `.nvmrc` (a file Renovate manages) and CI follows automatically. The `engines.node` floor is guarded in CI and auto-healed on PRs, so it can no longer silently drift below the dependency tree's real minimum.
- CI moves 22 → 26 in one step (26 is the current active LTS); the intermediate 24 step is skipped. The Node jobs run the same tools (OpenSpec CLI, commitlint) on the newer runtime.
- No product/runtime code changes. The `lint-and-test` job splits into `lint` and `test` jobs calling their specific targets; the Node jobs (`check-specs`, `check-deps`) call theirs — no check runs twice, and `make ci` is the local aggregate of exactly the targets CI runs; `semver` is already in the lockfile as a transitive dependency (so no new transitive code is added).
- Branch protection: the required-check entries `lint-and-test` and `openspec-validate` go dangling when their jobs are renamed/split — the owner updates the required set in a one-off manual update in sync with the merge (`lint` + `test` + `check-specs`, `check-deps` optional; the automation token has no admin scope).

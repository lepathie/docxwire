# Proposal

## Why

The project's JavaScript tooling (OpenSpec CLI validation, commitlint) is invoked via `npx` with version-pinned string literals scattered across two CI workflow files, an agent skill, and the README — three packages pinned in five places, with no manifest, no lockfile, and no npm cache in CI. Bumping a tool version means editing several literals that can silently diverge, and every CI run re-resolves and re-downloads the packages. A root `package.json` plus committed `package-lock.json` gives the project a single source of truth for tool versions, reproducible installs (`npm ci`), and enables GitHub's npm cache.

## What Changes

- Add a root `package.json` (`private: true`) declaring the three tool packages as exactly-pinned `devDependencies` (`@commitlint/cli@21.2.4`, `@commitlint/config-conventional@21.2.4`, `@fission-ai/openspec@1.16.0`), and commit the generated `package-lock.json`.
- Add `node_modules/` to `.gitignore`.
- Both CI workflows gain `actions/setup-node` (Node 22, `cache: npm`) followed by `npm ci`; all four `npx` invocations (`ci.yaml` openspec job, `commitlint.yaml` both jobs) are replaced with direct `node_modules/.bin` binary calls.
- `Makefile`: `make setup` additionally runs `npm ci`; new targets `make lint-commit` (validate a commit message piped via stdin) and `make openspec-validate` (validate OpenSpec artifacts locally) run the repo-local binaries.
- The `git-commit` agent skill validates messages via `make lint-commit` instead of the pinned `npx` one-liner.
- `README.md`: the OpenSpec section no longer carries a version literal — the canonical version lives in `package.json`; local validation is `make openspec-validate`; a personal `npm install -g` of the pinned version remains an optional convenience for having bare `openspec` on PATH (e.g. for agent workflows).
- Supersedes design decision D2 of the archived `enforce-conventional-commits` change ("pure `npx` invocation, no `package.json`"): its trade-off (per-run downloads, versions as YAML literals) is now accepted in exchange for a single, centrally managed version source.

The tool versions themselves are unchanged; only how they are installed and invoked changes.

## Capabilities

### New Capabilities

None — tooling-only change.

### Modified Capabilities

None — no spec-level behavior changes. The change declares `skip_specs: true`.

## Impact

- **Files**: `package.json` (new), `package-lock.json` (new), `.gitignore`, `.github/workflows/ci.yaml`, `.github/workflows/commitlint.yaml`, `Makefile`, `.agents/skills/git-commit/SKILL.md`, `README.md`.
- **Dependencies**: three npm `devDependencies`; no Python dependency changes.
- **CI**: the `openspec` and `commitlint` jobs install the npm tree via `npm ci` (cacheable by `actions/setup-node`); the Node runtime is explicitly pinned to 22 in CI instead of relying on the runner's default.
- **Behavior**: none — the converter, publisher, and all spec'd capabilities are untouched; CI checks run the same tool versions against the same configurations.

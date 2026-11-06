# Design

## Context

- The project's JavaScript tooling surface: three packages — `@fission-ai/openspec` (OpenSpec artifact validation in CI), `@commitlint/cli` + `@commitlint/config-conventional` (commit-message linting in CI and locally). Versions exist today as string literals in five `npx` call sites (one in `ci.yaml`, three in `commitlint.yaml`, one in the `git-commit` agent skill) plus a global-install instruction in `README.md`; there is no `package.json`, no lockfile, and no npm cache in CI.
- The archived `enforce-conventional-commits` change made the opposite call deliberately (its D2: "pure `npx` invocation, no `package.json`", trade-off: per-run downloads accepted to "keep the repo JavaScript-free"). That decision was right for two CI call sites; the surface has since grown, and central version locking now wins. This change supersedes that D2.
- Node 22 and npm are available on GitHub Actions runners and developer machines (already an assumed prerequisite).
- Drift is not hypothetical: a developer's globally installed OpenSpec CLI was observed a minor version behind the CI pin.
- See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**

- One source of truth for JS tool versions: root `package.json` + committed `package-lock.json`; no version literal anywhere else in the repo.
- Reproducible, cacheable CI installs: `npm ci` from the lockfile, cached by `actions/setup-node`.
- Zero `npx` invocations left in the repo (CI, Makefile, skill, docs).
- Local tool use through `make`, running repo-local binaries — no machine-global state required.
- Explicit Node 22 pin in CI (today the runner's default Node is used, which changes over time).

**Non-Goals:**

- No product JavaScript code; the manifest covers CI/dev tooling only.
- No local git hooks (enforcement stays server-side per the archived D4/D5).
- No tool version bumps or lint/validation configuration changes in this change.
- No composite actions or reusable workflows to DRY the shared CI setup steps (3 lines × 2 workflows is acceptable duplication).

## Decisions

### D1: Root `package.json` with exact-pinned `devDependencies`, committed lockfile

- Root-level, not a `tooling/` subdirectory: the npm-standard shape; a subdirectory would add `working-directory:` juggling to both workflows for a cosmetic clean root.
- Exact pins (`"21.2.4"`, not `"^21.2.4"`): these are CI *tools* whose minor bumps can change lint/validate behavior. The lockfile already pins the transitive tree, so exact top-level pins cost nothing and make `package.json` itself an unambiguous version statement.
- `private: true` prevents accidental `npm publish`.
- Version bumps become a single `npm update <pkg>` (or manifest edit) whose commit touches `package.json` + `package-lock.json` together — that pair *is* the central version home.

### D2: CI — `actions/setup-node` (Node 22, `cache: npm`) → `npm ci` → direct binary calls

- `actions/setup-node` with `cache: npm` is the standard primitive; it uses `actions/cache` internally, keyed on the lockfile hash, so cache invalidation is automatic on version bumps (no manual key management).
- `npm ci` installs exactly the lockfile tree and fails if manifest and lockfile diverge — CI == manifest by construction.
- Invocations call the binary directly (`node_modules/.bin/openspec …`, `node_modules/.bin/commitlint …`): plain and transparent. `npx --no-install` was considered; it is equivalent but adds a flag to misremember for no benefit.
- `node-version: 22` makes the runtime explicit in both workflows instead of inheriting the runner's drifting default.
- Both workflows carry the setup steps (2 jobs per event); with a warm cache each `npm ci` takes seconds. A composite action to factor this out was considered and rejected as YAGNI.

### D3: The Makefile is the local front

- `make setup` = `uv sync` + `npm ci` — repo-local only. Project tooling does not install machine-global state; that constraint ruled out scripting `npm install -g` (and a `~/.local/bin` symlink) from the Makefile.
- `make lint-commit` runs the repo-local `commitlint` with the message on stdin and an `$(ARGS)` passthrough, preserving the `git-commit` skill's "append `-l`, amend until green" loop (`make lint-commit ARGS=-l`).
- `make openspec-validate` runs the repo-local `openspec validate --all` — the local equivalent of the CI job.
- CI does **not** go through these targets: the push job needs `--from … --to …` range arguments and the PR-title job its own stdin shape, which fixed targets don't fit. The split is deliberate: *local = make, CI = workflow YAML*, both resolving the same `node_modules`.

### D4: OpenSpec CLI in the manifest for CI; bare `openspec` on PATH stays a personal choice

- The CLI-generated OpenSpec workflow skills (`.agents/skills/openspec-*/`, not hand-editable) invoke bare `openspec`, so agent workflows need it on PATH.
- The repo scripts no global install. `README.md` documents an *optional, personal* `npm install -g @fission-ai/openspec@<version from package.json>` for that.
- Guarantee boundary: everything the repo invokes (CI + make) is structurally lockfile-derived. A personal global CLI is best-effort alignment — a convenience tier, like shell config, explicitly outside the guarantee. Per the archived D4 reasoning, per-machine state is never an enforcement surface; enforcement remains the CI checks.

### D5: Supersede the archived D2, with the rationale recorded

Recorded here and in the proposal: D2's "JavaScript-free repo" preference is reversed because the accumulated surface (five `npx` sites, a skill, a README instruction, observed version drift) made scattered literals the higher-maintenance option.

## Risks / Trade-offs

- **Lockfile size** (commitlint's transitive tree, a few dozen packages) → accepted; standard npm practice, a few hundred KB at most.
- **Bump discipline**: a version-bump commit must touch `package.json` and `package-lock.json` together → `npm ci` fails loudly in CI if they diverge; the failure mode is safe.
- **Personal global CLI drift** (already observed: local a minor behind CI) → accepted residual per D4; CI is the enforcement point and is lockfile-pinned; the README names `package.json` as canonical.
- **Multi-project global prefix collision** (two repos pinning different OpenSpec versions) → pre-existing property of the global-install model; last install wins; unchanged by this change.
- **`npm ci` cost in two CI jobs per event** → seconds with a warm cache; negligible.
- **Fresh clone has no bare `openspec`** until a personal global install → `make setup` remains the documented onboarding step, and `make openspec-validate` covers local validation with no global state at all.
- **Node/npm becomes a hard `make setup` prerequisite** → already assumed (Node 22 per the archived design); the README states it explicitly.

## Migration Plan

- Single PR: manifest, lockfile, workflow, Makefile, skill, and README changes land together; CI runs the new path from the first commit.
- Rollback: revert the commit — the old `npx` lines are restored and the manifest files removed. No state migration: `node_modules/` is gitignored and disposable.
- After merge: developers re-run `make setup` on next touch and optionally align any personal global CLI.

## Open Questions

None — all decisions were resolved during exploration.

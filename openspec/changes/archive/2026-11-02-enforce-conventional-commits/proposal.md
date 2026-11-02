# Proposal

## Why

The git history follows Conventional Commits by convention, but nothing enforces it: a single malformed commit message can silently land in `main` and degrade the history that any changelog, release, or tooling downstream of it relies on. Enforcing the format on everything that lands in `main` adds an automated guardrail.

## What Changes

- Add a `.commitlintrc.json` config extending the `@commitlint/config-conventional` preset, with no custom rules.
- Add a new GitHub Actions workflow (`commitlint`) that lints commit messages via `npx`-invoked commitlint, pinned like the existing OpenSpec validation:
  - on `push` to `main`: lints the pushed range (`github.event.before..after`) — i.e., the (squashed) commit landing on `main`
  - on `pull_request` targeting `main` (opened/edited/reopened/synchronize): lints the PR title — it seeds the squash commit message, so a bad message is caught before merge
  - PR commits are deliberately not linted: per the Conventional Commits spec, a squash-based workflow lets the maintainer clean up commit messages at merge time, without imposing the spec on casual committers
- No local git hooks: `.git/hooks/` is not tracked by design, and a committed-hook-plus-install-step workaround has an enforcement gap (any clone where the install step never ran has no local hooks). Enforcement lives in CI; a local hook (husky/lefthook) can be added later as its own change if the feedback loop feels slow.
- Document the convention: README badge plus a "Conventional Commits" section naming the commitlint config as the enforcement mechanism. (A committed agent skill is deferred: the CI feedback loop already covers it, and a front-matter skill would additionally require pymarkdown's `front-matter` extension.)

## Capabilities

### New Capabilities

(none — tooling change, `skip_specs: true`)

### Modified Capabilities

(none)

## Impact

- **New files**: `.commitlintrc.json`, `.github/workflows/commitlint.yaml`
- **Modified**: `README.md` (badge + "Conventional Commits" section)
- **New tooling dependencies**: `@commitlint/cli` + `@commitlint/config-conventional`, pulled on demand via `npx` (version-pinned, 21.2.4) — no `package.json`/`node_modules` in the repo, no Python dependency changes
- **Manual repository configuration (no code)**: branch protection on `main` — require pull requests (no direct pushes) and require the `commitlint` status check; allow only squash merging (disable merge commits and rebase merging) so every PR lands as a single commit whose message the maintainer writes in the squash form
- **No changes** to application code, tests, or the Python toolchain

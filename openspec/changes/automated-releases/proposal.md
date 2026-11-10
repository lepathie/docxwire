# Proposal

## Why

The repo has no release process: `pyproject.toml` declares `0.1.0`, but there is no tag, no GitHub release, and no
changelog — cutting a release means manually bumping the version, re-stamping `uv.lock`, writing the notes, tagging, and
creating the release. The project already enforces Conventional Commits (commitlint), so the versioning information is
in the history; it just isn't wired up.

## What Changes

- Introduce [python-semantic-release (PSR)](https://python-semantic-release.readthedocs.io/) as the release tool: a
  GitHub Action on `main` computes the next version from the conventional commits since the last release tag and, in a
  single release commit, stamps `pyproject.toml` and `uv.lock`, updates `CHANGELOG.md`, creates the `v<version>` tag,
  and publishes a GitHub Release whose notes are the new changelog entry
- Add `CHANGELOG.md`, seeded with a hand-written `0.1.0` entry: with no tag history, the first release is cut manually
  (tag + GitHub release), and from the second release on PSR maintains the file
- `pyproject.toml` gains a `[tool.semantic_release]` section (version declared in `project.version`, branch `main`) and
  a `build` extra pinning `uv`, so the Docker-based action's `build_command` can re-stamp `uv.lock` in the release
  commit — CI installs with `uv sync --frozen`, so the lockfile must stay consistent with the stamped version
- New `.github/workflows/release.yml` running the PSR action on pushes to `main`, with a concurrency guard and minimal
  `contents: write` permission
- Standard SemVer versioning: `fix` bumps the patch, `feat` bumps the minor, a breaking change bumps the major — which
  PSR demotes to a minor bump while the major version is 0

Non-goals: publishing to PyPI (the tool is consumed from a checkout via `uv run`; the GitHub release is the distribution
surface), release asset uploads, re-publish/upsert behavior (`--force`), batch publishing.

## Capabilities

### New Capabilities

(None — tooling change; `skip_specs: true` in `.openspec.yaml`)

### Modified Capabilities

(None)

## Impact

- `pyproject.toml` — new `[tool.semantic_release]` section and `build` optional-dependency extra (no runtime dependency
  change)
- `.github/workflows/release.yml` — new workflow, independent of the CI pipeline
- `CHANGELOG.md` — new file
- No Python code, test, or CLI behavior changes; `make ci` is unaffected

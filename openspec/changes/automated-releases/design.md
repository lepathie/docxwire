# Design

## Context

The repo ships a CLI consumed from a checkout (`uv run docxwire`), with
Conventional Commits enforced by commitlint (`@commitlint/config-conventional`),
a `uv sync --frozen` CI, and Renovate managing dependencies (including weekly
lockfile maintenance). No release tooling exists. python-semantic-release (PSR) was chosen over release-please and
semantic-release (JS) for its
first-class uv integration — re-stamping `uv.lock` in the release commit via
`build_command`.

## Goals / Non-Goals

**Goals:**

- Cut a release (version stamp + changelog + lockfile + tag + GitHub release)
  automatically from the conventional commits on `main`
- Keep the `uv sync --frozen` CI green across a release
- Keep the release record in the repo (`CHANGELOG.md`), the GitHub release a
  mirror of its latest entry

**Non-Goals:**

- Publishing to PyPI or any other package index
- Uploading release assets (no PSR `publish-action`)
- A human gate on releases (PSR's push-triggered model is a deliberate choice
  over release-please's release-PR model)

## Decisions

### 1. Push-triggered, no human gate, no CI gate

PSR runs on every push to `main` and cuts the release immediately. The
release does not wait for the CI pipeline — `release.yml` and `ci.yaml` are
separate workflows on the same push, running in parallel. The release commit
itself triggers a fresh CI run, so a release cut from a red push is
re-verified right away. Accepted for a single-maintainer repo with fast CI.

### 2. Standard SemVer commit parsing

The conventional-commit parser runs with its defaults — `fix` → patch,
`feat` → minor, breaking → major, with PSR demoting a major bump to a
minor while the major version is 0. No custom `commit_parser_options`:
0.x is exactly the range where SemVer says anything may change, and
consumers and tooling already understand that cadence.

### 3. The lockfile is re-stamped by the `build_command`

CI installs with `uv sync --frozen`; a version bump in `pyproject.toml`
would desync `uv.lock` and break the next CI run. Per PSR's uv integration
guide, the `build_command` runs `uv lock --upgrade-package "$PACKAGE_NAME"`
(updates only the project's own version in the lock, never the
dependencies) and `git add uv.lock`, so the lockfile lands in the release
commit. The `build_command` runs inside the uv-managed venv that `uv run`
creates for the CLI (decision 6), which ships no `pip`, so the project is
installed with `uv pip install -e '.[build]'` from a new `build`
optional-dependencies extra; pinning `uv` there lets Renovate keep it
current. No `uv build` step — no distribution artifacts are built.

### 4. Manual `v0.1.0` baseline; PSR generates the changelog

`v0.1.0` is cut manually (tag + GitHub release with the agreed notes)
before the workflow is armed. `CHANGELOG.md` is not seeded: PSR's default
init mode generates it from the git history at the first automated release,
and `mask_initial_release` (the default) renders the very first release as
a one-line "Initial Release" — so no full-history dump lands in the file
and no hand-maintained seed can drift from the generated entries.
**Sequencing constraint:** the `v0.1.0` tag must exist on `main` before
the first `feat`/`fix` push after the release workflow is active —
otherwise PSR computes the first version from the full history.

### 5. The pipeline-arming commit is `chore(release)`, not `feat`

The commit that adds `release.yml` is typed `chore(release):` (allowed by
`@commitlint/config-conventional`) so arming the pipeline does not itself
cut a release; the next real `feat`/`fix` does.

### 6. Workflow shape

`on: push` to `main`; a concurrency group (`release-<ref>`,
`cancel-in-progress: false`) so rapid successive pushes cannot race two
release jobs; checkout at `github.ref_name` with `fetch-depth: 0` (PSR needs
the full history to compute the version) followed by
`git reset --hard ${{ github.sha }}` so a branch that moves while the run is
in flight cannot release un-evaluated changes; `contents: write` scoped to
the release job only (least privilege); every action pinned with a version
comment matching the `ci.yaml` pinning convention. PSR runs as the **CLI**
(`uv run --with 'python-semantic-release==<pin>' semantic-release version`)
rather than the official Docker action: the Docker container cannot see the
runner's SSH agent, which the release push depends on (decision 8).

### 7. The release push goes through a deploy key (ruleset bypass)

`main` is protected by a repository **ruleset** with required status checks.
A release commit pushed by the workflow would arrive with no status checks
of its own, so the ruleset rejects the push — the push that is meant to
*trigger* the checks is blocked *by* them (the chicken-and-egg that failed
the first armed run with `GH006: Protected branch update failed`). Granting
the `github-actions` identity ruleset bypass would let every workflow bypass
the ruleset; instead a dedicated **deploy key** (write access, scoped to this
one repository) is added as the ruleset's bypass actor. The workflow
authenticates the checkout (`ssh-key:`) and the push (via
`webfactory/ssh-agent`) with that key, and
`[tool.semantic_release.remote]` sets `ignore_token_for_push = true` so
`GITHUB_TOKEN` is never used for the git push — it remains the credential
for the Releases API only. The key is a repository secret (`DEPLOY_KEY`) and
can be rotated or revoked without touching the ruleset. This is the pattern
documented in PSR issue #1343.

### 8. Curation lives in the commit messages

Keep a Changelog 2.0.0 cautions that a changelog generated from commit
messages is "raw material at best" — the judgment of what is notable belongs
to a person. With PSR that judgment moves upstream into the commit messages,
which this repo already disciplines (commitlint, motivation in the body).
Accepted for a single-maintainer tool.

Scope convention: the product is a single-component CLI, so a `cli` scope
is noise — PSR renders it as a `**cli**:` prefix on every entry. Commits
should omit the scope (`feat: …`); commitlint already allows that. Scopes
stay available for a day when real sub-areas (`converter`, `joomla`) emerge.

### 9. The changelog shows only user-facing changes

The first automated release (v0.2.0) showed the cost of an unfiltered
changelog: Renovate `chore(deps)`, OpenSpec workflow `chore(openspec)`, and
`ci` housekeeping made up most of the entries, burying the one real feature.
`changelog.exclude_commit_patterns` therefore drops the non-user-facing
types (`chore`, `ci`, `build`, `refactor`, `style`, `test`) from the
rendered entries — a standard config option, not a custom template, so the
default rendering (decision 4) is otherwise untouched; this is the same
curation release-please applies by default. `CHANGELOG.md` is excluded from
pymarkdown (`system.exclude_path`): the file is machine-generated and its
whitespace belongs to PSR's template, which the linter rejects (MD012/MD022).

## Risks / Trade-offs

- **A release can be cut from a red push** (no CI gate, decision 1): the
  release commit triggers a fresh CI run; a broken release is corrected by
  the next `fix:` commit.
- **`build_command` failure**: PSR aborts the release before tagging — the
  workflow fails visibly and nothing is published; the commit is assembled
  before the tag/push, so there is no partial state.
- **A standing write credential to `main`** (deploy key, decision 7): it is
  scoped to this repository only (deploy keys cannot be org-wide), its use
  is limited to the one release workflow, and it is rotatable by replacing
  the `DEPLOY_KEY` secret and the key in the ruleset — no workflow or
  ruleset change required.
- **The release workflow depends on repo settings outside the repo**
  (deploy key + ruleset bypass actor): a settings regression (key removed,
  bypass actor dropped) surfaces as a visible `GH006` push failure with no
  partial state — the release commit simply does not land and the next
  releasable push retries.

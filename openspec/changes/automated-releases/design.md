# Design

## Context

The repo ships a CLI consumed from a checkout (`uv run docxwire`), with
Conventional Commits enforced by commitlint (`@commitlint/config-conventional`),
a `uv sync --frozen` CI, and Renovate managing dependencies (including weekly
lockfile maintenance). No release tooling exists. python-semantic-release (PSR) was chosen over release-please and
semantic-release (JS) for its
first-class uv integration — re-stamping `uv.lock` in the release commit via
`build_command` — and its official GitHub Action.

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
commit. The PSR action is Docker-based and does not ship `uv`, so the
`build_command` first installs it from a new `build`
optional-dependencies extra (`pip install -e '.[build]'`); pinning `uv`
there lets Renovate keep it current. No `uv build` step — no distribution
artifacts are built.

### 4. Manual `v0.1.0` baseline, hand-written changelog seed

No tag history exists, so an auto-generated first release would dump the
repo's entire history into the notes. `v0.1.0` is cut manually (tag +
GitHub release) and `CHANGELOG.md` is seeded with a hand-written `0.1.0`
entry shaped like what PSR generates later (`## [0.1.0] - <date>` heading,
`### Features` grouping), so the file has one style. **Sequencing
constraint:** the `v0.1.0` tag must exist on `main` before the first
`feat`/`fix` push after the release workflow is active — otherwise PSR
computes the first version from the full history.

### 5. The pipeline-arming commit is `chore(release)`, not `feat`

The commit that adds `release.yml` is typed `chore(release):` (allowed by
`@commitlint/config-conventional`) so arming the pipeline does not itself
cut a release; the next real `feat`/`fix` does.

### 6. Workflow shape

Per the PSR GitHub Actions documentation: `on: push` to `main`; a
concurrency group (`release-<ref>`, `cancel-in-progress: false`) so rapid
successive pushes cannot race two release jobs; checkout at
`github.ref_name` followed by `git reset --hard ${{ github.sha }}` so a
branch that moves while the run is in flight cannot release un-evaluated
changes; `contents: write` scoped to the release job only (least privilege);
`GITHUB_TOKEN` as the action token; the action pinned with a version comment
matching the `ci.yaml` pinning convention. No `fetch-depth: 0` needed —
PSR ≥ 10.5 unshallows automatically.

### 7. Curation lives in the commit messages

Keep a Changelog 2.0.0 cautions that a changelog generated from commit
messages is "raw material at best" — the judgment of what is notable belongs
to a person. With PSR that judgment moves upstream into the commit messages,
which this repo already disciplines (commitlint, motivation in the body).
Accepted for a single-maintainer tool.

## Risks / Trade-offs

- **A release can be cut from a red push** (no CI gate, decision 1): the
  release commit triggers a fresh CI run; a broken release is corrected by
  the next `fix:` commit.
- **`build_command` failure**: PSR aborts the release before tagging — the
  workflow fails visibly and nothing is published; the commit is assembled
  before the tag/push, so there is no partial state.
- **Docker-action constraints** (no `uv`, no caching, fixed Python):
  mitigated by the documented `build`-extra install; the lock re-stamp is a
  single fast `uv lock` run.

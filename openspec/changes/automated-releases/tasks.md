# Tasks

## 1. Changelog baseline

- [ ] 1.1 Create `CHANGELOG.md` with the Keep a Changelog preamble and the hand-written `0.1.0` entry (date = the day `v0.1.0` is tagged; text agreed in the release discussion); verify `make lint` (pymarkdown) passes

## 2. PSR configuration (`pyproject.toml`)

- [ ] 2.1 Add a `build` optional-dependencies extra pinning `uv`
- [ ] 2.2 Add a `[tool.semantic_release]` section: `version_toml = ["pyproject.toml:project.version"]`, `branch = "main"`, `allow_zero_version = true`, and a `build_command` that installs the `build` extra, runs `uv lock --upgrade-package "$PACKAGE_NAME"`, and stages `uv.lock`

## 3. Release workflow

- [ ] 3.1 Add `.github/workflows/release.yml` per the PSR GitHub Actions pattern: `on: push` to `main`, concurrency group, checkout at `github.ref_name` + reset to `github.sha`, the PSR action pinned with a version comment, `contents: write` scoped to the job, `GITHUB_TOKEN`
- [ ] 3.2 Lint the workflow (e.g. `uvx actionlint .github/workflows/release.yml`)

## 4. Verification

- [ ] 4.1 Dry-run the version computation locally (temporary `v0.1.0` tag plus a test `fix:` commit, `--no-commit --no-tag`); verify it computes `0.1.1`; remove the temporary tag
- [ ] 4.2 Run `make ci`; verify it is green

## 5. Baseline release (user action)

- [ ] 5.1 Tag `v0.1.0` on `main` (before this change is pushed) and push the tag
- [ ] 5.2 Create the `v0.1.0` GitHub Release with the agreed release notes

## 6. Arm the pipeline (user action)

- [ ] 6.1 Commit this change (code + `openspec/changes/automated-releases/`) with a `chore(release):` message and push to `main` — the workflow becomes active and no release is cut (`chore` is not releasable)

## 7. First automated release (user action)

- [ ] 7.1 Push a small `fix:` commit to `main`
- [ ] 7.2 Verify the pipeline cut `v0.1.1`: the release commit contains the stamped `pyproject.toml`, the re-stamped `uv.lock`, and the `CHANGELOG.md` entry; the `v0.1.1` tag exists; the GitHub Release notes mirror the entry

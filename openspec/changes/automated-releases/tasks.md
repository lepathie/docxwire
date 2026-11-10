# Tasks

## 1. PSR configuration (`pyproject.toml`)

- [x] 1.1 Add a `build` optional-dependencies extra pinning `uv`
- [x] 1.2 Add a `[tool.semantic_release]` section: `version_toml = ["pyproject.toml:project.version"]`, `branch = "main"`, `allow_zero_version = true`, and a `build_command` that installs the `build` extra, runs `uv lock --upgrade-package "$PACKAGE_NAME"`, and stages `uv.lock` (no `changelog` section — the default init mode generates `CHANGELOG.md`, initial release masked)

## 2. Release workflow

- [x] 2.1 Add `.github/workflows/release.yml` per the PSR GitHub Actions pattern: `on: push` to `main`, concurrency group, checkout at `github.ref_name` + reset to `github.sha`, the PSR action pinned with a version comment, `contents: write` scoped to the job, `GITHUB_TOKEN`
- [x] 2.2 Lint the workflow (e.g. `uvx actionlint .github/workflows/release.yml`)

## 3. Verification

- [x] 3.1 Dry-run the version computation locally (temporary `v0.1.0` tag plus a test `fix:` commit, `--no-commit --no-tag`); verify it computes `0.1.1`; remove the temporary tag
- [x] 3.2 Run `make ci`; verify it is green

## 4. Baseline release (user action)

- [x] 4.1 Tag `v0.1.0` on `main` (before this change is pushed) and push the tag
- [x] 4.2 Create the `v0.1.0` GitHub Release with the agreed release notes

## 5. Arm the pipeline (user action)

- [x] 5.1 Commit this change (code + `openspec/changes/automated-releases/`) with a `chore(release):` message and push to `main` — the workflow becomes active and no release is cut (`chore` is not releasable`)

## 6. First automated release (user action)

- [ ] 6.1 Push a small `fix:` commit to `main`
- [ ] 6.2 Verify the pipeline cut `v0.1.1`: the release commit contains the stamped `pyproject.toml`, the re-stamped `uv.lock`, and the `CHANGELOG.md` entry; the `v0.1.1` tag exists; the GitHub Release notes mirror the entry

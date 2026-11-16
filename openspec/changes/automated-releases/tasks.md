# Tasks

## 1. PSR configuration (`pyproject.toml`)

- [x] 1.1 Add a `build` optional-dependencies extra pinning `uv`
- [x] 1.2 Add a `[tool.semantic_release]` section: `version_toml = ["pyproject.toml:project.version"]`, `branch = "main"`, `allow_zero_version = true`, a `build_command` that installs the `build` extra (`uv pip` — the `uv run` venv ships no `pip`), runs `uv lock --upgrade-package "$PACKAGE_NAME"`, and stages `uv.lock` (no `changelog` section — the default init mode generates `CHANGELOG.md`, initial release masked), and a `[tool.semantic_release.remote]` section with `token = { env = "GITHUB_TOKEN" }` and `ignore_token_for_push = true`

## 2. Release workflow

- [x] 2.1 Add `.github/workflows/release.yml`: `on: push` to `main`, concurrency group, SSH checkout (`ssh-key: DEPLOY_KEY`, `fetch-depth: 0`) at `github.ref_name` + reset to `github.sha`, `webfactory/ssh-agent` loading the deploy key, `astral-sh/setup-uv`, the PSR CLI via `uv run --with` (pinned, not the Docker action — it can't see the SSH agent), `contents: write` scoped to the job, `GITHUB_TOKEN` for the Releases API only
- [x] 2.2 Lint the workflow (e.g. `uvx actionlint .github/workflows/release.yml`)

## 3. Verification

- [x] 3.1 Dry-run the version computation locally (temporary `v0.1.0` tag plus a test `fix:` commit, `--no-commit --no-tag`); verify it computes `0.1.1`; remove the temporary tag
- [x] 3.2 Run `make ci`; verify it is green

## 4. Baseline release (user action)

- [x] 4.1 Tag `v0.1.0` on `main` (before this change is pushed) and push the tag
- [x] 4.2 Create the `v0.1.0` GitHub Release with the agreed release notes

## 5. Arm the pipeline (user action)

- [x] 5.1 Commit this change (code + `openspec/changes/automated-releases/`) with a `chore(release):` message and push to `main` — the workflow becomes active and no release is cut (`chore` is not releasable`)

## 6. Deploy key setup (user action)

- [ ] 6.1 Generate an ed25519 SSH keypair without a passphrase
- [ ] 6.2 Add the public key to the repository as a deploy key **with write access**
- [ ] 6.3 Add the deploy key to the `main` ruleset's bypass actors
- [ ] 6.4 Set the `DEPLOY_KEY` repository secret to the private key

## 7. First automated release (user action)

- [x] 7.1 Push the deploy-key arming commit to `main` — the pending `feat(cli)` commit is already in the untagged range, so this push alone cuts the first release (no extra `fix:` commit needed)
- [x] 7.2 Verify the pipeline cut `v0.2.0`: the release commit contains the stamped `pyproject.toml`, the re-stamped `uv.lock`, and the `CHANGELOG.md` entry; the `v0.2.0` tag exists; the GitHub Release notes mirror the entry

## 8. Changelog curation (post-v0.2.0)

- [x] 8.1 Exclude `CHANGELOG.md` from pymarkdown (`system.exclude_path`) — generated file, template-owned whitespace (MD012/MD022)
- [x] 8.2 Add a `[tool.semantic_release.changelog]` section with `exclude_commit_patterns` dropping `chore`/`ci`/`build`/`refactor`/`style`/`test` from the rendered entries (v0.2.0's notes were mostly Renovate and OpenSpec housekeeping)
- [ ] 8.3 Push to `main` (`ci:` type — no release is cut) and verify the CI pipeline is green again

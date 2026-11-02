# Tasks

- [ ] 1. Add `.commitlintrc.json` with the preset-only config (`extends: ["@commitlint/config-conventional"]`)
- [ ] 2. Add `.github/workflows/commitlint.yaml`: `push` + `pull_request` (opened/edited/reopened/synchronize) on `main`; two event-gated jobs — `lint-commits` (push range, root-commit fallback for zero `before`, `fetch-depth: 0`) and `lint-pr-title` (title piped to commitlint via stdin, no checkout); pinned `npx` commitlint
- [ ] 3. Update `README.md`: Conventional Commits badge + short section naming the commitlint config as the enforcement mechanism and the squash-merge workflow
- [ ] 4. Verify locally: lint the repo's full current history with the CI command (must pass); exercise the push range logic (incl. the zero-`before` case) and the title pipe (valid + invalid) in a scratch setup
- [ ] 5. Run `make ci` and `openspec validate`
- [ ] 6. (Manual, repo owner) GitHub repository settings: require pull requests for `main` (no direct pushes), require both `commitlint` checks (push + PR title), allow only squash merging (disable merge commits and rebase merging), enable "Default to PR title for squash merge commits"

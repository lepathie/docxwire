# Tasks

## 1. Manifest and lockfile

- [x] 1.1 Add root `package.json`: `name` `docxwire`, `private: true`, `engines.node` `>=22`, and `devDependencies` with exact pins `@commitlint/cli@21.2.4`, `@commitlint/config-conventional@21.2.4`, `@fission-ai/openspec@1.16.0` — verify: file exists with the three exact pins and no other dependencies
- [x] 1.2 Generate `package-lock.json` and verify `npm ci` succeeds from it — verify: `npm ci` exits 0 and `node_modules/.bin/{openspec,commitlint}` exist

## 2. CI workflows

- [x] 2.1 `ci.yaml` `openspec` job: add `actions/setup-node` (`node-version: 22`, `cache: npm`) and an `npm ci` step; replace the `npx` line with `./node_modules/.bin/openspec validate --all` — verify: YAML parses and the job steps are checkout → setup-node → npm ci → validate
- [x] 2.2 `commitlint.yaml` both jobs: add the same `actions/setup-node` + `npm ci` steps; replace all three `npx` invocations with `./node_modules/.bin/commitlint`, preserving the `--from`/`--to` range logic and the PR-title stdin pipe — verify: `grep -n npx .github/workflows/` returns nothing

## 3. Makefile

- [x] 3.1 Extend `setup` with `npm ci` after `uv sync` — verify: `make setup` completes and `node_modules/` is populated
- [x] 3.2 Add `lint-commit` target running `./node_modules/.bin/commitlint $(ARGS)` with the message on stdin — verify: `echo "feat: x" | make lint-commit` exits 0 and `echo "bad message" | make lint-commit` exits non-zero
- [x] 3.3 Add `openspec-validate` target running `./node_modules/.bin/openspec validate --all` — verify: `make openspec-validate` exits 0 on the current tree

## 4. Skill and docs

- [x] 4.1 `.agents/skills/git-commit/SKILL.md`: replace the pinned `npx` one-liner with `make lint-commit`, documenting `make lint-commit ARGS=-l` for the amend loop — verify: no `npx` remains in the skill and `make check` (pymarkdown) is clean
- [x] 4.2 `README.md`: add `lint-commit`/`openspec-validate` to the make target list; reword the OpenSpec section so it carries no version literal (canonical version in `package.json`), names `make openspec-validate` for local validation, and offers the personal `npm install -g` of the pinned version as an optional PATH convenience; state the Node 22 prerequisite — verify: `grep -n "1.16.0" README.md` returns nothing and `make check` is clean

## 5. Verification

- [x] 5.1 `make ci` is green (lint, type check, tests at 100% coverage) — verify: exit 0
- [x] 5.2 `make openspec-validate` passes with the new change's artifacts in place — verify: exit 0
- [x] 5.3 No `npx` invocation remains in active project files (workflows, Makefile, skills, README, manifest) — verify: `grep -rn npx .github Makefile .agents README.md package.json` returns nothing (archived changes under `openspec/changes/archive/` are history and stay untouched)

## Workflow follow-up

- The first push to `main` after merge exercises both reworked jobs (`OpenSpec`, `Commit Lint`) — confirm they pass in CI.
- Archive this change from `main` after the implementation is merged (user-initiated).

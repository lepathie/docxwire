# Design

## Context

- The repository's existing commit history already follows Conventional Commits; nothing enforces it.
- The project is Python/uv with no `package.json`. CI already uses a pinned `npx` invocation for OpenSpec validation (`npx -y @fission-ai/openspec@1.16.0 validate --all`).
- Node 22 is available on GitHub Actions runners and developer machines.
- Git hooks live in `.git/hooks/`, which is not tracked by design; client-side hooks are not copied when a repository is cloned, so they are a per-clone convenience, not a shared enforcement point.

## Decisions

### D1: Standalone workflow file, not a job in the CI Pipeline

`commitlint.yaml` is a separate workflow from `ci.yaml`:

- It lints a *range of commits* (push: `event.before..after`) and the *PR title* (pull request), rather than a tree state.
- It provides its own named status checks (`commitlint`) for branch protection on `main`.
- Triggers: `push: branches: [main]` and `pull_request: branches: [main]` (opened, edited, reopened, synchronize), with two event-gated jobs — `lint-commits` (push) and `lint-pr-title` (pull request). PR *commits* are out of scope by design (D5); only the title is linted.

### D2: Pure `npx` invocation, no `package.json`

```sh
npx -y -p @commitlint/cli@21.2.4 -p @commitlint/config-conventional@21.2.4 commitlint …
```

- Verified locally on Node 22: the preset resolves from `.commitlintrc.json` in a bare `npx` environment; no repo-local `node_modules` is required.
- `.commitlintrc.json` contains only `{ "extends": ["@commitlint/config-conventional"] }` — no custom rules.
- Versions are pinned, matching the OpenSpec job; bumped by a chore commit.

### D3: Lint inputs per event

- **`lint-commits` (push)**: `commitlint --from ${{ github.event.before }} --to ${{ github.event.after }}`. When `before` is all zeros (the push creates the branch), lint from the root commit: `--from $(git rev-list --max-parents=0 ${{ github.event.after }})`. The job uses `actions/checkout` with `fetch-depth: 0` (the history is small; this keeps the range logic uniform).
- **`lint-pr-title` (pull request)**: `echo "$PR_TITLE" | commitlint` — one line on stdin. A checkout (default depth) is required: without it the workspace contains no `.commitlintrc.json`, and commitlint rejects every title with "Please add rules" (exit 9). The checkout makes both jobs read the same config file — a single source of truth for the rules.

### D4: No local git hooks

Git hooks are not tracked by design: they live in `.git/hooks/`, which no clone receives. Committing hook scripts under `scripts/git-hooks/` plus a `make hooks` install step is a workaround, and it has an enforcement gap — any clone where the install step was never run (fresh clones, other developers' machines) has no local hooks at all. Git's own guidance for policy enforcement is to do it on the server side; on GitHub that is the CI check plus branch protection, which D5 makes mandatory.

Consequences:

- Violations surface when a push to `main` is made — i.e., at merge time, when the maintainer enters the squash commit message — with zero per-clone setup.
- A bad merge message is caught after it lands; the fix is `git reset --soft HEAD~1`, recommit with a proper message, and a force-push to `main`.
- If the feedback loop becomes a pain in practice, a local hook via husky or lefthook can be added later as its own change — deliberately deferred, not needed for enforcement.

### D5: Server-side enforcement, squash-based per the spec

The Conventional Commits spec's FAQ is explicit: contributors do not all need to follow the spec — "If you use a squash based workflow on Git lead maintainers can clean up the commit messages as they're merged—adding no workload to casual committers. A common workflow for this is to have your git system automatically squash commits from a pull request and present a form for the lead maintainer to enter the proper git commit message for the merge."

This change follows that workflow:

- CI checks: `push` to `main` (validates the (squashed) commit landing on `main`) and `pull_request` title (validates the message that will become the squash commit — pre-merge feedback; PR commits themselves are deliberately not linted). The squash form pre-fills from the title, so a passing title check means the default squash message passes; if the maintainer edits the message in the form, the push check is the backstop.
- Manual repository configuration (no code) — this is what makes the CI checks real gates:
  - Branch protection on `main`: require pull requests (disable direct pushes) and require both `commitlint` checks (push + PR title).
  - Allow only squash merging (disable "Create a merge commit" and "Rebase and merge" in Settings → Options): every PR lands as a single commit, and the squash form is where the maintainer writes the conventional message that the CI check then validates.

### D6: Docs, with the agent skill deferred

- **README**: the Conventional Commits badge plus a short section stating the adherence and naming the enforcement mechanism (commitlint + `@commitlint/config-conventional`, `.commitlintrc.json`).
- **Agent skill (deferred, not part of this change)**: a committed `git-commit` skill would largely duplicate what the CI feedback already provides — an agent can run the same pinned commitlint command locally and get the same verdict before committing. A committed skill with YAML front matter would additionally need pymarkdown's `front-matter` extension enabled in `pyproject.toml`, because `.agents/skills/git-commit/` is not in `system.exclude_path` and the file is (rightly) scanned. If a skill is added later, that config change belongs in the same change.

## Future considerations (out of scope)

- **release-please**: automates changelog, version bump, and release from the Conventional Commits history. It is a consumer of the convention, not an enforcer — it only pays off once the project has a release process (versioning cadence, changelog, publishing). Revisit after v1.0.

## Trade-offs

- `npx` downloads the two packages on every CI run (no npm cache configured); a few MB per run. The alternative — `package.json` + `npm ci` + GitHub's npm cache — was rejected to keep the repo JavaScript-free.
- The PR title is validated pre-merge, but a message edited only in the squash form is validated after it lands on `main` (fix: soft reset, recommit, force-push). Direct pushes to `main` are closed off by requiring pull requests in branch protection (D5).

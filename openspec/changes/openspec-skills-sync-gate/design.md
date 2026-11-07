# Design

## Context

The `openspec` job in `.github/workflows/ci.yaml` already checks out the repo, sets up Node, runs `npm ci`, and executes `openspec validate --all`. The generated files it guards are `.agents/skills/openspec-*/SKILL.md` plus a `.agents/skills/.openspec-target` marker.

Verified behavior of the OpenSpec CLI (v1.16.0): `openspec update --dry-run --json` prints `{"changes": [...], "notes": [...], "failures": []}` and **exits 0 even when `changes` is non-empty** (i.e. generated files are stale relative to the installed CLI). When in sync, `changes` is an empty array.

Renovate's config automerges qualifying PRs on the platform (`platformAutomerge`), which requires the required status checks to be green on the PR's *latest* head commit. The required set for `main` is `lint-and-test`, `openspec`, and `lint-pr-title`, and it stays that way — so **all three** check runs must land on the (possibly fixed) head commit. Three GitHub behaviors (per the current "Events that trigger workflows" docs) shape this design:

- Check runs are recorded against a run's own `GITHUB_SHA`. For a `workflow_dispatch` with a `ref`, that is the tip of the given branch — so a dispatch on the PR head branch produces check runs on the fixed head commit. A `workflow_run`-triggered run, by contrast, gets the *default branch* as its SHA: the declarative cross-workflow "dependency" provides ordering, but its check runs land on `main` and can never satisfy the PR's required checks — which is why it was considered and rejected.
- A push made with `GITHUB_TOKEN` that updates a PR creates `pull_request` runs that **require human approval**; other `GITHUB_TOKEN`-triggered events create no runs at all. The exception: `workflow_dispatch` / `repository_dispatch` runs created via the API execute normally. An explicit dispatch is therefore the only `GITHUB_TOKEN` path that starts a run without a human in the loop — and it is what keeps the fix loop-safe (no unattended re-triggering).
- Consequence: the fix job must dispatch the pipeline explicitly after pushing; nothing re-triggers it on its own.

## Goals / Non-Goals

**Goals:**

- Any PR that leaves the generated OpenSpec files stale fails CI, so drift can never reach `main`.
- A PR that leaves the files stale (in practice: Renovate's CLI-bump PRs) is auto-healed and remains automerge-able: the fix lands on the PR branch, and the pipeline runs — green — on the updated head.
- The pipeline runs only after the fix, on the (possibly fixed) head — never on a stale head about to be superseded.
- The required-checks set stays exactly `{lint-and-test, openspec, lint-pr-title}`; no branch-protection change.

**Non-Goals:**

- Automatically regenerating the files inside Renovate (a post-upgrade task). That is blocked on the Mend-hosted Renovate app — post-upgrade commands are disabled by default there and `allowedCommands` is a global-only option a repo config cannot set. If Renovate is ever self-hosted, the ready-to-use config is: `postUpgradeTasks: { "commands": ["openspec update"], "fileFilters": [".agents/skills/**"], "executionMode": "update" }` (the filter must cover `.openspec-target`, not only the `openspec-*` directories). The CI auto-regeneration is the hosted-app equivalent of it and can be retired in that case.
- Changing how the skills are generated or what they contain.

## Decisions

- **Assert on the JSON output, not the exit code.** The gate is `test "$(openspec update --dry-run --json | jq '[.changes[] | select(.path | startswith("~") | not)] | length')" -eq 0`. Alternative considered: plain `openspec update --dry-run` relying on the exit code — rejected because the exit code is 0 while stale (verified empirically); it would never fire.
- **`jq` for the assertion.** Preinstalled on `ubuntu-latest`; more readable than a Node one-liner. If a future runner image dropped `jq`, the step fails loudly (`command not found`) rather than passing silently.
- **Filter out non-repo paths (`~/**`).** Discovered on the first live run: in a fresh environment (every CI runner) the CLI's first run plans to create its machine-global `~/.config/openspec/config.json` (profile/delivery are machine-global by design — `openspec.dev/docs/profiles`; there is no project-level setting for them, `openspec/config.yaml` carries agent rules only) and reports that as a pending change. Unfiltered, the gate would fail on every run regardless of drift, and the regenerate job's `-gt 0` condition would send every in-sync PR into the fix branch, where `git commit` fails on an empty diff. The sync invariant is about the repo's generated files, so both the gate and the staleness condition count only changes whose path is not a `~`-prefixed global path. This also keeps the gate immune to future CLI changes in out-of-repo first-run behavior.
- **Only core-config files can be regenerated.** The regenerate job's commit is scoped to `git add .agents/skills`, so the bot commit can only contain the generated skill files; and in a fresh environment the CLI defaults to the `core` profile (exactly the six installed workflows) with a first-run migration that infers `delivery: skills` from the present state. Verified empirically: a real `openspec update` in a fresh environment touches nothing (in sync) or exactly the seven `.agents/skills/**` files (stale) — no command files, no extra workflows.
- **New step in the existing `openspec` job**, after `Validate OpenSpec artifacts`. Alternative: a separate job — rejected; it would duplicate checkout, Node setup, and `npm ci` for one extra CLI invocation.
- **Gate on `changes` only.** Operational errors already fail the step via the CLI's non-zero exit; the assertion adds exactly the sync invariant and nothing else.
- **The fix lives in its own workflow** (`.github/workflows/openspec-regenerate.yaml`). It needs a writable checkout of the PR head branch, its own `permissions:` block, and a PR-only trigger scope; keeping it out of `ci.yaml` keeps the pipeline file a pure gate. The single cross-file reference in the design is the retrigger line itself — a name reference of the same kind a `workflows: [ … ]` list would be, kept visible in the fix job rather than hidden in a trigger block.
- **`GITHUB_TOKEN` with `permissions: contents: write, actions: write`** — never a PAT. A `GITHUB_TOKEN` PR update creates only approval-pending runs, so the fix cannot spawn unattended runs; the explicit dispatch it makes is a `workflow_dispatch` event, which the regenerate workflow does not listen to. Bounded by construction: at most one fix push + one dispatch per stale PR update.
- **`ci.yaml` drops its `pull_request` trigger and gains a `workflow_dispatch:` with a `pr_title` input** (string, not required). The pipeline's PR runs then happen only via the retrigger, which is what guarantees "fix first, checks second, on the fixed head". The `push: branches: ["main"]` trigger is unchanged.
- **All three required checks in the single retriggered pipeline.** `lint-pr-title` moves from `commitlint.yaml` into `ci.yaml`, gated on `workflow_dispatch` with a non-empty `pr_title` input; the retrigger passes the PR title as a dispatch input. `commitlint.yaml` retains only its push-to-`main` `lint-commits` job, which remains the enforcement backstop (squash-merge commit message = PR title). Consequence: a PR title *edit* no longer triggers an immediate re-lint (the old `commitlint.yaml` ran on `edited`); the push-to-`main` backstop is unchanged. Alternative considered: dispatch `ci.yaml` **and** `commitlint.yaml` (which would keep the `edited` re-lint) — rejected: two cross-file references and two runs for what is one pipeline.
- **The retrigger runs for every PR, not just stale ones.** The dispatch is a separate, unconditional final step of the regenerate job (after the conditional fix), passing the PR title. This is what gives normal PRs their pipeline runs — with a stale-only dispatch, an in-sync PR would get no CI at all.
- **Re-trigger after (or instead of) pushing.** The final step is `gh workflow run ci.yaml --ref <head branch> -f pr_title=<PR title>` (`gh` is preinstalled on `ubuntu-latest`).
- **`gh` gets an explicit `GH_TOKEN`.** On the first live run the retrigger failed with `gh: … set the GH_TOKEN environment variable` — in an Actions run `gh` authenticates from `GH_TOKEN`, and the job's `GITHUB_TOKEN` was not picked up, so `gh` had no token. The step therefore sets `GH_TOKEN: ${{ github.token }}` explicitly (the canonical pattern). That token carries the `actions: write` scope from the job's `permissions:` block, which `gh workflow run` requires to dispatch the pipeline.
- **Check out `github.head_ref`** in the fix job — the PR branch, not the merge ref — so the commit lands on the branch the PR is tracking.
- **Skip fork PRs and the bot's own pushes** (`if: … head.repo.fork == false && github.actor != 'github-actions[bot]'`): fork PRs run with a read-only token and cannot be pushed to — Mend-hosted Renovate is a GitHub App creating branches on the origin repo, so its PRs are not fork PRs and are covered; the actor filter stops the approval-pending `synchronize` runs that every fix push creates (see Risks).
- **Plain `git` + `gh` commands, not a third-party auto-commit action** — no new supply-chain dependency, consistent with the existing plain-`run` workflow style.
- **Scope the commit to generated paths only** (`git add .agents/skills`) and use a conventional message (`chore(openspec): regenerate workflow skills`).
- **Run on all PRs, no path filter**: the gate also fires when a generated file is hand-edited, and auto-fixing that is the intended semantics ("generated files equal CLI output"). The job is a cheap no-op when in sync (dry-run reports no changes → no commit, no push — but the retrigger dispatch still happens).

The `ci.yaml` `on:` block as it will read:

```yaml
on:
  push:
    branches: ["main"]
  workflow_dispatch:
    inputs:
      pr_title:
        description: "PR title to lint (set by the auto-regenerate workflow)"
        required: false
        type: string
```

the gate step in the `openspec` job:

```yaml
      - name: Check generated OpenSpec files are in sync
        run: |
          test "$(./node_modules/.bin/openspec update --dry-run --json | jq '[.changes[] | select(.path | startswith("~") | not)] | length')" -eq 0
```

and the moved title job (verbatim from `commitlint.yaml`, minus its event-name gate):

```yaml
  lint-pr-title:
    if: github.event_name == 'workflow_dispatch' && github.event.inputs.pr_title != ''
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v7

      - uses: actions/setup-node@v7
        with:
          node-version: 22
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Lint pull request title
        env:
          PR_TITLE: ${{ github.event.inputs.pr_title }}
        run: echo "$PR_TITLE" | ./node_modules/.bin/commitlint
```

`commitlint.yaml` loses the `lint-pr-title` job and its `pull_request` trigger; the `lint-commits` job and the `push: branches: ["main"]` trigger are untouched.

The regenerate workflow as it will read:

```yaml
name: OpenSpec Skills Auto-Regenerate

on:
  pull_request:
    branches: ["main"]
    types: [opened, synchronize, reopened]

jobs:
  regenerate:
    if: >-
      github.event.pull_request.head.repo.fork == false &&
      github.actor != 'github-actions[bot]'
    runs-on: ubuntu-latest
    permissions:
      contents: write # push the fix to the PR branch
      actions: write # re-trigger the pipeline via `gh workflow run`
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.head_ref }} # the PR branch, not the merge ref
      - uses: actions/setup-node@v7
        with:
          node-version: 22
          cache: npm
      - name: Install dependencies
        run: npm ci
      - name: Regenerate if stale
        env:
          BRANCH: ${{ github.head_ref }}
        run: |
          if [ "$(./node_modules/.bin/openspec update --dry-run --json | jq '[.changes[] | select(.path | startswith("~") | not)] | length')" -gt 0 ]; then
            ./node_modules/.bin/openspec update
            git config user.name "github-actions[bot]"
            git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
            git add .agents/skills
            git commit -m "chore(openspec): regenerate workflow skills"
            git push
          fi
      - name: Re-trigger CI on the (possibly fixed) head
        env:
          BRANCH: ${{ github.head_ref }}
          PR_TITLE: ${{ github.event.pull_request.title }}
          GH_TOKEN: ${{ github.token }}
        run: gh workflow run ci.yaml --ref "$BRANCH" -f "pr_title=$PR_TITLE"
```

## Risks / Trade-offs

- [CI for PRs now depends on the regenerate workflow running] → `ci.yaml` no longer triggers on `pull_request`; if the regenerate workflow is deleted, disabled, or fails to parse, PRs get no pipeline runs. A failed regenerate run is visible as a failed check on the PR, and a PR without a green pipeline run cannot merge — the same outcome as a red pipeline, with the failure itself visible. Accepted.
- [Approval-pending `synchronize` runs on every fix push] → Per the current docs, a `GITHUB_TOKEN` PR update creates `pull_request` runs that require approval; each fix push therefore leaves a pending, approval-gated run of the regenerate workflow on the PR. It is a no-op by construction (in sync after the fix → no push; the retrigger step then dispatches the pipeline exactly once) and can be cancelled; the `github.actor` filter guarantees it does nothing even if approved. Cosmetic badge, not a blocker.
- [Title edits no longer re-lint immediately] → The moved `lint-pr-title` job only runs in the retriggered pipeline, so a PR title *edit* no longer triggers an immediate re-lint (the old `commitlint.yaml` ran on `edited`). The push-to-`main` `lint-commits` job still enforces the conventional title at the merge point. Accepted.
- [A manual `workflow_dispatch` without a title skips the title check] → The job's `if:` requires a non-empty `pr_title`; a manual re-run that omits it produces a run with the title check skipped, which a required-checks evaluation on that head does not count as passing. The bot always passes a title; a human re-run can supply one. Edge case, accepted.
- [Two PRs bumping the CLI in parallel → merge conflict on the regenerated files] → Resolved at PR merge; rare in a one-person repo.
- [The auto-fix overwrites in-flight hand edits to generated files on a PR branch] → Intended: the files are CLI-generated and `AGENTS.md` says not to hand-edit them.
- [`jq` availability on the runner] → Preinstalled on `ubuntu-latest`; failure mode is loud, not silent.

## Migration Plan

Three workflow files, **no** branch-protection change (the required set is unchanged and is satisfied by the single retriggered pipeline). Deployment is the merge itself; rollback is a revert. The tree is verified in sync with the pinned CLI (Task 1.1), so `main` is green on merge.

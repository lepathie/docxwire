# Design

## Context

The `openspec` job in `.github/workflows/ci.yaml` already checks out the repo, sets up Node, runs `npm ci`, and executes `openspec validate --all`. The generated files it guards are `.agents/skills/openspec-*/SKILL.md` plus a `.agents/skills/.openspec-target` marker.

Verified behavior of the OpenSpec CLI (v1.16.0): `openspec update --dry-run --json` prints `{"changes": [...], "notes": [...], "failures": []}` and **exits 0 even when `changes` is non-empty** (i.e. generated files are stale relative to the installed CLI). When in sync, `changes` is an empty array.

## Goals / Non-Goals

**Goals:**

- Any PR that leaves the generated OpenSpec files stale fails CI, so drift can never reach `main`.

**Non-Goals:**

- Automatically regenerating the files inside Renovate (a post-upgrade task). That is blocked on the Mend-hosted Renovate app — post-upgrade commands are disabled by default there and `allowedCommands` is a global-only option a repo config cannot set. If Renovate is ever self-hosted, the ready-to-use config is: `postUpgradeTasks: { "commands": ["openspec update"], "fileFilters": [".agents/skills/**"], "executionMode": "update" }` (the filter must cover `.openspec-target`, not only the `openspec-*` directories).
- Changing how the skills are generated or what they contain.

## Decisions

- **Assert on the JSON output, not the exit code.** The gate is `test "$(openspec update --dry-run --json | jq '.changes | length')" -eq 0`. Alternative considered: plain `openspec update --dry-run` relying on the exit code — rejected because the exit code is 0 while stale (verified empirically); it would never fire.
- **`jq` for the assertion.** Preinstalled on `ubuntu-latest`; more readable than a Node one-liner. If a future runner image dropped `jq`, the step fails loudly (`command not found`) rather than passing silently.
- **New step in the existing `openspec` job**, after `Validate OpenSpec artifacts`. Alternative: a separate job — rejected; it would duplicate checkout, Node setup, and `npm ci` for one extra CLI invocation.
- **Gate on `changes` only.** Operational errors already fail the step via the CLI's non-zero exit; the assertion adds exactly the sync invariant and nothing else.

The step as it will read in `ci.yaml`:

```yaml
      - name: Check generated OpenSpec files are in sync
        run: |
          test "$(./node_modules/.bin/openspec update --dry-run --json | jq '.changes | length')" -eq 0
```

## Risks / Trade-offs

- [The remedy is manual: someone runs `openspec update` and pushes to the Renovate branch] → Inherent to the hosted-app constraint; accepted. The gate converts "silently stale" into "loudly blocked", and the fix is one local command in a one-person repo.
- [`jq` availability on the runner] → Preinstalled on `ubuntu-latest`; failure mode is loud, not silent.

## Migration Plan

Single-file CI change; deployment is the merge itself, rollback is a revert. The tree is verified in sync with the pinned CLI (Task 1.1), so `main` is green on merge.

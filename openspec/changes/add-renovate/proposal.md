# Proposal

## Why

Dependency updates are currently manual (`uv lock --upgrade`, `npm install`), with no cadence. Direct dependencies and their transitive closure drift until someone remembers to refresh them, and a single catch-up update then bundles many releases at once, which is harder to review and bisect than small frequent updates. The repo already has the precondition that makes automation safe: a CI pipeline (`make ci`: lint, type check, 100%-coverage tests, OpenSpec validation) that would catch a breaking update.

## What Changes

- Add a `renovate.json` at the repository root configuring the Renovate bot for the `uv` (`pyproject.toml` + `uv.lock`) and `npm` (`package.json` + `package-lock.json`) ecosystems, plus the GitHub Actions in the CI workflows and the pinned Python version (`.python-version`).
- Define the update policy in that config:
  - 7-day minimum release age for version updates (supply-chain cooldown); security updates are not delayed.
  - Automerge for `patch` updates and for `minor`/`patch` of dev-only dependencies, gated on passing CI status checks; `0.x` versions are excluded from automerge.
  - `major` updates never automerge: they land as PRs for a human, one PR per major version (sequenced).
  - Weekly lockfile maintenance (transitive refresh) that may automerge.
- Document the policy and the manual override (requesting an update from the Renovate dashboard / branch) in the README.

## Capabilities

### New Capabilities

(None — tooling change, `skip_specs: true`)

### Modified Capabilities

(None)

## Impact

- New file: `renovate.json` (the complete policy, machine-enforced).
- Docs: a short README section on how updates flow through and how to override the policy.
- No changes to application code, CI workflows, or dependency versions. The existing `ci.yaml` status checks are what the automerge gate requires; making those checks *required* on `main` via branch protection is a repository-settings action the owner performs when installing the Renovate GitHub App, outside this repo's files.

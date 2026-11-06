# Design

## Context

See proposal.md for motivation. Constraints that shape the approach:

- Two ecosystems: `uv` (`pyproject.toml` + committed `uv.lock`, CI installs with `uv sync --frozen`) and `npm` (`package.json` with exact pins + committed `package-lock.json`, CI installs with `npm ci`).
- The repo lints commit messages and PR titles with `@commitlint/config-conventional` (`.commitlintrc.json`, `commitlint.yaml` workflow) — any bot-generated title must be a valid conventional commit.
- `make ci` (lint + type check + 100%-coverage tests) plus the OpenSpec validation job already run on every PR; these are the status checks an automerge gate can rely on.
- Dependency constraints are lower bounds only (no upper caps), so lockfile refreshes stay within declared constraints.

## Goals / Non-Goals

**Goals:**

- A single bot config (`renovate.json`) that manages both ecosystems and encodes the full update policy: 7-day release-age cooldown, tiered automerge with 0.x exclusion, manual + sequenced majors, weekly lockfile maintenance.
- Bot commits/PR titles that pass the existing commitlint gate with no config changes.

**Non-Goals:**

- No changes to CI workflows, application code, or current dependency versions.
- No second update bot (Dependabot et al.) — one bot per repo.
- Not in this change: making CI checks *required* on `main` (a repository-settings action the owner performs when installing the app).

## Decisions

**1. Renovate over Dependabot or a DIY workflow.**

| Option | Verdict | Why |
|---|---|---|
| Renovate | **Chosen** | Default commit messages are `chore(deps): bump …`, which pass this repo's commitlint as-is; `lockFileMaintenance` covers transitive drift (Dependabot has no equivalent); automerge is built in and gated on status checks; host-agnostic (GitHub, GitLab, self-hosted) — the least platform-locked option. |
| Dependabot | Rejected | Fixed `Bump X from A to B` PR titles fail the repo's `config-conventional` type check; no lockfile-maintenance mode; automerging needs a separate hand-written workflow. |
| Scheduled workflow running `uv lock --upgrade` / `npm update` | Rejected | No changelogs, no grouping, no release-age cooldown, more code to maintain — strictly less for more effort. |

**2. Config shape.** Single `renovate.json` at the repo root:

- `extends: ["config:best-practices"]` — Renovate's own recommended starting preset (weekly schedule, sensible PR limits).
- `minimumReleaseAge: "7 days"` — the supply-chain cooldown; Renovate applies it to version updates, and its vulnerability alerts are not age-gated, matching the spec.
- `lockFileMaintenance: { enabled: true, automerge: true, schedule: ["before 6am on Monday"] }` — weekly transitive refresh.
- `packageRules`, in order (later matches override earlier):
  1. `{ matchUpdateTypes: ["patch"], matchCurrentVersion: "!/^0/", automerge: true, platformAutomerge: true }`
  2. `{ matchDepTypes: ["devDependencies", "dev"], matchUpdateTypes: ["minor", "patch"], matchCurrentVersion: "!/^0/", automerge: true, platformAutomerge: true }`
  3. majors get no automerge (the default), enforced to be one PR per major via `separateMultipleMajorReleases: true` at the top level.
- `platformAutomerge: true` uses the platform's native auto-merge, which honors the repository's required-status-check branch protection — the gate is enforced by GitHub, not by the bot's word.

**3. Ecosystem coverage.** Renovate auto-detects both `uv` (from `uv.lock`) and `npm` (from `package-lock.json`) managers from the files at the repo root; no `managerFilePatterns` needed. The uv manager updates `pyproject.toml` constraints and `uv.lock` in the same PR.

## Risks / Trade-offs

- [Automerge with non-required checks would be a silent supply-chain channel] → the owner enables branch protection requiring the `lint-and-test`, `openspec`, and `lint-pr-title` checks on `main` **before** the app is installed; `platformAutomerge` is a request to merge, not an override of merge rules.
- [Bot PR titles fail commitlint] → Renovate's default `chore(deps):` prefix is conventional; verified on the first PR (task below). Fallback if a title shape fails: add a `commitMessageTopic` rule, not a commitlint weakening.
- [A 0.x dev tool (e.g. `ty` at 0.0.x) gets automerged] → both automerge rules carry `matchCurrentVersion: "!/^0/"`.
- [`dev` dep-type string differs per manager] → the rule matches `["devDependencies", "dev"]` covering npm and uv; the first bot run is inspected to confirm dev deps land in the automerge tier (task below).
- [PR volume] → the repo has 8 Python and 3 npm dependencies; at most a handful of PRs per week, and `config:best-practices` caps concurrent PRs.

## Migration Plan

1. Commit `renovate.json` and the README section (this change).
2. Owner validates the config (`renovate config-validate` via `npx`) — no app needed.
3. Owner installs the Renovate GitHub App for the repo and enables branch protection with the three required checks (both outside repo files).
4. First bot run: inspect the opened PRs for commitlint pass, correct dev/dep classification, and correct lockfile handling; fix the config if any rule misfired.

**Rollback:** close the bot's branches and remove the app's access (and optionally delete `renovate.json`). Nothing else is coupled to the bot; lockfiles and manifests are untouched until a PR is merged.

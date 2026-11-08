# Design

## Context

See proposal.md for motivation. Current state that shapes the approach:

- Three workflow files each hardcode `node-version: 22` alongside `cache: npm` in their `actions/setup-node` step: `ci.yaml` (two jobs — `openspec-validate`, `lint-pr-title`), `commitlint.yaml` (`lint-commits`), and `pr-orchestrator.yaml` (`openspec-skills-sync`). In every file `actions/checkout` runs before `setup-node`, so a file at the repo root is available when the version is resolved.
- `package.json` declares `engines.node: ">=22"`. The locked dependency tree's strictest minimum is `>=22.12.0` (the 18 `@commitlint/*` 21.x packages). Union constraints such as `>=23.5.0 || ^22.13.0 || ^20.17.0` have *lower* minimums (20.17 / 20.19) and do not raise the floor.
- No `.nvmrc` / `.node-version` exists, and there is no `.npmrc`, so `engines` is advisory (npm warns, never fails, on mismatch).
- `actions/setup-node` supports `node-version-file: <path>`, resolving the version from a file instead of a literal.
- Renovate manages `.nvmrc` as a Node-version file (it is on Renovate's supported-file list) and, when present, drives node updates from it.
- Two Renovate PRs are in flight — #5 (→24) and #6 (→26) — both editing the `node-version` literals this change removes.
- The `openspec-validate` job in `ci.yaml` is a Node job (it runs `setup-node` + `npm ci`); the guard is a Node script. `semver@7.8.6` is already a transitive dependency in the lockfile (via `@commitlint/is-ignored`), so declaring it directly adds no new transitive code.
- `.github/workflows/pr-orchestrator.yaml` already auto-heals PRs: its `openspec-skills-sync` job checks out the PR head (`github.head_ref`), and when the generated OpenSpec skills are stale it runs `openspec update`, commits, and pushes to the PR branch, then an unconditional final step re-triggers `ci.yaml` on the (possibly fixed) head. This is the template the `engines.node` auto-bump reuses.

## Goals / Non-Goals

**Goals:**

- One file (`.nvmrc`) is the single source of truth for the Node.js version, read by both CI and local dev.
- Every CI job resolves the version from `.nvmrc` via `node-version-file`, with no duplicated literals.
- `engines.node` states the true support floor — the strictest minimum in the locked tree — as a stable `>=` range.
- The `engines.node` floor is enforced in CI (guard) and auto-healed on PRs (the orchestrator bumps it when a dependency raises the tree minimum), so it never silently drops below the dependency tree's real minimum.
- A future Node bump is a one-file edit (`.nvmrc`) that Renovate drives and CI follows automatically.

**Non-Goals:**

- Enforcing engines at install time (no `.npmrc` / `engine-strict`); `engines` stays advisory.

## Decisions

- **`.nvmrc` as the single source** (over `.node-version` or the `package.json` `volta` field). `.nvmrc` is the de-facto standard filename — read by nvm, fnm, and most other version managers — and is on Renovate's supported Node-version file list, so Renovate will manage it. `.node-version` is the older nodenv name with narrower recognition; the `volta` field would couple the choice to Volta.
- **`node-version-file: .nvmrc` in all three workflows** (over keeping the literal). Removes the four duplicated `node-version: 22` values. `cache: npm` is orthogonal to how the version is spelled and is kept as-is.
- **Pin `26`** (over `24`). 26 is the current active LTS; the in-flight #6 already exercises 26 in CI. Landing the single source at the target skips the intermediate 24 step. (Owner's choice.)
- **`engines.node: ">=22.12.0"`** — the actual floor, not the CI version. The floor is a *support-policy* statement and is deliberately independent of the version CI tests. `22.12.0` is the strictest minimum in the locked tree; the value both matches reality and still admits 26.
- **Keep `engines` a `>=` range, not a pinned value.** A `>=` range already admits the next Node major, so Renovate leaves it alone across node-bump PRs. A pinned `engines.node: "26"` would be rewritten by Renovate on every bump — churn for no benefit.
- **Close #5 and #6 as obsolete.** Both edit the `node-version` literals this change deletes; leaving them open guarantees a merge conflict. This change *is* the consolidated Node migration. (Closing is the owner's action — the automation token has no admin scope.)
- **Guard as a small Node script using the `semver` package** (added as an exact-pinned devDependency, `7.8.6`), not a hand-rolled range parser. `semver.minVersion()` is the canonical, npm-maintained implementation ("the semantic version parser used by npm") and correctly handles every range shape (prereleases, `x`-ranges, hyphen ranges, `||` unions) that a hand-rolled parser would only approximate. It is already in the lockfile as a transitive dep (so no new transitive code), ISC-licensed, SLSA-provenanced, and `node >=10`-compatible; declaring it directly also removes the latent phantom-dependency fragility of importing an undeclared transitive. The script computes both the declared floor and the tree's strictest minimum via `minVersion()`; its **check** mode fails (naming the offending package) when the declared floor is lower and runs as the `make check-deps` target (invoked by the `check-deps` job in `ci.yaml`, aggregated into `make check` → `make ci`), with `--fix` in `make fix`, while its **fix** mode rewrites `engines.node` to the computed floor for the orchestrator's auto-bump.
- **Makefile as the single definition of checks; CI jobs map 1:1 to targets.** Each check group is one make target — `lint` (ty, ruff, pymarkdown), `test` (pytest), `check-specs` (`openspec validate --all` + the generated-files-in-sync check), `check-deps` (engines floor) — with `make check` aggregating them and `make ci` = `check` + `test`, so local `make ci` runs exactly what CI runs. `ci.yaml` drops the monolithic-`make ci` `lint-and-test` job and the separate `openspec-validate` / `check-dependencies` jobs in favour of one job per target (`lint`, `test`, `check-specs`, `check-deps`) running in parallel: each check runs exactly once, no target is invoked from two places, and the remote runner gets the parallelism the monolith hid. `publish-pr-checks` mirrors the five check jobs. Cost: the branch-protection required-check entries must be renamed in sync with the merge (`lint-and-test` → `lint` + `test`, `openspec-validate` → `check-specs`, `check-deps` optional) — the same one-off owner action pattern as the earlier `openspec` → `openspec-validate` rename.
- **Auto-bump reuses the orchestrator's auto-heal job, not a second job.** The `pr-orchestrator` re-trigger step is what gives every PR its CI run; a second sync job with its own re-trigger would dispatch `ci.yaml` twice per PR. So the existing sync job gains a "bump `engines.node` if stale" step (run the check; on failure run `--fix`, `git add package.json`, commit, push) placed before the single shared re-trigger, and the job is renamed `openspec-skills-sync` → `post-upgrade-tasks` (after Renovate's postUpgradeTasks, which this replaces for our workflows) to reflect that it now performs both the skills regeneration and the floor bump. The two fixes are triggered by different dependency bumps (mutually exclusive per PR in practice), so they never contend for the push.
- **`check-node-engines.mjs` has a `--fix` mode.** The CI guard uses check mode (exit non-zero); the orchestrator uses fix mode (rewrite `engines.node` to the computed floor, exit 0). One script, one source of the floor logic, two entry points.

## Risks / Trade-offs

- [CI jumps 22 → 26, skipping 24] → 26 is already validated by the in-flight #6's CI run, and the Node jobs run stable pure-JS tools (OpenSpec CLI, commitlint). Accepted.
- [Both in-flight PRs conflict with this change] → Close both as superseded; this change is the single node migration.
- [Local dev on Node < 22.12 now gets an `EBADENGINE` warning] → `engines` is advisory (no `engine-strict`), so it warns rather than fails — a nudge in the right direction, not a break. Accepted.
- [`node-version-file` resolution] → `actions/checkout` precedes `setup-node` in all three jobs, so `.nvmrc` is present when read. Failure mode (missing file) is loud, not silent.
- [Renovate's next node PR targets `.nvmrc`] → That is the intended outcome: the PR edits `.nvmrc` and CI follows.
- [The bot rewrites a support-policy value (`engines.node`)] → It only ever **raises** the floor, and only when a dependency bump forces a higher minimum (fix mode computes the lockfile's strictest minimum) — the bot is applying an inevitability, not making a policy choice. It is a `chore(deps)` bot commit on the PR branch, reviewable before merge, exactly like the existing skills-regeneration commits.
- [Adding `semver` as a direct devDependency] → It is already in the lockfile as a transitive dep (7.8.6, via `@commitlint/is-ignored`), so this promotes an existing, npm-maintained, ISC-licensed, SLSA-provenanced package to a direct dep — no new transitive code. It joins the existing Renovate devDependency loop (kept current; major bumps land as reviewable PRs, not silent automerges). Declaring it also removes the phantom-dependency fragility of importing an undeclared transitive.

## Migration Plan

Merge this change (`.nvmrc` + workflow switch + `engines` correction + guard + auto-bump + `post-upgrade-tasks` rename + `semver` devDep + make-target/CI-job 1:1 restructure). The push to `main` triggers `ci.yaml`; the Node jobs (`check-specs`, `check-deps`, `lint-pr-title`) then run on 26 from `.nvmrc`, and the `pr-orchestrator`'s renamed `post-upgrade-tasks` job is live — that first green run on `main` is the validation. In sync with the merge, the owner updates the branch-protection required set (`lint` + `test` + `check-specs`, `check-deps` optional; the old `lint-and-test` / `openspec-validate` entries removed). Close PRs #5 and #6 as superseded. Rollback is a revert (restores the `node-version: 22` literals, removes `.nvmrc` and the guard/auto-bump, renames `post-upgrade-tasks` back to `openspec-skills-sync`, restores the old Makefile targets and job layout, and drops the `semver` devDep).

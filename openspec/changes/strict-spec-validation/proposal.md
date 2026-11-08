# Proposal

## Why

`make check-specs` runs `openspec validate --all` without `--strict`, so spec-quality findings (overlong requirement text, missing SHALL/MUST, placeholder purposes) are advisory-only and can accumulate invisibly. Since upstream #1976 / #2020 these findings are proper warnings that fail `--strict` — the tooling supports enforcing the documented quality bar in CI.

## What Changes

- The `check-specs` Makefile target runs `openspec validate --all --strict`, so `make check` and `make ci` fail on spec-quality warnings.
- No spec content changes.

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

(None) — CI tooling change with no spec-level behavior change; the change declares `skip_specs: true`.

## Impact

- `Makefile` (one flag on the `check-specs` target).
- **Prerequisite:** `split-settings-example-requirement` must be archived first, or the gate goes red on the existing 558-character `settings` requirement.

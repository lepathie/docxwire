# Design

## Context

`make check-specs` (part of `make check` and `make ci`) runs `./node_modules/.bin/openspec validate --all` — non-strict. Since upstream #1976 / #2020, OpenSpec classifies spec-quality findings (overlong requirement text, missing SHALL/MUST, placeholder purposes) as warnings: normal validation passes, `--strict` fails. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**

- Make the documented spec-quality bar enforceable in CI: `make check` / `make ci` fail on spec-quality warnings.

**Non-Goals:**

- Fixing spec content — if the gate surfaces warnings in other capabilities, each is fixed in its own dedicated change (the same discipline as the length split).
- Per-lifecycle configurable limits — left to upstream (#2069).

## Decisions

1. **Adopt `--strict` on the existing `--all` invocation, not a new target.** The gate already exists and is wired into `make check` / `make ci`; adding the flag keeps one entry point. Alternative considered: a separate `check-specs-strict` target CI opts into — rejected, it leaves the default gate weak and risks drift.
2. **Land after `split-settings-example-requirement`.** The tree currently carries exactly one strict-failing finding: the 558-character `settings` requirement. Once the split is archived the tree is clean, and adding the gate is a pure policy change with no content fix bundled in.

## Risks / Trade-offs

- **Future `--strict`-only findings block unrelated PRs** → that is the point of the gate: quality debt becomes visible and paid at the point of touch instead of accumulating invisibly.
- **Upstream reclassifies a warning** → OpenSpec owns the classification; upstream #2069 (configurable per-lifecycle limits) is the path if the project wants finer control.

## Migration Plan

One-line Makefile edit; rollback is the one-line revert.

## Open Questions

(None)

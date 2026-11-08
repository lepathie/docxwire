# Design

## Context

OpenSpec flags requirement descriptions over 500 characters as a warning (upstream #1976 / #2020: advisory in normal validation, failing under `--strict`). The `settings` spec's "An example settings file is committed" requirement is 558 characters after `settings-example-base-path` appended the `base_path` pin as a third sentence. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**

- Bring the requirement under the 500-character limit without losing any stated behavior.
- Use the canonical OpenSpec split so the result is what the tooling (and its `--strict` checks) expects.

**Non-Goals:**

- Changing what the example file must document — the scenario set is identical before and after.
- Adopting `--strict` in CI — that is the separate `strict-spec-validation` change, which lands after this one.

## Decisions

1. **Canonical split, not a trim.** The specs instruction defines exactly one sanctioned way to shrink an existing long requirement: a dedicated change where the `MODIFIED` block keeps the requirement's header and every scenario while cutting the description to one behavior, and each removed behavior becomes its own `ADDED` requirement with its own scenarios. The alternative — trimming the description in place without the `ADDED` blocks — would silently drop the `basic_auth`-note and `base_path`-pin behaviors from the contract.
2. **Split into three, not two.** The description carries three normative behaviors: document all keys with placeholder values and no real credentials (kept), the `basic_auth` explanation note (added), the `base_path` pin (added). One behavior per requirement is the point of the limit.

## Risks / Trade-offs

- **Scenario duplication** → the canonical pattern keeps every scenario in the original requirement while the new requirements repeat the relevant ones. That is the documented, toolchain-verified shape (upstream #2020 verifies a split change validates `--strict`, archives, and leaves the main spec `--strict`-clean); the duplication is the price of a lossless split.

## Migration Plan

None — spec-only. The split lands when this change is archived (delta sync + move).

## Open Questions

(None)

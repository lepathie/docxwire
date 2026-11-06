# Design

## Context

`settings.toml.example` documents the `[joomla]` section for a new developer. Its `base_path` placeholder (`/index.php/api/index.php`) is the legacy pre-Joomla 4 path shape; the `joomla-client` verification gate confirmed the club site's content API lives at `/api/index.php/v1` (see the archived change's design, "Verified contract"). See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**

- The example documents a `base_path` that works on a stock Joomla 5 site.
- The example becomes a contract: a test asserts the placeholder, so it cannot silently regress.

**Non-Goals:**

- The settings loader (it already accepts any `base_path` string).
- Customize `settings.toml` file locally, it's already configured.

## Decisions

1. **Pin the placeholder in the spec and assert it in the test.** Alternatives considered: fixing the file without a spec change (drift can return), or having the loader warn about the legacy shape (overkill — `base_path` is site-specific configuration, not something to validate).

## Risks / Trade-offs

- **A different Joomla 5 installation may serve the API from a different path** → the placeholder documents the stock shape; `base_path` remains free-form configuration, and the spec pins only the example's value.

## Migration Plan

None — documentation-only.

## Open Questions

(None)

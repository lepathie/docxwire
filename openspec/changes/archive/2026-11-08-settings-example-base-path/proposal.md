# Proposal

## Why

The `base_path` placeholder in `settings.toml.example` (`/index.php/api/index.php`) is the legacy pre-Joomla 4 API path shape. The `joomla-client` verification gate confirmed on the club's Joomla 5 site that the content API lives at `/api/index.php/v1` — the legacy placeholder 404s. A developer who copies the example and fills in only `base_url` and `token` ends up with a non-working `base_path` and an obscure 404 on the first API call.

## What Changes

- Change the `base_path` placeholder in `settings.toml.example` to the Joomla 5 API path shape `/api/index.php/v1`.
- Pin that placeholder in the settings spec so the example keeps documenting a working path.

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

- `settings`: the example-file requirement now pins the `base_path` placeholder to the Joomla 5 API path shape `/api/index.php/v1`.

## Impact

- `settings.toml.example` (one line) and `tests/settings/test_settings.py` (a test for the committed example).
- No impact on the settings loader, on existing custom `settings.toml` files (gitignored), or on the `joomla-client` change.

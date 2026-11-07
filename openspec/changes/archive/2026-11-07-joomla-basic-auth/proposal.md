# Proposal

## Why

Some publishing targets (e.g. the club's own staging site) sit behind an HTTP Basic Auth
gate in front of the Joomla API. The client currently sends only the Joomla token
(`X-Joomla-Token`), so it cannot get past such a gate. We need an optional, per-target
Basic Auth layer that composes with the existing token auth and stays off by default.

## What Changes

- Add an optional `basic_auth` key to the `[joomla]` settings section. When present,
  its value is sent verbatim as the `Authorization: Basic <value>` header on every
  request; when absent, no `Authorization` header is sent (existing behavior unchanged).
- `JoomlaSettings` gains an optional `basic_auth` field (defaults to unset); the
  settings loader reads it and type-checks it as a string when present.
- `JoomlaClient` sets the `Authorization` header on its shared session only when
  `basic_auth` is configured.
- `settings.toml.example` documents the new key, including a short note on how to
  derive the value from a `username:password` pair (base64).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `joomla-client`: the "configured from Joomla settings" requirement gains an optional
  `Authorization: Basic` header, sent only when the setting is present.
- `settings`: the `[joomla]` section documents and validates a new optional `basic_auth`
  string key; the committed example file lists it.

## Impact

- Code: `src/docxwire/settings.py` (new optional field + type check),
  `src/docxwire/joomla/client.py` (conditional header in `__init__`).
- Config: `settings.toml.example` (new documented key).
- No breaking change: the key is optional and defaults to unset, so existing
  `settings.toml` files are unaffected.
- Tests: `tests/settings/test_settings.py` and `tests/joomla/test_client.py`.

# Tasks

## 1. Settings: optional `basic_auth` key

- [x] 1.1 Add `basic_auth` coverage to `tests/settings/test_settings.py` (loaded verbatim when present; unset when the key is absent; a non-string value raises `SettingsError`), run it and confirm it fails, then add the optional `basic_auth` field to `JoomlaSettings` and read + type-check it in `load_settings` so the new tests pass.
- [x] 1.2 Document `basic_auth` in `settings.toml.example` with a placeholder value and a short note on base64-encoding a `username:password` pair for classical Basic Auth gates, and confirm the file lists the key and the note by reading it back.

## 2. Client: optional `Authorization: Basic` header

- [x] 2.1 Add `basic_auth` coverage to `tests/joomla/test_client.py` (the `Authorization: Basic <value>` header is present and verbatim when configured; no `Authorization` header when not configured; both `Authorization` and `X-Joomla-Token` are present when both are set), run it and confirm it fails, then set the header on the session in `JoomlaClient.__init__` only when `basic_auth` is set so the new tests pass.

## 3. Verification

- [x] 3.1 Run `make ci` (lint, type check, tests at 100% coverage) and confirm it is green.

## Workflow follow-up

- Archive the change (`openspec archive`) once the project's review requirements are satisfied, then verify the archived result.

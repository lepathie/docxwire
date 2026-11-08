# Tasks

## 1. Example file

- [x] 1.1 Add a test asserting that the committed `settings.toml.example` parses as TOML, its `[joomla]` section lists all four keys with placeholder values, and `base_path` is `/api/index.php/v1` — verify it fails against the current example
- [x] 1.2 Change the `base_path` placeholder in `settings.toml.example` to `/api/index.php/v1` — verify the test passes
- [x] 1.3 Run `make ci` (lint, type check, tests at 100% coverage) — verify it is green

## Workflow follow-up

- Archive this change (move to `changes/archive/` + spec sync) once `make ci` is green and the user has reviewed — its own commit, per repo convention.

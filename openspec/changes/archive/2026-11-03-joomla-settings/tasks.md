# Tasks

## 1. Settings file layout

- [x] 1.1 Add `settings.toml` to `.gitignore` and verify `git check-ignore settings.toml` reports it as ignored
- [x] 1.2 Create `settings.toml.example` at the repository root with a `[joomla]` section documenting `base_url`, `base_path`, `token`, and `default_catid` with placeholder values, and verify it parses as valid TOML (e.g. `python -c "import tomllib; tomllib.load(open('settings.toml.example', 'rb'))"`)

## 2. Settings module

- [x] 2.1 Implement `src/docxwire/settings.py` with a `SettingsError`, frozen `JoomlaSettings` (`base_url`, `base_path`, `token`, `default_catid = 0`) and `Settings` dataclasses, and a `load_settings(path)` function using stdlib `tomllib` (default path `settings.toml` in the working directory), and verify the happy-path tests pass (valid file via default path, explicit path honored, values preserved, omitted `default_catid` yields `0`)
- [x] 2.2 Add the error-path tests to `tests/settings/` (missing file → error referencing `settings.toml.example`; malformed TOML → wrapped `SettingsError`, not the raw parse exception; missing `[joomla]` section; missing required key names the key; non-integer `default_catid`) and verify they all pass
- [x] 2.3 Add a test that the converter package works without a settings file present (conversion succeeds with no `settings.toml` in the working directory, and `docxwire.converter` does not import `docxwire.settings`) and verify it passes

## 3. Integration check

- [x] 3.1 Run `make ci` (lint, type check, tests with 100% coverage) and verify it is green

## Workflow follow-up

- Archive the change (move to `changes/archive/` + sync the `settings` spec) as its own commit, once `make ci` is green and the user is satisfied.

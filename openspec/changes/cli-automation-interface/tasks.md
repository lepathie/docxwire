# Tasks

Self-contained: no prerequisite changes (the env loader and the CLI flags
land together, so no release ships an inaccessible primitive).

## 1. Env-based settings loader

- [ ] 1.1 Factor the `[joomla]` section validation (required keys, types, defaults, `SettingsError` messages) out of `load_settings` into a shared helper in `src/docxwire/settings.py` and verify the existing TOML tests in `tests/settings/test_settings.py` still pass unchanged
- [ ] 1.2 Add `load_settings_from_env()` reading `DOXXWIRE_JOOMLA_BASE_URL`, `DOXXWIRE_JOOMLA_BASE_PATH`, `DOXXWIRE_JOOMLA_TOKEN`, `DOXXWIRE_JOOMLA_DEFAULT_CATID`, `DOXXWIRE_JOOMLA_BASIC_AUTH`, `DOXXWIRE_JOOMLA_DEFAULT_LANGUAGE` through the shared helper, with error messages naming the variable; verify `uv run pytest tests/settings` passes
- [ ] 1.3 Add the env-loader test matrix from the spec delta: all six variables set → values preserved; each required variable missing → `SettingsError` naming that variable; `default_catid` omitted → `0`; `basic_auth` omitted → unset; `default_language` omitted → `*`; non-integer `default_catid` → `SettingsError`; empty-string value passes the type check as in TOML; verify `uv run pytest tests/settings` passes

## 2. CLI flags

- [ ] 2.1 Add `--json` and `--settings-env` flags to the argument parser in `src/docxwire/cli.py` (both optional, `action="store_true"`) and verify `docxwire --help` lists them while an unknown option still exits 2 with the usage text
- [ ] 2.2 Implement the `--json` output: on success a single JSON object `{"id", "title", "note"}` on stdout (note `""` when empty, `ensure_ascii=False`), on an operational failure a single `{"error": "…"}` object on stdout with the existing exit code 1; verify new tests in `tests/test_cli.py` assert the exact stdout objects and exit codes
- [ ] 2.3 Wire `--settings-env` to `load_settings_from_env()` (replacing the `settings.toml` lookup when the flag is set; a missing/invalid env source exits 1 with a message naming the variable) and verify with tests covering: env vars used when the flag is set, missing required variable → actionable error, and `settings.toml` not required in the CWD
- [ ] 2.4 Verify the default behavior is unchanged: all pre-existing `tests/test_cli.py` tests (human-oriented output, TOML settings, exit codes) pass without modification

## 3. Verification

- [ ] 3.1 Run `make ci` on the full change (lint, type check, 100%-coverage tests, specs) and verify it is green

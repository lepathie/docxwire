# Proposal

## Why

Publishing to Joomla needs per-environment connection settings — the site's base URL, the API endpoint path, the API token, and the default article category — and the repository currently has nowhere to hold them. The forthcoming Joomla client has nothing to read its configuration from, and the token is a secret that must never be committed. We need a gitignored per-developer file plus a committed example, and a single validated loader that all future consumers share.

## What Changes

- Add a committed `settings.toml.example` at the repository root documenting a `[joomla]` section with `base_url`, `base_path`, `token`, and `default_catid`.
- Add `settings.toml` (the per-developer, gitignored real file) to `.gitignore`.
- Add a new top-level module `src/docxwire/settings.py`: frozen `Settings` / `JoomlaSettings` dataclasses and a `load_settings(path)` function that parses TOML with the stdlib `tomllib` (no new dependency), validates key presence and types, and raises an actionable `SettingsError` (a missing file points at the example file).
- `default_catid` is the only optional key and defaults to `0`, matching the `Article.catid` "unset" sentinel. Mapping `0 → default_catid` is the future publisher's job, not this module's.
- The converter is unchanged and never reads settings; only the future publishing step loads configuration.

## Capabilities

### New Capabilities

- `settings`: the settings file layout (committed example, gitignored real file), the `[joomla]` TOML schema, and the loader contract (default path, explicit path, defaults, validation, and error behavior).

### Modified Capabilities

(None)

## Impact

- **New code:** `src/docxwire/settings.py`, `tests/settings/` (CI enforces 100% coverage).
- **Repo files:** `settings.toml.example` (new), `.gitignore` (one added line).
- **Dependencies:** none — `tomllib` is stdlib (the project already requires Python ≥ 3.11.5).
- **Converter:** untouched; it keeps working with no settings file present.
- **Future work:** the Joomla client change consumes `load_settings()`; the `Article.catid → default_catid` mapping lands there.

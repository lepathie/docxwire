# Proposal

## Why

The `docxwire` CLI is the project's automation entry point — the Azure
Function built by `azure-functions-deployment` invokes it — but its interface
is human-oriented: a free-form two-line stdout report, and settings only from
`settings.toml` in the current working directory. Automations need a stable
machine-readable result contract and a way to be configured through
environment variables. Both halves ship in this one change so that no
release contains an inaccessible primitive: after it lands,
`docxwire <file> --settings-env --json` works end to end.

## What Changes

- New `load_settings_from_env()` in `docxwire.settings`: reads
  `DOXXWIRE_JOOMLA_BASE_URL`, `DOXXWIRE_JOOMLA_BASE_PATH`, and
  `DOXXWIRE_JOOMLA_TOKEN` (required), plus the optional
  `DOXXWIRE_JOOMLA_DEFAULT_CATID` (integer, default `0`),
  `DOXXWIRE_JOOMLA_BASIC_AUTH`, and `DOXXWIRE_JOOMLA_DEFAULT_LANGUAGE`
  (default `*`), validating its input exactly like the TOML loader does for
  the same values
- New `--settings-env` CLI flag: settings are read from the
  `DOXXWIRE_JOOMLA_*` environment variables instead of `settings.toml` in
  the working directory
- New `--json` CLI flag: in this mode stdout carries exactly one JSON object
  — on success `{"id": …, "title": …, "note": …}`, on an operational failure
  `{"error": "…"}`. Exit codes (0 success, 1 operational failure, 2 usage
  error) are unchanged and remain the discriminator; usage errors keep the
  argparse text output
- The default (human-oriented) output, the TOML settings source, and the
  settings example file are unchanged

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

- `settings`: gains the requirements that settings can be loaded from
  environment variables and that the env source validates like the TOML
  source; the existing TOML-file requirements are unchanged
- `cli`: the command accepts two optional flags; the success-reporting
  requirement gains the `--json` output contract; the settings-source
  requirement gains the environment-variable source selected by
  `--settings-env`

## Impact

- `src/docxwire/settings.py` — new env loader (additive; validation shared
  with the TOML loader)
- `src/docxwire/cli.py` — parser flags, JSON output, env settings wiring
- `tests/settings/test_settings.py`, `tests/test_cli.py` — new tests;
  pre-existing tests must pass unchanged
- No dependency changes; `make ci` stays green

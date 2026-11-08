# Proposal

## Why

The `settings` spec's "An example settings file is committed" requirement is 558 characters, over OpenSpec's 500-character recommendation, ever since `settings-example-base-path` appended the Joomla 5 `base_path` pin to it. The warning is advisory in CI today, but the requirement now carries three distinct behaviors in one description.

## What Changes

Split the overlong requirement using OpenSpec's canonical split (per the specs instruction and upstream issue #1976 / PR #2020):

- `MODIFIED` "An example settings file is committed": description cut to one behavior (the committed example documents every supported key with placeholder values and no real credentials); header and all three scenarios kept.
- `ADDED` "The example explains the Basic Auth value": the `basic_auth` note behavior, with its own scenario.
- `ADDED` "The example pins the Joomla 5 base_path": the `base_path` placeholder behavior, with its own scenario.

No behavior change: the set of scenarios is identical before and after the split.

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

- `settings`: one requirement becomes three; nothing is added, removed, or renamed beyond the split.

## Impact

- `openspec/specs/settings/spec.md` only, via the delta at archive sync. No code, no tests, no settings files.

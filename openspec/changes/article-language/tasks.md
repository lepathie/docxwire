# Tasks

## 1. Settings

- [ ] 1.1 Add the optional `language` key to `JoomlaSettings` (default `*`) with loader validation (missing → `*`; non-string → settings error) and tests for the default and the wrong type — verify the tests pass
- [ ] 1.2 Add a test asserting the committed `settings.toml.example` parses as TOML, its `[joomla]` section documents every supported key with a placeholder, `base_path` is `/api/index.php/v1`, and `language` is `*` — verify it fails against the current example
- [ ] 1.3 Update `settings.toml.example` to add `language = "*"` — verify the test passes

## 2. Article and mapping

- [ ] 2.1 Add the optional `language` field to the `Article` dataclass (default empty) — verify `make ci` stays green
- [ ] 2.2 Change `build_article_payload` to take the `JoomlaSettings` and resolve the payload's `language` (article → settings → `*`), updating the existing mapping tests to the new signature and adding one test per resolution level — verify the tests pass

## 3. Integration

- [ ] 3.1 Run `make ci` (lint, type check, tests at 100% coverage) — verify it is green

## Workflow follow-up

- Apply only after `settings-example-base-path` is archived.
- Archive this change (move to `changes/archive/` + spec sync) once `make ci` is green and the user has reviewed — its own commit, per repo convention.

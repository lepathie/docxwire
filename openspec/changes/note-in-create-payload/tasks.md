# Tasks

## 1. Mapping carries the note

- [ ] 1.1 Add failing tests to `tests/joomla/test_mapping.py` in `TestMetadataCarryOver`: the payload's `note` equals the article's non-empty note (e.g. `Prüfe: Titel` via `make_article(note=…)`) and is the empty string for a clean article; verify both tests fail against the current mapping
- [ ] 1.2 Add `"note": article.note` to the payload dict in `build_article_payload` (`src/docxwire/joomla/mapping.py`); verify the new tests pass and the full `tests/joomla/test_mapping.py` file passes

## 2. Verification

- [ ] 2.1 Run `make ci`; verify lint, type check, and the test suite at 100% coverage all pass, including `openspec validate --all --strict`

## Workflow follow-up

- Archive the change once the user is satisfied (spec sync into `openspec/specs/joomla-client/spec.md` + move to `openspec/changes/archive/`) — user-initiated per repo rules.

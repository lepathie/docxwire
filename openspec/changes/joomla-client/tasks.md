# Tasks

## 1. Live verification (gate — before any implementation)

- [ ] 1.1 Confirm prerequisites: `joomla-settings` is implemented (`load_settings()` importable) and a `settings.toml` with real `[joomla]` values exists in the working directory — verify by loading it with stdlib `tomllib` and printing key names/types only (never values)
- [ ] 1.2 Run read-only probes (list with `limit`, get one known article) against the live site and record the response envelope, item shape, and a real article's field names in the design's "Verified contract" section — verify the section is filled with observed data
- [ ] 1.3 Run the write round trip (create a clearly marked `[docxwire-test]` article in `default_catid` with the body in `introtext` and empty `fulltext` → get → patch title → get → delete → get expecting 404) plus the field matrix (`introtext` vs `fulltext` vs `articletext` persistence, duplicate-alias behavior, `created` format acceptance, resulting workflow state) and record the findings in the "Verified contract" section — verify the round trip completed, the test article is gone (final GET returns 404), and the section is filled
- [ ] 1.4 Reconcile the spec with the verified contract and, if any expectation was contradicted, revise `specs/joomla-client/spec.md` before implementation starts — verify `openspec validate --change joomla-client` passes and the spec matches the observed behavior

## 2. Client implementation

- [ ] 2.1 Add `requests` as a runtime dependency (`uv add requests`) — verify `uv sync` succeeds and `import requests` works in the project environment
- [ ] 2.2 Scaffold the `src/docxwire/joomla/` subpackage (`__init__.py` re-exports, `client.py`, `mapping.py`) — verify the package imports cleanly and `make ci` stays green
- [ ] 2.3 Implement `JoomlaApiError` and the request core (endpoint composition from `JoomlaSettings`, `X-Joomla-Token` header, `{"errors": [...]}` envelope parsing, no retries) with unit tests for the 401, 404, and 5xx scenarios — verify the tests pass
- [ ] 2.4 Implement the CRUD surface (`list_articles` with filter/ordering pass-through, `get_article`, `create_article`, `update_article`, `delete_article`) with unit tests covering every CRUD spec scenario against a mocked session — verify the tests pass
- [ ] 2.5 Implement `build_article_payload` (title/alias/catid with the `0 → default_catid` fallback, `introtext` = full body with empty `fulltext`, `created_by_alias`/`metadesc`/`metakey`/`created` carry-over, no `articletext`) with unit tests for each mapping spec scenario — verify the tests pass

## 3. Integration

- [ ] 3.1 Run `make ci` (lint, type check, tests at 100% coverage) — verify it is green
- [ ] 3.2 Drive the implemented client (not raw requests) through one live round trip: create a marked test article from a real `Article`, get it back, update its title, delete it — verify each step behaves as specified and the test article is gone

## Workflow follow-up

- Archive this change (move to `changes/archive/` + spec sync) once `make ci` is green and the user has reviewed — its own commit, per repo convention.
- The `joomla-settings` change is archived independently when it lands.

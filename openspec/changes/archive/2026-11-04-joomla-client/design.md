# Design

## Context

The converter produces a complete `Article` (title, slug, body HTML, images, author, dates, metadata) and nothing consumes it — there is no publishing side. The `joomla-settings` change (landed and archived) supplies the configuration contract: a frozen `JoomlaSettings(base_url, base_path, token, default_catid)` from `load_settings()`, and reserves `src/docxwire/joomla/` as this client's home. The only community documentation of the Joomla 5 content API (the reverse-engineered Postman collection) is unreliable — it shows the Joomla 1.5-era `articletext` field where Joomla 4/5/6 use `introtext`/`fulltext` — so the contract must be established against the live site before implementation. Constraints: CI enforces 100% test coverage; OpenSpec artifacts are public (no tokens, no category IDs); the site runs Joomla 5 and migrates to Joomla 6 within a year.

## Goals / Non-Goals

**Goals:**

- A thin, easily mockable transport over the five article endpoints, authenticated with `X-Joomla-Token`.
- One pure, unit-testable mapping seam (`Article` → payload) that is the only place Joomla field knowledge lives.
- A contract grounded in observed live behavior, not in the community approximation.
- 100% coverage with zero network access in CI.

**Non-Goals:**

- Media upload, image-reference rewriting, tags, and the `introtext`/`fulltext` read-more split (later increments).
- Any publishing orchestration / CLI (the client is a library; a future step drives it).
- Retries, connection pooling knobs, caching, response dataclasses, environment-variable configuration.

## Decisions

1. **`requests` as the one new runtime dependency.** The tool is CLI-shaped and synchronous; `requests` is the thin, universal choice with a trivially mockable session. Alternatives: `httpx` (async capabilities this project does not need — rejected for dependency weight), stdlib `urllib` (hand-rolled JSON/header/error plumbing and a worse mocking story — rejected).
2. **`src/docxwire/joomla/` subpackage with two modules.** `client.py` (transport + CRUD + `JoomlaApiError`) and `mapping.py` (the pure payload builder); `__init__.py` re-exports the public surface. The subpackage follows the precedent set by the settings design ("a real domain gets its own subpackage"); the two-module split keeps the dumb transport separate from the only place Joomla semantics live.
3. **The client is constructed from `JoomlaSettings`, not scalars.** One coupling point to the settings contract; the endpoint is composed as `base_url + base_path + "/content/articles[/{id}]"`.
4. **Thin CRUD over raw dicts.** Methods `list_articles`, `get_article`, `create_article`, `update_article`, `delete_article` return the API's JSON data untyped. A `RemoteArticle` dataclass is deliberately deferred until an orchestration step needs one — adding it later is an additive change.
5. **`build_article_payload(article, default_catid) -> dict` is pure.** Maps `title`→`title`, `slug`→`alias`, `catid`→`catid` (with `0 → default_catid`), `body`→`introtext`, plus a literal empty `fulltext`, and carries `created_by_alias`, `metadesc`, `metakey`, and the creation date into `created` (converted to Joomla's `Y-m-d H:i:s` form; acceptance confirmed by the probe). `state` is deliberately NOT sent: created articles land in the site's workflow "new"/unpublished state (verified: state 0), so publishing remains a human editorial act. `language` IS sent (the live site rejects creates without it, 400 "Field 'language' doesn't have a default value"); this change sends the all-languages sentinel `*`, and the value's resolution (article → settings → `*`) is deferred to the follow-up `article-language` change. `articletext` is never emitted.
6. **`JoomlaApiError(status, errors)` for all non-2xx.** The `{"errors": [...]}` envelope is parsed into the exception; a body that does not match the envelope falls back to carrying the raw text. No automatic retries, ever — a failed publish must be visible.
7. **Verification-first, recorded in this document.** Before any implementation, a throwaway probe script (reads `settings.toml` directly via stdlib `tomllib`, so it has no dependency on the settings module) runs the ladder against the live site:
   - P1 `GET /content/articles?limit=3` — auth, envelope, item shape
   - P2 `GET /content/articles/{id}` — real article's field names
   - P3 `POST /content/articles` — marked test article (`[docxwire-test] …`), body in `introtext`, `fulltext` empty, in `default_catid`
   - P4 `GET` the new ID — assert the body actually persisted (guards against a 201-that-drops-fields), note which optional fields stuck
   - P5 `PATCH` the title → P6 `GET` to confirm
   - P7 `DELETE` → P8 `GET` expecting 404
   - field matrix folded into P3/P4: `introtext` vs `fulltext` vs `articletext`; duplicate-alias behavior; `created` format acceptance
   Findings land in the **Verified contract** section below. Any contradiction with the spec triggers a spec revision *before* implementation tasks start.
8. **Tests mock the HTTP layer.** The client's `requests` session is injected/monkeypatched; every spec scenario maps to a unit test. No test touches the network; the live probe is a one-time manual gate, not part of CI.

## Verified contract

Verified against the live club site on 2026-11-03 (read-only probes plus one marked create/patch round trip; the test articles were trashed afterwards via `PATCH state: -2`).

- **Base path:** the API lives at `<base_url>/api/index.php/v1` — `settings.toml`'s `base_path` must be `/api/index.php/v1`. The `settings.toml.example` placeholder (`/index.php/api/index.php`) 404s; tracked as the `settings-example-base-path` change.
- **Accept header:** every request must send `Accept: application/vnd.api+json`; without it the API answers 406 "Could not match accept header" (content negotiation happens before routing and auth).
- **Authentication:** `X-Joomla-Token` works. A bad token answers 401 with `{"errors": [{"title": "Forbidden"}]}`.
- **Read shape (JSON:API):** collections return `{links, data: [item], meta}`; single resources return `{links, data: item}`; an item is `{type: "articles", id: <string>, attributes: {...}, relationships: {category, created_by, modified_by, tags}}`. The stored body is exposed as the `attributes.text` string; read responses contain no `introtext`/`fulltext`/`articletext`.
- **Write shape (flat):** create and update accept a flat JSON body with `Content-Type: application/json`. A JSON:API-shaped write body (`{"data": {"attributes": ...}}`) is not parsed and fails with "Field required: Title / Category".
- **Create:** flat fields `title`, `alias`, `catid` (integer), the body field, `created_by_alias`, `metadesc`, `metakey`, `created` (`Y-m-d H:i:s` accepted), and `language` are all accepted and persisted (all read back on the created article). Created articles land in state 0 (unpublished) — publishing remains a human editorial act. `language` is **required** on this site (400 "Field 'language' doesn't have a default value" without it); the mapping sends the all-languages sentinel `*`.
- **Field matrix:** both `articletext` and `introtext` are accepted on create and persist; the body is returned on read as `text`. The mapping keeps `introtext` (full body) with empty `fulltext` and never emits `articletext`.
- **Update (PATCH):** flat; `{"title": ...}` updates the title (200, confirmed on read-back); `{"state": -2}` moves the article to the trash.
- **Delete (DELETE):** answers 204 with an empty body. On a *live* article it is a **no-op** (state unchanged, still addressable) — the spec's original "a subsequent get 404s" expectation was contradicted and revised. On a *trashed* article it is a true hard delete (verified: create → `PATCH state: -2` → `DELETE` → subsequent GET 404s). Full removal is therefore two steps: trash (`PATCH state: -2`), then `DELETE`.
- **404 envelope:** `{"errors": [{"title": "Resource not found", "code": 404}]}`.
- **Duplicate-alias behavior:** not exercised (the probe used unique timestamped aliases); not needed for the MVP mapping, which always sends the article's own slug.

## Risks / Trade-offs

- **Probes write to the live club site** → one clearly marked test article, created and deleted within a single round trip, in the category the operator chooses via `default_catid`; read-only probes (P1–P2) run first and can stop there if anything looks wrong.
- **The community spec misleads (the `articletext` trap: a 201 that silently drops the body)** → P4 reads the created article back and asserts body persistence, not just a success status.
- **Secrets in a public artifact** → the probe script and this document never print or record the token or the category ID; `settings.toml` is gitignored.
- **`requests` as a new dependency** → single, mainstream, stable; the brief explicitly asks for a thin client, and this is the thinnest credible option.
- **Joomla 6 migration within a year** → `introtext`/`fulltext`, the endpoint paths, and `X-Joomla-Token` are stable across the 4/5/6 line; the contract is re-probed at migration time.

## Migration Plan

None — new facility. Roll-forward order: `settings.toml` exists (its `base_path` was corrected to `/api/index.php/v1` during the probe) → probe runs and fills the Verified contract (done 2026-11-03) → implementation.

## Open Questions

- The exact `created` timestamp format the site's API accepts (probe P3 answers; if `Y-m-d H:i:s` is rejected, the mapping's conversion is adjusted — no spec change).
- What workflow state created articles land in (probe P4 observes; expected "new"/unpublished — informational, no spec change).

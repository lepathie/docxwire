# Proposal

## Why

DOCxWIRE converts `.docx` submissions into a complete `Article` (title, slug, body HTML, images, metadata) but has no way to publish it: there is no link to the club's Joomla 5 site. The Joomla 5 REST API (`/api/index.php/v1/content/articles`) is that link, but its only community-documented surface (the reverse-engineered Postman collection) is unreliable — e.g. it shows the Joomla 1.5-era `articletext` field instead of the modern `introtext`/`fulltext` pair — so the client must be thin, and its contract must be verified against the live API before any of it is committed.

## What Changes

- New top-level subpackage `src/docxwire/joomla/` holding a **thin HTTP client** for the Joomla 5 content API with the full article CRUD surface: list, get, create, update (PATCH), and delete. Only *create* is needed for the MVP; the rest exists so testing and later orchestration are easy.
- The client is constructed from the `JoomlaSettings` dataclass of the `joomla-settings` change (`base_url`, `base_path`, `token`, `default_catid`); authentication is the `X-Joomla-Token` header. That change has landed (implemented, synced, and archived on 2026-11-03), so the prerequisite is met.
- A **pure payload-mapping function** is the single place Joomla knowledge lives: `Article` → JSON payload (`title`, `alias` from `slug`, `catid` with the `0 → default_catid` mapping, body into a single body field, `created_by_alias`, `metadesc`, `metakey`, creation date). For the MVP the entire body goes into one field — expected `introtext` with `fulltext` empty, **to be confirmed by live verification** (the deprecated `articletext` is deliberately excluded; the site migrates to Joomla 6 within a year).
- Non-2xx API responses of the form `{"errors": [...]}` are surfaced as a typed `JoomlaApiError` carrying the status and the server's error entries.
- **Verification gate:** before implementation, a live probe runs against the club's Joomla 5 site using a real token from `settings.toml`: read-only list/get probes, a field-shape probe (which of `introtext`/`fulltext`/`articletext` actually stores the body), and a full create → get → update → get → delete → get round trip with a clearly marked test article in the configured default category. The probe's findings are recorded in `design.md`; if they contradict the spec, the spec is revised before implementation proceeds.
- **Out of scope (later increments):** media upload and image-reference rewriting, article tags, the `introtext`/`fulltext` split at a "read more" marker, and the resolution of the payload's `language` value (per-article / per-settings) — the follow-up `article-language` change.

## Capabilities

### New Capabilities

- `joomla-client`: the thin Joomla 5 REST client — configuration source, transport and authentication, the article CRUD surface, the `Article` → payload mapping contract (including the verified body field), and error surfacing.

### Modified Capabilities

(None)

## Impact

- **New code:** `src/docxwire/joomla/` (client + payload mapping + error type), `tests/joomla/` (CI enforces 100% coverage; HTTP is mocked, no network in tests).
- **Dependencies:** one new runtime dependency, `requests`.
- **Prerequisite:** the `joomla-settings` change — **met** (implemented, synced, and archived) — the client consumes `load_settings()` / `JoomlaSettings` from `docxwire.settings`.
- **Converter:** untouched.
- **Live site:** the verification round trip briefly creates (and then deletes) one clearly marked test article in the category named by `default_catid` in `settings.toml`.

# Design

## Context

The converter produces a complete `Article` whose `images` carry the extracted
bytes (`Image.media_filename` is byte-identical to the `<img src>` in the body,
e.g. `media/image1.jpg`); `Image.upload_path` exists but is never populated, and
`build_article_payload` publishes the body's local references verbatim — dead on
the site. The `joomla-client` change deliberately deferred "media upload,
image-reference rewriting" as a later increment; this is it. The target site
runs a 5.4-line Joomla 5 whose `com_media` REST API can write into the site's
`images/` tree, and the content API's article payload carries an `images`
object for intro/fulltext imagery. The contract below was established by
probing the staging site (four rounds; every write cleaned up). Constraints:
100% test coverage with zero network access in CI; OpenSpec artifacts are
public (no hosts, tokens, or IDs).

## Goals / Non-Goals

**Goals:**

- A thin upload method on `JoomlaClient` reusing the existing session, headers,
  and `{"errors": [...]}` failure handling.
- One pure mapping seam that turns uploaded images into correct payload
  references (body `src` rewrite + `images` object) — the only place the
  slot-assignment and directory-scheme knowledge lives.
- A live-verified contract recorded in this document.

**Non-Goals:**

- Image compression or any web-traffic optimization (explicitly out of scope).
- The publishing orchestration that sequences upload → `upload_path` → payload
  (the client is a library; a future step drives it).
- Prioritization among secondary lead images; the `introtext`/`fulltext`
  read-more split; site-side extensions (not needed).

## Decisions

1. **The core `com_media` API is the transport — no site-side extension.**
   The 5.4-line Media API uploads into the `images/` root through its
   `local-images` adapter. Alternatives: a custom site extension with its own
   upload route (rejected — the core API already reaches `images/`); the Media
   Manager's CMS endpoints (rejected — a UI surface with CSRF tokens, not an
   API).

2. **Upload request is JSON with base64 `content`, not multipart.**
   The API's add operation reads `path` and `content` from a flat JSON body
   (`content` = base64 of the raw bytes), with `override` controlling
   overwrite. `override: true` makes re-publishes idempotent. This keeps the
   client uniform: one `_request` path, one header set, one error envelope.

3. **Path argument shape is `<adapter-id>:/<path>`; item ops use URL segments.**
   The resolver splits on the first `:` — the left side must be the adapter
   *id* (`local-images`, as returned by `GET /media/adapters`), the right side
   a leading-slash site-relative path. A bare name (`images:…`) 500s. Reads
   accept `?path=`, but DELETE only works with the path as a URL segment
   (`/media/files/local-images:/…`); `?path=` on DELETE 404s. Folder deletion
   is recursive.

4. **Directory scheme: `images/articles/<YYYY>/<MM>/<slug>/`.**
   `<YYYY>`/`<MM>` come from the article title's date prefix — the same prefix
   `slugify` already consumes (`2026.10 Abrudern` → `2026`, `10`); the inner
   folder is the article's slug verbatim (the same value sent as `alias`).
   This matches the site's existing layout (`images/articles/2026/01/…`).
   Fallback when a title has no date prefix: the article's creation date; if
   that is missing too, the upload fails loudly. Alternatives: flat
   `articles/<slug>/` (rejected — diverges from the site's layout);
   date-first inner folder names (rejected — the slug is the one stable
   identity, reused from the payload's `alias`).

5. **Lead-slot assignment without a new `Image` flag.**
   The first lead in document order — the first `is_lead` entry of
   `Article.images`, which `article-note-review-gate` D5 orders by document
   position — is emitted in the payload's `images` object in *both* slots:
   `image_intro` (displayed in the blog/listing layout) and `image_fulltext`
   (displayed on the article page), each with the image's caption and an empty
   `alt`. With no lead image the `images` key is omitted entirely. Secondary
   leads are uploaded but unreferenced. The `attribs.featured_image` route was
   probed and rejected: accepted on write, not exposed on read — a silent
   drop, unverifiable. No new flag (e.g. `is_intro`) is added; document order
   plus `is_lead` is the single encoding. This decision is the slot
   assignment that change's `_lead_label` seam was waiting for.

6. **The reference rewrite lives in the mapping and is exact-string.**
   `build_article_payload` builds a `{media_filename → upload_path}` map from
   `article.images` and rewrites every body `<img src>` through it; pandoc's
   `src` equals `media_filename`, so this is a 1:1 lookup with no fuzzy
   matching. Targets are site-root-relative (`/images/articles/…`), keeping
   the payload domain-independent (the API normalizes `images` values to
   absolute LiveSite URLs on save — verified; body `src` values are stored as
   sent). Any body `<img>` without an uploaded match raises, so a publish
   never ships with a dead reference.

7. **Client surface: `upload_image(data, rel_path) -> dict`.**
   Composes `<base_url><base_path>/media/files`, prefixes `rel_path`
   (`articles/<YYYY>/<MM>/<slug>/<basename>`) with the `local-images` adapter,
   and returns the created item's `data` object — the same "return the API's
   JSON data" contract as the CRUD methods. The future orchestrator populates
   `Image.upload_path` from the result; the mapping only ever sees populated
   values.

8. **Sequencing: lands after `article-note-review-gate`.**
   "First lead" is only well-defined once `Article.images` is document-
   ordered (that change's D5); under today's glob order it is ambiguous. The
   note builder's `_lead_label` seam flips to the real slot label when both
   changes are in.

## Verified contract

Verified against the staging site on 2026-11-06/07 (read-only probes plus one
marked upload/article round trip per round; all probe files and test articles
removed and verified gone).

- **Base:** the Media API sits at `<base_url><base_path>` (the site's
  `/api/index.php/v1`-style prefix) and answers with the same
  `X-Joomla-Token` / `Accept: application/vnd.api+json` contract as the
  content API. (The staging reverse proxy additionally requires a Basic
  auth header — an environment detail, not part of the contract.)
- **Adapters:** `GET /media/adapters` → 200, JSON:API list; items carry
  `id` (`local-images` / `local-files`) and `attributes.path`
  (`local-images:/` …). `local-images` is the adapter rooted at the site's
  `images/` folder.
- **List:** `GET /media/files?path=local-images:/<rel>` → 200 (JSON:API
  `data[]` with `type` dir/file, `name`, adapter-prefixed `path`, `size`,
  `mime_type`, `width`/`height`, dates); absent paths 404 with the standard
  envelope. `&url=1` adds an absolute `url` to file items.
- **Upload:** `POST /media/files` with
  `{"path": "local-images:/<rel>", "content": "<base64>", "override": true}`
  → 200 with the created item; the full parent directory chain is created in
  the single call. The file's extension must be in com_media's allowed image
  extensions (default `bmp,gif,jpg,jpeg,png,webp,avif`); request size is
  checked against the component's `upload_maxsize` and the PHP limits
  (400 with an error entry when exceeded).
- **Item ops:** `GET|PATCH|DELETE /media/files/{adapter}:/<path>` (path as
  URL segment). DELETE → 204, files and folders (recursive). `?path=` is
  honored for reads only.
- **Content API `images`:** `POST /content/articles` with a flat
  `images: {image_intro, image_intro_alt, image_intro_caption, …}` → 200;
  the values persist and are exposed on read as `attributes.images`. A
  root-relative value is normalized to an absolute LiveSite URL on save.
  Contrast: `attribs` is accepted on write but absent from the read shape —
  silently dropped, unusable.

## Risks / Trade-offs

- **Media API is a 5.4-line feature** → the contract is re-probed at the
  Joomla 6 migration, same register as the joomla-client change.
- **`images` values are stored as absolute LiveSite URLs** (server-side
  normalization) → benign: the article is served by the same site.
- **"First lead" depends on the note gate's ordering** → declared dependency;
  a test asserts the first `is_lead` entry is the document-first lead, so a
  silent regression picks the wrong image, not a random one.
- **`override: true` clobbers on re-publish** → deliberate idempotency; an
  editor who hand-renames a file inside an article's folder loses it on the
  next publish (accepted — the folder is docxwire's).
- **Unreferenced extracted media are uploaded too** (they are part of
  `Article.images`) → minor storage cost; explicitly wanted so editors have
  every image at hand.
- **Real-world image sizes vs PHP limits** → surfaced as a typed 400
  `JoomlaApiError`, no retries; the operator sees it.
- **Public artifacts** → the verified contract records shapes only: no host
  names, tokens, or category IDs.

## Migration Plan

None — additive library facility, no data migration. Roll-forward order:
`article-note-review-gate` lands (document-ordered `Article.images`) → this
change lands → the future orchestration step becomes the first caller
(upload → populate `upload_path` → `build_article_payload`). Rollback is
reverting the two module changes.

## Open Questions

- The exact wording of the resolved lead label in the `Prüfe:` note once
  `_lead_label` flips — owned by `article-note-review-gate`; coordinate when
  that change closes the seam.

# Proposal

## Why

Published articles currently ship with broken image references: the converted body
points at pandoc's temporary media paths (`media/imageN.jpg`), which nothing on the
site serves, and lead images are stripped from the body with nowhere to go. The
site's Joomla 5 (5.4-line) `com_media` REST API can upload files into
`images/articles/…`, and the content API's article payload accepts an `images`
object for the intro/fulltext images — both verified against the staging site.
This change adds the upload and the referencing correction so articles publish
with working imagery.

## What Changes

- `JoomlaClient` gains a media upload method: `POST /media/files` with a JSON body
  (adapter-prefixed `path`, base64 `content`, `override`) against the site's Media
  API; a single call creates the full directory chain.
- `build_article_payload` rewrites in-body `<img src>` references to the uploaded
  location (site-root-relative `/images/articles/<YYYY>/<MM>/<slug>/<basename>`),
  driven by the `Image.upload_path` values the publishing flow populates after
  uploading.
- The first lead image in document order is emitted in the payload's `images`
  object as both `image_intro` (blog/listing layout) and `image_fulltext`
  (article page), carrying its caption; secondary lead images are uploaded but
  not referenced.
- All of the article's images are always uploaded, so an editor can switch the
  lead to a secondary image in the admin afterwards (the caption would then need
  re-entering there — accepted trade-off).
- Publishing fails loudly when a body image has no corresponding upload (no
  partial publishes with dead references).
- Depends on `article-note-review-gate` (document-ordered `Article.images`) and
  resolves that change's `_lead_label` seam by defining the lead-slot assignment.

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

- `joomla-client`: a new requirement for media upload (endpoint, request shape,
  success/failure envelope); the payload requirements change so that body image
  references are rewritten to the uploaded locations and the lead image is
  carried in the `images` object.

## Impact

- `src/docxwire/joomla/client.py`: upload method plus the media endpoint constant.
- `src/docxwire/joomla/mapping.py`: image-aware payload building (reference
  rewrite, `images` object).
- `tests/joomla/test_client.py`, `tests/joomla/test_mapping.py`.
- No site-side changes (core Media API of the 5.4-line Joomla) and no new Python
  dependency.
- Sequencing: lands after `article-note-review-gate` (it consumes that change's
  document-ordered `Article.images` and closes its `_lead_label` seam).
- Out of scope: image compression/optimization; publishing orchestration/CLI
  (the client is a library; a future step drives it); prioritization among
  secondary lead images; the `introtext`/`fulltext` read-more split.

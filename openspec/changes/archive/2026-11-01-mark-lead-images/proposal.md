# Proposal

## Why

Articles converted from `.docx` currently keep any images that sit above the title inside the article body, and no image is distinguished as a "lead" image. Downstream publishing therefore has no way to tell a hero/lead image apart from in-body images. The converter needs to pull leading (pre-heading) images out of the body and flag them so they can be treated as lead imagery.

## What Changes

- During `.docx` conversion, detect image blocks (`<img>`) that appear in the document body **before the first heading**.
- Remove those leading images from the article body.
- Mark the corresponding extracted-media `Image` objects with `is_lead=True`.
- Images that do not appear before the first heading remain in the body and keep `is_lead=False`.
- A leading image that cannot be matched to an extracted local media file is an **internal error** and fails the conversion (pandoc extracts every pipeline image — including Word "Online Pictures" — to a local file, so this should not occur in normal operation).

**Out of scope (separate feature):** the no-heading case — a document with no heading that starts with an image treating that image as the lead and flagging the article via `Article.note`. This change only handles documents that have a first heading; with no heading, no image is treated as lead. An image nested **inside** the first heading is also out of scope (it should be an error, but is not part of the current test data and is handled separately).

## Capabilities

### New Capabilities
- `article-images`: How the converter treats images during article conversion — separating leading (pre-heading) images from in-body images and flagging lead images with `is_lead`.

### Modified Capabilities
<!-- No existing specs; nothing to modify. -->

## Impact

- **Affected code:** `src/docxwire/converter/docx.py` (`DocxConverter.convert`). The `Image.is_lead` field already exists in `src/docxwire/converter/base.py`, so no data-model change is required.
- **Behavior:** `Article.body` will no longer contain pre-heading images; `Article.images` will carry `is_lead=True` on the matching images. A lead image with no matching local media file now fails conversion (internal error).
- **Tests:** `tests/converter/test_docx.py`. Test data uses real `.docx` fixtures in `tests/data/` — `Ruderkurs` (single lead), `Lichterfest` (multiple lead), `Heineken` (in-body), `Abrudern` (no image in front) — the two new ones sanitized (PII stripped, `thumbnail` dropped, media compressed) before tracking; the no-heading and unmatched-lead cases use `pypandoc` mocks.
- **No** API or dependency changes.

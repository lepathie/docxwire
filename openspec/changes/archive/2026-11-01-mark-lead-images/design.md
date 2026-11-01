# Design

## Context

`DocxConverter.convert` (`src/docxwire/converter/docx.py`) converts a `.docx` to HTML via pypandoc (`--extract-media`), parses it with BeautifulSoup, extracts the first `h1`–`h6` as the title and `decompose()`s it, then builds the `Article` with `body=str(soup)` and an `images` list populated by globbing the extracted media directory. The `Image` dataclass (`src/docxwire/converter/base.py`) already carries an `is_lead: bool = False` field that is never currently set. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Identify `<img>` elements that appear in the parsed body before the first heading.
- Remove those elements from the body.
- Set `is_lead=True` on the corresponding extracted-media `Image` entries.

**Non-Goals:**
- No change to the `Image`/`Article` data model (the `is_lead` field already exists).
- No change to how non-leading (in-body) images are handled.
- No handling of image captions/alt text (out of scope for this change).
- No change to the docx→HTML conversion pipeline (pypandoc invocation).
- The no-heading case (a document with no heading that starts with an image → lead, flagged via `Article.note`) is a **separate feature/change** and is not implemented here.

## Decisions

**Anchor lead detection on the first heading, using document order.**
Walk the parsed soup in document order (`soup.find_all(True)`) and stop at the first heading. Any `<img>` encountered before that point is a lead image. This correctly handles nested structures (e.g. an image wrapped in a `<p>` or `<div>` before the heading) because it relies on document order rather than sibling position. An `<img>` nested *inside* the heading is **out of scope** for this change (it should be an error, but is not part of the current test data); the document-order walk simply does not classify it as a lead.
- *Alternative considered:* Inspecting the heading's preceding siblings. Rejected — fragile when the heading or images are nested in container elements.

**Collect lead sources first, then flag matching images.**
Before `decompose()`ing the lead `<img>` elements, record each one's `src`. After the body is finalized and the `images` list is built from the media directory, set `is_lead=True` on each `Image` whose `media_filename` matches a recorded lead source.
- *Alternative considered:* Flagging images during the media-dir glob by re-scanning the body. Rejected — the lead `<img>` elements are removed from the body, so they would no longer be available to match against; capturing sources up front is simpler and order-independent.

**Match lead `<img src>` to `Image.media_filename` by filename.**
pypandoc's `--extract-media` writes each extracted image to the media directory and references it from the HTML `src` using the file's name. `Image.media_filename` is the path relative to the media dir. Matching on the source filename (last path component) is robust to a leading directory segment in either form.

**An unmatched lead image is an internal error.**
If a detected lead `<img>` has no matching extracted local media file, `convert` raises an error (wrapped in the existing `RuntimeError`). Rationale: pandoc extracts every pipeline image — including Word "Online Pictures" — to a local file, so a missing match signals a pipeline/internal fault rather than a benign external URL.
- *Alternative considered:* Silently skip the unmatched lead image. Rejected — it would hide a real fault and drop content silently.

**Test data reuses real, sanitized fixtures.**
Cases map to `.docx` fixtures in `tests/data/`: single-lead → `Ruderkurs`; multiple-lead → `Lichterfest` (2 pre-heading); in-body + mixed → `Heineken` (1 pre-heading + 5 in-body); no-lead / no image in front → `Abrudern` (2 in-body, none pre-heading). The two new fixtures (`Abrudern`, `Lichterfest`) arrive unsanitized and oversized, so the first implementation step strips PII from `docProps/*` and `customXml/item*.xml`, drops `docProps/thumbnail.*`, and compresses `word/media/*` (Lichterfest's `image3.jpg` is ~39.6 MB) without changing the before/after-heading image counts. The no-heading and unmatched-lead cases use `pypandoc` mocks.

## Risks / Trade-offs

- [A `src` / `media_filename` mismatch due to path normalization would cause a spurious "unmatched lead image" error] → Mitigated by matching on the filename (basename) rather than the full relative path, so only a genuinely missing file triggers the error.
- [Behavior change for existing articles] → Pre-heading images that were previously in the body are now removed and flagged; this is the intended behavior change and the point of the change.

## Migration Plan

None required. No data-model, API, or dependency changes; the change is confined to `DocxConverter.convert`. Converted output for documents without pre-heading images is unchanged.

## Open Questions

None.

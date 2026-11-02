# Proposal

## Why

Article image captions are currently lost or mangled by the converter. In the source documents, a caption is the line of text directly below an image, usually formatted with the custom `Bildunterschrift` paragraph style (the Word native caption feature is not used). Today the converter (a) leaves the lead image's caption line orphaned in the body after removing the image, (b) leaves in-body caption lines as plain unstyled paragraphs, and (c) never populates `Image.caption` — so downstream publishing has no access to the captions.

## What Changes

- During `.docx` conversion, detect each image's caption: the text line directly below the image (the next block in document order). The `Bildunterschrift` style is the usual marker, but detection is positional and does NOT require the style, so authoring mistakes (caption line missing the style) are captured too.
- **Lead (pre-heading) images:** the caption line is **cut from the article body** and its text is **captured** into `Image.caption`. The lead image removal now also clears the image's paragraph wrapper, so no empty `<p>` or orphaned caption survives in the body.
- **In-body (after-heading) images:** the image plus its caption line are **rewritten in the body as `<figure>` + `<figcaption>`**, and the caption text is additionally captured into `Image.caption`.
- **Guessing is flagged for review:** when a captured caption line lacks the `Bildunterschrift` style (the converter is guessing — including body text written directly under an image), a concise line is added to `Article.note` naming the affected images by media filename. Styled captions add no note.
- Images with no caption line below them are left unchanged: `Image.caption` stays empty and the body markup is untouched.
- **BREAKING** (behavioral): `Article.body` of converted articles changes — lead caption lines disappear from the body, and in-body image+caption pairs become `<figure>`/`<figcaption>` markup. `Article.images[*].caption` is now populated.

## Capabilities

### New Capabilities

<!-- None: this change extends the existing article-images capability. -->

### Modified Capabilities

- `article-images`: leading-image removal now includes the image's caption line; in-body images with a caption line are rewritten as `<figure>`/`<figcaption>` in the body; a new requirement captures the caption text into `Image.caption`. (Baseline: the main spec at `openspec/specs/article-images/spec.md`, synced when `mark-lead-images` was archived.)

## Impact

- **Affected code:** `src/docxwire/converter/docx.py` (`DocxConverter.convert` — caption detection, lead removal, in-body figure rewrite, caption capture). The `Image.caption` field already exists in `src/docxwire/converter/base.py`; no data-model change.
- **Behavior:** `Article.body` no longer contains orphaned lead caption lines or empty image paragraphs; in-body image+caption pairs become `<figure>`/`<figcaption>`; `Article.images[*].caption` carries the caption text (matched to extracted media by filename, same convention as lead flagging); `Article.note` gains a concise line (no line breaks, no caption text) naming images whose caption was guessed.
- **Tests:** `tests/converter/test_docx.py`. All four existing real `.docx` fixtures contain `Bildunterschrift` caption lines under every image (verified against pandoc output), so they exercise the real path; `pypandoc`-mocked tests cover the no-style (authoring mistake) and no-caption cases.
- **Archive ordering:** `mark-lead-images` must be archived (syncing `openspec/specs/article-images/spec.md`) before this change is archived, since this delta modifies its requirements.
- **No** API or dependency changes.

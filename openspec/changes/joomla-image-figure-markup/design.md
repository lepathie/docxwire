# Design

## Context

`DocxConverter.convert` (src/docxwire/converter/docx.py) runs pandoc with `--extract-media`, then post-processes the HTML with BeautifulSoup. The in-body image pass (the `for img in soup.find_all("img")` loop) currently rewrites only images that have a caption line directly below them into a plain `<figure>` + `<figcaption>`; caption-less in-body images are left as bare `<img>` tags (typically inside a `<p>`), and shared blocks (several `<img>` in one block) are skipped entirely. Lead images were already decomposed from the body in the earlier pass, so they are not seen by this loop.

The site's editor convention (see proposal.md) requires every in-body image to be a `<figure class="image align-center">` with an `<img loading="lazy">` that carries no other styling.

## Goals / Non-Goals

**Goals:**

- One in-body image pass that wraps every in-body image in a `figure` carrying `class="image align-center"`.
- Every in-body `<img>` ends up with exactly `src` + `loading="lazy"` (no `class`/`style`/`width`/`height`).
- Caption handling (figcaption creation, caption capture, guess flagging) is unchanged in semantics.

**Non-Goals:**

- No change to lead-image handling, media extraction, the `Image`/`Article` data model, or the publishing side.
- No changes to pandoc invocation or to how captions are detected.

## Decisions

**D1: Unify the in-body pass so every processable image is wrapped.**
The loop restructures around the top-level block of each image. For a block containing a single image, the existing caption detection (`_next_block_sibling` + `_is_caption_candidate`) decides whether a `figcaption` is appended; the figure is created in both cases. For a block containing several images, the block is replaced by one figure per image, in document order, without figcaptions. Rationale: the spec's "every in-body image SHALL be wrapped" admits no exceptions, and the split is a small, lossless transformation (a paragraph with two inline images becomes two centered figures, which is the site's intended look). Alternative considered: keep skipping shared blocks — rejected because it would leave bare `<img>` tags in the body.

**D2: Caption-less shared blocks get no caption attribution.**
A caption line following a shared block stays in the body as a plain paragraph (current behavior). Per-image caption attribution inside one block is ambiguous, so no `figcaption` is created there and no `captions` entry is recorded. This matches today's behavior for shared blocks.

**D3: Attribute cleanup order — strip first, then set `loading`.**
After extracting the `<img>` into its figure, pop `class`, `style`, `width`, `height` from `img.attrs`, then set `img["loading"] = "lazy"`. The figure gets `class=["image", "align-center"]` (rendered as `class="image align-center"`). Doing the strip before the set guarantees the final attribute set is exactly `src` + `loading` regardless of what the source markup contained.

**D4: Source-less images are wrapped too.**
The current `if not img_src: continue` guard is narrowed: a missing `src` no longer skips wrapping — it only skips the `captions` lookup (which needs a filename to match). A `figure` wrapping a source-less `img` is still conformant; with `--extract-media`, pandoc always emits a `src`, so this is defensive consistency, not a behavior users will see.

**D5: Figure class as a module constant.**
The class pair is a site convention that may evolve; it lives in one module-level constant (e.g. `_FIGURE_CLASSES`) next to the existing `_CAPTION_STYLE` constant, not inline in the loop.

**Why this is safe for the rest of the pipeline:** the lead pass runs first and removes lead image blocks, so "lead images are not wrapped" holds structurally; `_flag_lead_images` and `_apply_image_captions` operate on the image list (keyed by media filename), which the figure rewrite does not alter.

## Risks / Trade-offs

- [Shared-block split changes markup that was previously untouched] → rare in club submissions (multiple images in one paragraph); covered by a dedicated test; the resulting centered figure stack is the site's intended rendering.
- [Attribute stripping removes styling that a future pandoc version might emit deliberately] → intentional: the site convention puts all image styling on the `figure` class; `img` must stay clean.
- [Existing test `test_inbody_image_without_caption_line_stays_unchanged` asserts the old bare-`<img>` behavior] → rewritten as part of this change to assert the new figure/lazy behavior, including its edge cases (heading next, document end, empty next paragraph, shared block, source-less image).

## Migration Plan

None. The change affects conversion output only; no stored data, no schema, no API. Rollback is reverting the converter change.

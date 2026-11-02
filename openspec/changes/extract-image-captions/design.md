# Design

## Context

`DocxConverter.convert` (`src/docxwire/converter/docx.py`) converts `.docx` → HTML via pypandoc (`docx+styles`, `--extract-media`), parses with BeautifulSoup, lifts the first heading into the title, removes pre-heading `<img>` elements (recording their `src` for `is_lead` flagging via `_flag_lead_images`), and builds `Article` with `body=str(soup)` plus `Image` entries globbed from the extracted media dir. `Image.caption` exists in `src/docxwire/converter/base.py` but is never populated. See proposal.md for motivation.

Observed pandoc markup for these documents (verified against all four `tests/data/` fixtures): every image is a top-level `<p><img src="…/media/imageN.ext" …/></p>`, and a caption is the **next top-level block**: `<div data-custom-style="Bildunterschrift"><p>caption text</p></div>`. The Word native caption feature (which would yield `<figure>`/`<figcaption>`) is not used. Today the converter `decompose()`s only the `<img>`, leaving an empty `<p></p>` and an orphaned caption line in the body.

## Goals / Non-Goals

**Goals:**
- Detect each image's caption positionally: the next top-level block in document order after the image's block, when it is a non-heading text paragraph. The `Bildunterschrift` style is the usual marker but is NOT required (authoring mistakes must still be captured).
- Lead images: cut the image's block **and** its caption line from the body (no empty `<p>`, no orphaned caption); capture the caption text.
- In-body images: rewrite image block + caption line into `<figure>` (containing the `<img>`) + `<figcaption>` (containing the caption text) in the body; capture the caption text.
- Populate `Image.caption` for both lead and in-body images, matched to extracted media by filename (same convention as lead flagging).
- Flag guessed captions (caption line without the `Bildunterschrift` style) in `Article.note` as a single concise line naming the affected images, for the human reviewer's final check.

**Non-Goals:**
- No data-model change (`Image.caption` already exists).
- No `Image.alt` population (pandoc sets `alt` from the Word image description; out of scope).
- No change to the pypandoc invocation, title extraction, slug, or lead-flagging/error behavior.
- No handling of the no-heading "image at top → lead" case (separate feature, per `mark-lead-images`).
- No re-styling of `data-custom-style` attributes on non-caption paragraphs (pre-existing, out of scope).

## Decisions

**Caption = next top-level block, classified by a shared "caption candidate" predicate.**
For an `<img>`, walk up to its top-level block (direct child of the document root — in these documents the wrapping `<p>`). Its `next_sibling` is a caption candidate iff it is a Tag, not a heading (`h1`–`h6`), contains no `<img>`, has non-empty text, and is paragraph-shaped (`<p>`, or a `<div>` wrapping a `<p>` — the shape pandoc emits for styled lines). Anything else (heading, image block, table, empty) → the image has no caption.
- *Alternative considered:* Require `data-custom-style="Bildunterschrift"`. Rejected — the user confirmed authors sometimes miss the style and those captions must still be captured; the style is used by nothing, so making it mandatory would lose data.
- *Alternative considered:* Next *paragraph* anywhere (skipping non-text blocks). Rejected — "the line directly below" is the definition; skipping blocks would capture text that is not directly below the image.

**Lead removal decomposes the image's top-level block, not the bare `<img>`.**
The existing document-order walk (stop at first heading) is kept; when it meets an attached `<img>`, it now resolves the image's top-level block and decomposes that block (plus the caption-candidate sibling, if present) instead of the bare `<img>`. This removes the empty-`<p>` shell as a side benefit. The walk gains a guard: skip elements that are no longer attached (`el.parent is None`) so that children of an already-decomposed block are not reprocessed.
- *Alternative considered:* Rewrite the walk over top-level blocks only (`soup.find_all(recursive=False)`). Rejected — the proven all-elements walk also handles nested placements; only the decompose target and the sibling check change.

**In-body rewrite is a local block replacement, done after heading removal.**
For each remaining attached `<img>` (document order): if its top-level block's next sibling is a caption candidate, build `<figure>` with `soup.new_tag`, move the `<img>` into it (extract from the `<p>`), append a `<figcaption>` holding the stripped caption text, replace the image block with the figure, and `decompose()` the caption block. No caption candidate → block left untouched.
- *Alternative considered:* String-level regex rewriting of the final HTML. Rejected — the codebase works in the DOM throughout; a DOM replacement keeps one representation.

**Captions are matched to `Image` entries by filename, in one dict.**
Both passes (lead cut, in-body rewrite) record `src → caption text`; the basenames (last path component) key a dict that is applied after the media glob, in a sibling helper next to `_flag_lead_images` (e.g. `_apply_image_captions`), setting `image.caption` where the basename matches.
- *Alternative considered:* Extend `_flag_lead_images` to also take captions. Rejected — it is lead-specific (ordered list + unmatched error); caption matching is image-set-wide and must not affect the lead error path. Basename-keying is safe even if a filename were ever reused: the invariant is that the same image always carries the same caption.

**Guessed captions are flagged in `Article.note` as one concise line.**
Every captured caption line lacking the `Bildunterschrift` style marks a guess (it may be body text written directly under an image). All guessed images are flagged with a single short note line naming them by media filename — no caption text, no per-image lines, no line breaks: the note field stays terse, and richer internal organization of flagged issues is explicitly out of scope for this change.
- *Alternative considered:* one note line per image, including the caption text. Rejected — verbose; long texts and line breaks do not belong in the note.
- *Alternative considered:* a structured `warnings: list[str]` field on `Article`. Rejected — `Article.note` already exists as the free-form review note, and a data-model change is not wanted.

**Caption text is the block's stripped text content.**
`get_text()` of the caption block, `.strip()`ed. Observed captions are plain single-paragraph text; no HTML is preserved inside `<figcaption>`.
- *Alternative considered:* Preserving inner markup of the caption line. Rejected — no fixture contains markup in a caption; plain text keeps the published `<figcaption>` simple.

## Risks / Trade-offs

- [An author who writes body text directly under an image (no caption line) has that line captured as the caption — and for a lead image, cut from the body] → This is the definition the user confirmed ("the caption is the line of text directly below an image"); in practice the pre-heading region of these documents contains only images and their captions, and in-body lines are relocated (into `<figcaption>`), not lost — and the guess is flagged concisely in `Article.note` (missing `Bildunterschrift` style) so a human reviewer gives it a final check.
- [The same media filename is referenced by two images] → Cannot happen in practice: pandoc names extracted media `image1`, `image2`, …, one unique name per image. Even if it did, the invariant that the same image always carries the same caption means both `Image` entries are meant to hold the same caption — exactly what basename-keyed last-write-wins yields, so the matching stays safe.
- [Body markup changes more than before (empty `<p>`s removed, figures introduced)] → Intended behavior change; existing fixture-based tests are updated to assert the new body shape.
- [Unobserved markup variants (image not in a top-level `<p>`, caption deeper-nested)] → The walk-up to the top-level block plus the shape-restricted caption predicate degrades safely: unrecognized shapes simply yield "no caption" (image kept/removed as before, no content lost).

## Migration Plan

None required. No data-model, API, or dependency changes; confined to `DocxConverter.convert` and its tests. Rollback is a code revert. Converted output for documents without caption lines is byte-identical to today except for the empty-`<p>` cleanup on lead images.

## Open Questions

None. (The in-body representation — `<figure>`/`<figcaption>` rewrite vs. keep-as-is — was confirmed with the user during planning.)

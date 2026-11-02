# Proposal

## Why

The club's Joomla 5 website (Clubnachrichten blog) renders article images through a fixed set of editor conventions: every image is wrapped in `<figure class="image align-center">` and each `<img>` carries `loading="lazy"` with no other styling. DOCxWIRE's converted bodies currently do not follow these conventions — in-body images with a caption become a plain `<figure>` (no class), and in-body images without a caption stay as bare `<img>` tags — so published articles need manual markup fixes to match the established blog styling.

## What Changes

- Every in-body image in the converted article body is wrapped in a `<figure>` element carrying `class="image align-center"`, including images without a caption (which today remain bare `<img>` tags).
- Every in-body `<img>` element carries `loading="lazy"`.
- In-body `<img>` elements carry no other styling: any `class`, `style`, `width`, or `height` attributes present in the source markup are stripped, leaving only `src` and `loading="lazy"`.
- Lead images are unaffected: they are removed from the body and published as separate lead images, so no figure wrapping applies to them.

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

- `article-images`: the "In-body images are preserved" requirement changes so that caption-less in-body images also become figures; a new requirement mandates the Joomla-conformant figure class and clean `<img>` attributes for all in-body images.

## Impact

- `src/docxwire/converter/docx.py`: the in-body figure-rewriting pass must add the `image align-center` class, set `loading="lazy"`, strip styling attributes, and extend figure wrapping to caption-less in-body images.
- `tests/converter/test_docx.py`: existing figure assertions extend to the class/lazy/loading expectations; new tests cover caption-less in-body images and attribute stripping.
- No changes to the `Article`/`Image` data model, the publishing side, or media extraction.

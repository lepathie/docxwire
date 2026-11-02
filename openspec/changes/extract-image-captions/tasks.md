# Tasks

## 1. Tests for caption capture (red)

Test names follow `test_<scenario>_<expected_result>` (see `tests/AGENTS.md`). All four existing fixtures contain `Bildunterschrift` caption lines under every image (verified against pandoc output), so the fixture tests use the real caption texts; mock-based tests cover the no-style and no-caption cases.

- [x] 1.1 Using the `Ruderkurs` fixture (1 lead image with caption), assert the lead `Image.caption` equals `"Unter Anleitung geht es für die Teilnehmenden das erste Mal aufs Water"`-style real text (read from the fixture's caption line), the caption text no longer appears in `Article.body`, and no empty `<p>` element remains in the body. Verify: fails before implementation (caption empty, caption line + empty `<p>` present in body).
- [x] 1.2 Using the `Lichterfest` fixture (2 lead images with captions), assert both `Image` entries carry their caption texts and no caption line or empty `<p>` remains in the body. Verify: fails before implementation (red).
- [x] 1.3 Using the `Heineken` fixture (1 lead + 5 in-body, all captioned), assert: the lead caption is captured and cut from the body; each in-body image is wrapped in a `<figure>` whose `<figcaption>` carries the caption text; no `Bildunterschrift`-styled block remains in the body; all 6 `Image` entries have non-empty `caption`. Verify: fails before implementation (red).
- [x] 1.4 Using the `Abrudern` fixture (2 in-body images with captions), assert both in-body images become `<figure>`/`<figcaption>` in the body, both `Image` entries carry the caption texts, and no image is marked lead. Verify: fails before implementation (red).
- [x] 1.5 (mock, authoring mistake) Mock `pypandoc.convert_file` to return a pre-heading `<p><img src='media/x.jpg'></p>` followed by a plain `<p>` caption line (no `Bildunterschrift` style) and a heading; assert the caption is captured into `Image.caption` and the caption line is cut from the body. Verify: fails before implementation (red).
- [x] 1.6 (mock, no caption) Mock `pypandoc.convert_file` so an in-body image's next block is a heading (e.g. `<h1>T</h1><p><img src='media/x.jpg'></p><h2>Next</h2>`); assert the image's `caption` stays empty and the image stays in the body in its original markup (no figure wrapper). Verify: passes both before and after (regression guard against over-capturing).
- [x] 1.7 (mock, in-body, authoring mistake) Mock `pypandoc.convert_file` to return a heading, then `<p><img src='media/x.jpg'></p>` followed by a plain unstyled `<p>` caption line and a body paragraph; assert the image is rewritten as `<figure>`/`<figcaption>` in the body and the caption is captured. Verify: fails before implementation (red).
- [x] 1.8 (mock, guessed caption) Mock `pypandoc.convert_file` so an in-body image is followed by a plain unstyled `<p>` caption line; assert `Article.note` is a single concise line naming the image by its media filename, contains no line breaks, and does not contain the caption text. Verify: fails before implementation (red).
- [x] 1.9 (fixture, no guesses) Using the `Ruderkurs` fixture (its caption line carries the `Bildunterschrift` style), assert `Article.note` is empty. Verify: passes both before and after (regression guard against over-flagging).

## 2. Implementation in `DocxConverter` (green)

- [x] 2.1 Add the shared "caption candidate" predicate from design.md: the next top-level sibling block of an image's top-level block is a caption iff it is a Tag, not a heading, contains no `<img>`, has non-empty text, and is paragraph-shaped (`<p>` or `<div>` wrapping a `<p>`). Verify: module imports cleanly and the predicate is used by both passes below.
- [x] 2.2 Extend the pre-heading lead walk: when it meets an attached `<img>`, resolve its top-level block, record the `src` and the caption-candidate sibling's stripped text, and decompose the top-level block plus the caption sibling (instead of the bare `<img>`); guard the walk against detached elements (`el.parent is None`). Verify: 1.1, 1.2, and 1.5 pass (green).
- [x] 2.3 Add the in-body figure rewrite (after heading removal): for each remaining attached `<img>` whose top-level block has a caption-candidate next sibling, replace the image block with a `<figure>` containing the `<img>` and a `<figcaption>` with the stripped caption text, and decompose the caption block; leave the block untouched when there is no caption candidate. Verify: 1.3, 1.4, and 1.7 pass (green); 1.6 still passes.
- [x] 2.4 Apply captured captions to `Image` entries: collect `src → caption text` from both passes, and after the media glob set `image.caption` on each `Image` whose `media_filename` basename matches (sibling helper next to `_flag_lead_images`, without touching the lead error path). Verify: the `caption` assertions in 1.1–1.5 and 1.7 pass (green).
- [x] 2.5 Flag guessed captions: when a captured caption line lacks the `Bildunterschrift` style, add one concise line to `Article.note` naming all such images by media filename (no caption text, no line breaks; the note stays empty when nothing is guessed). Verify: 1.8 passes (green) and 1.9 stays green.

## 3. Verification

- [x] 3.1 Run the project checks (`make check`: ty, ruff check, ruff format, pymarkdown) and the full test suite (`make test`). Verify: all tests pass and the linters are clean.

## Workflow follow-up

- Archive this change once the project's review requirements are met (`openspec archive extract-image-captions`) and verify `openspec/specs/article-images/spec.md` reflects the new caption requirements.

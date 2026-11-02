# Tasks

## 1. Failing tests for the new in-body image markup

- [ ] 1.1 Rewrite `test_inbody_image_without_caption_line_stays_unchanged` in `tests/converter/test_docx.py` to assert the new behavior: every image in the mocked in-body markup (heading-adjacent, document end, empty-paragraph-adjacent, source-less) is wrapped in a `figure` with `class="image align-center"` and its `img` carries `loading="lazy"`; verify with `pytest tests/converter/test_docx.py -k without_caption` (fails before implementation)
- [ ] 1.2 Add a mock-based test that an in-body image without a caption line becomes a `figure` (no `figcaption`) with `class="image align-center"` and `img[loading="lazy"]`, keeping its `src`; verify with `pytest tests/converter/test_docx.py -k captionless` (fails before implementation)
- [ ] 1.3 Add a mock-based test that `class`, `style`, `width`, and `height` attributes on a source `img` are stripped, leaving exactly `src` and `loading="lazy"`; verify with `pytest tests/converter/test_docx.py -k stripping` (fails before implementation)
- [ ] 1.4 Add a mock-based test that a shared block with two images is replaced by two `figure` elements, one per image, each with `class="image align-center"` and `img[loading="lazy"]`, and no `figcaption`; verify with `pytest tests/converter/test_docx.py -k shared_block` (fails before implementation)
- [ ] 1.5 Extend the real-fixture assertions in `test_inbody_images_become_figures_with_captions` (heineken) and `test_inbody_images_become_figures_and_no_image_marked_lead` (abrudern) to assert `figure` class `["image", "align-center"]` and `img[loading="lazy"]` for every in-body image; verify with `pytest tests/converter/test_docx.py -k figures` (fails before implementation)

## 2. Implementation

- [ ] 2.1 Add a module-level `_FIGURE_CLASSES` constant (`("image", "align-center")`) in `src/docxwire/converter/docx.py` next to `_CAPTION_STYLE`; verify with `ruff check src/docxwire/converter/docx.py`
- [ ] 2.2 Rework the in-body image loop in `DocxConverter.convert` per design D1–D4: wrap every processable in-body image in a `figure` carrying `_FIGURE_CLASSES` (with `figcaption` only when a caption candidate exists), split shared blocks into one figure per image in document order, strip `class`/`style`/`width`/`height` from each `img` before setting `loading="lazy"`, and let source-less images be wrapped while skipping only the caption lookup; verify with `pytest tests/converter/test_docx.py` (all tests from group 1 pass)
- [ ] 2.3 Run `pytest` for the full suite and verify no regressions (in particular the lead-image, caption-capture, and note-flagging tests)

## 3. Verification

- [ ] 3.1 Run `make ci` and verify lint, type check, and the test suite at 100% coverage all pass

# Tasks

## 1. Test data & fixtures

- [x] 1.1 Add the `2026.03 Heineken Regatta Amsterdam.docx` fixture to `tests/data/` and register it in `tests/conftest.py`. Verify: the file exists under `tests/data/` and the new fixture resolves (a trivial test using it passes).
- [x] 1.2 Anonymize `2026.10 Abrudern.docx` **in place** (preserve data, anonymize PII — do not nuke): keep the original body text but replace person names with consistent pseudonyms; anonymize name fields in `docProps/` while preserving non-PII metadata (e.g. `dc:title`); downscale `word/media/*` to extreme low-res/low-quality **preserving each file's format** (JPEG→JPEG, PNG→PNG) so images stay displayable; keep the package valid (opens in Word without repair) — **without changing** the number of images before/after the heading. Verify: opens in Word cleanly, images display, no person names remain in body/metadata, title preserved, 0 before / 2 after the heading.
- [x] 1.3 Anonymize `2025.07 Heilbronner Lichterfest 2025.docx` **in place** with the same approach as 1.2 (anonymize names in the body + `docProps/`, preserve non-PII metadata, extreme low-res/low-quality images preserving format, valid package) — its `word/media/image3.jpg` (the large one) is downscaled like the rest. Verify: opens in Word cleanly, images display, no person names remain, title preserved, 2 before / 0 after the heading.
- [x] 1.4 Register the `Abrudern` and `Lichterfest` fixtures in `tests/conftest.py`. Verify: the fixtures resolve (a trivial test using each passes).

## 2. Tests for lead-image behavior (red)

Test names follow `test_<scenario>_<expected_result>` (see `tests/AGENTS.md`).

- [x] 2.1 Using the existing `2025.04 Ruderkurs` fixture (1 pre-heading image), assert the image is removed from `Article.body` and its `Article.images` entry has `is_lead=True`. Verify: fails before implementation (image currently kept in body, `is_lead` `False`).
- [x] 2.2 Using the `Lichterfest` fixture (2 pre-heading images), assert **all** pre-heading images are removed from the body and **all** are flagged `is_lead=True`. Verify: fails before implementation (red).
- [x] 2.3 Using the `Heineken` fixture (1 pre-heading + 5 in-body), assert the in-body images remain in `Article.body` with `is_lead=False` while the single pre-heading image is flagged `is_lead=True`. Verify: the in-body-stays assertions pass before and after; the flag assertions fail before implementation.
- [x] 2.4 Using the `Abrudern` fixture (no pre-heading image, 2 in-body), assert **no** image is marked `is_lead` and both in-body images remain in `Article.body` with `is_lead=False`. Verify: passes both before and after (regression guard against over-flagging).
- [x] 2.5 (no heading) Mock `pypandoc.convert_file` to return heading-less HTML and assert no image is treated as lead. The no-heading "starts with an image → lead" behavior is a **separate feature** and is not implemented here. Verify: passes both before and after.
- [x] 2.6 (unmatched lead) Mock `pypandoc.convert_file` to return a pre-heading `<img>` whose `src` matches no extracted media file and assert `convert` raises `RuntimeError`. Verify: fails before (no error today), passes once the check is added.

## 3. Implementation in `DocxConverter` (green)

- [x] 3.1 In `DocxConverter.convert`, detect leading `<img>` elements (those in document order before the first heading), record their `src`, and `decompose()` them from the parsed soup before the body string is built. Verify: the 2.1 / 2.2 / 2.3 body-removal assertions pass (green).
- [x] 3.2 When building the `images` list, set `is_lead=True` on each `Image` whose `media_filename` matches a recorded lead `src` (match by filename). Verify: the 2.1 / 2.2 / 2.3 `is_lead=True` assertions pass (green).
- [x] 3.3 Confirm non-leading images are left untouched (remain in body, `is_lead` stays `False`). Verify: the 2.3 and 2.4 tests pass.
- [x] 3.4 When matching recorded lead `src`s to extracted media, if a lead `src` matches no local media file, raise an internal error (wrapped in the existing `RuntimeError`). Verify: the 2.6 test passes (green).

## 4. Verification

- [x] 4.1 Run the converter test suite (`pytest tests/converter/`) and the project linter. Verify: all tests pass and the linter is clean.

## Workflow follow-up

- Archive the change once the project's review requirements are met (`openspec archive mark-lead-images`), then verify the archived result and that `openspec/specs/article-images/spec.md` is created.

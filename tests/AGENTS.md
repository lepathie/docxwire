# Test Conventions

Conventions for the test suite: layout, naming, and test-data hygiene.

## Structure

- **Structure**: Tests in separate `./<package>/test_<file>.py` mirroring the `../src/<root_package>/<package>/<file>.py`  structure.

## Conventions

- **Naming**: Test names should convey the outcome expected, the condition, and the scenario for which a unit is responsible → `test_[scenario]_[expected_result]` (e.g. `def test_checkout_with_invalid_coupon_displays_validation_error():`)

## Test Data

Follow [motivation](../MOTIVATION.md), support **user input of different quality**.

- **Realism**: Static test data resembling real input → `./data`. You MAY ask the author to provide documents that cover new edge-cases.
- **Sanitize**: No PII must be included in tracked files (e.g. `*.docx`). Anonymize, do not nuke:
  - ALWAYS sanitize author-provided documents.
  - Keep the original content (body text, non-PII metadata such as the title); replace PII only.
  - Person names → truncated pseudonyms (first name + last-name initial: `Max Mustermann` → `Max M.`), consistent per person.
  - Metadata name fields → neutral values (`Test-Autor`, `Test-Pipeline`).
  - PII can sit in any part — body (`word/document.xml`), `docProps/*`, `customXml/item*.xml`; names may be split across text runs (replace at paragraph level).
- **Compress**: Compress to the lowest possible quality/level supporting the test case.
  - Images → extreme low-res/low-quality variant of the original, preserving each file's format (JPEG→JPEG, PNG→PNG). Never placeholder images.
  - When dropping parts (e.g. `docProps/thumbnail.*`), also remove their references in `[Content_Types].xml` and `_rels/.rels`.
- **Verify**: The sanitized file must stay a valid package — opens in Word without repair (zip integrity, all XML parts well-formed, images open in their expected format) — and the document structure the tests rely on (e.g. number of images before/after the heading) must be unchanged.
- **Reuse**: Global fixtures → `./conftest.py`.

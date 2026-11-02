# Tasks

## 1. Creation date from core properties

- [x] 1.1 Add a failing test in `tests/converter/test_docx.py` asserting `DocxConverter().convert(ruderkurs_doc).created_date == "2025-04-26 17:52:00"`. Verify: `pytest tests/converter/test_docx.py -k created_date` fails (red).
- [x] 1.2 Implement a private helper in `docx.py` (stdlib `zipfile` + `xml.etree.ElementTree`) that reads `docProps/core.xml` → `dcterms:created` and normalizes it to `YYYY-MM-DD HH:MM:SS`, wired into `DocxConverter.convert()` to set `Article.created_date` (a missing timestamp is recorded in `Article.note`). Verify: the 1.1 test passes (green).
- [x] 1.3 Add a test for a document with no creation timestamp (mocked) asserting `created_date` is `""`, the issue is recorded in `Article.note`, and conversion succeeds. Verify: test passes.

## 2. Author extraction from the "Autor" line

- [x] 2.1 Add failing tests in `tests/converter/test_docx.py` asserting `created_by_alias == "Bernhard M."` for `ruderkurs_doc` and that the `data-custom-style="Autor"` block is absent from `Article.body`. Verify: `pytest tests/converter/test_docx.py -k autor` fails (red).
- [x] 2.2 Implement "Autor" line extraction as a private helper in `docx.py`, called from `DocxConverter.convert()`: locate the last `data-custom-style="Autor"` element, strip an optional leading `Autor:` label, set `Article.created_by_alias`, and `.decompose()` it from the soup. Verify: the 2.1 tests pass (green).
- [x] 2.3 Add a test for the `Autor:`-prefixed variant (mock `pypandoc.convert_file` to return `<div data-custom-style="Autor"><p>Autor: Max M.</p></div>`) asserting `created_by_alias == "Max M."`. Verify: test passes.

## 3. Missing / anomalous author → note

- [x] 3.1 Add a failing test for a document with no "Autor" line (mock) asserting `created_by_alias` is empty and `Article.note` states the author is missing. Verify: test fails (red).
- [x] 3.2 Implement the missing-author branch (in the `docx.py` helpers): when no "Autor" line (or empty after label stripping), leave `created_by_alias` empty and set `Article.note`. Verify: the 3.1 test passes (green).
- [x] 3.3 Add a test for the empty-"Autor"-line case (mock) asserting the same missing-author note and empty `created_by_alias`. Verify: test passes.
- [x] 3.4 Add a failing test for multiple "Autor" lines (mock returning two `data-custom-style="Autor"` blocks) asserting `created_by_alias` is the last one and `Article.note` flags the anomaly. Verify: test fails (red).
- [x] 3.5 Implement the multiple-"Autor"-lines branch: use the last line as the author and set the anomaly note. Verify: the 3.4 test passes (green).

## 4. Integration verification

- [x] 4.1 Run the full suite `pytest` (honoring the `--cov-fail-under=100` gate) plus the linters `ruff` and `ty`. Verify: all pass with 100% coverage and no lint/type errors.

## Workflow follow-up

- After the project's review requirements are satisfied, archive the change (`/opsx-archive`) and verify the archived result.

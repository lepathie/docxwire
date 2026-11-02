# Proposal

## Why

When docxwire publishes converted articles to Joomla it must supply article metadata — the author and the creation date — but the converter currently leaves `Article.created_by_alias`, `Article.created_date`, and `Article.note` empty. Both values are already present in the source `.docx` (an "Autor" styled line in the body, and the file's `dcterms:created` core property), so they can be extracted automatically instead of being lost.

## What Changes

- During `.docx` conversion, extract the **author** from the "Autor" line — the (usually) last body line that carries the custom paragraph style `Autor`, optionally prefixed with `Autor: `.
  - The extracted name is stored in `Article.created_by_alias`.
  - The "Autor" line is **removed from the article body** (mirroring how the title heading is already stripped).
- If no author can be determined (no `Autor` line, or the line is empty after stripping the prefix), the issue is **recorded in `Article.note`**.
- Anomalous documents are also **flagged in `Article.note`** — when more than one "Autor" line is present, the last is used as the author (best guess) and the anomaly is noted.
- Extract the **creation date** from the input `.docx`'s core properties (`dcterms:created`) and store it in `Article.created_date`.

**Out of scope:**
- The Joomla publishing step that consumes `Article` (the REST client) is not part of this change; this change only populates the `Article` metadata fields.
- The `dc:creator` core property is **not** used as the author — the author always comes from the body "Autor" line, per the source-document convention.
- `publish_up`, `metadesc`, `metakey`, and `tags` are not populated here.

## Capabilities

### New Capabilities
- `article-metadata`: How the converter extracts and attaches article metadata (author and creation date) during `.docx` conversion, and how a missing author is surfaced via `Article.note`.

### Modified Capabilities
<!-- None: this change adds the new article-metadata capability. -->

## Impact

- **Affected code:** `src/docxwire/converter/docx.py` (`DocxConverter.convert`) plus a small helper to read the `.docx` core properties. The `Article.created_by_alias`, `Article.created_date`, and `Article.note` fields already exist in `src/docxwire/converter/base.py`, so **no data-model change** is required.
- **Behavior:** `Article.body` will no longer contain the "Autor" line; `Article.created_by_alias` and `Article.created_date` will be populated; `Article.note` will carry a message when the author is missing.
- **Dependencies:** None new — core properties are read with the standard-library `zipfile` + `xml.etree.ElementTree` (the project has no `python-docx` dependency).
- **Tests:** `tests/converter/test_docx.py` against the real `.docx` fixtures in `tests/data/` (e.g. `Ruderkurs` has an `Autor` line and a `dcterms:created`); missing-author and no-core-property cases use `pypandoc`/file mocks.

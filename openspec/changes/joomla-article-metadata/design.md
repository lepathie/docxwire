# Design

## Context

`DocxConverter.convert()` (`src/docxwire/converter/docx.py`) renders a `.docx` to HTML with `pypandoc` (`format="docx+styles"`, `to="html-native_spans"`) and post-processes the result with BeautifulSoup. It already strips the first heading (→ `title`) and the pre-heading lead images from the body. The `Article` dataclass (`src/docxwire/converter/base.py`) already declares `created_by_alias`, `created_date`, and `note`; the converter simply never fills them.

Observed on the `Ruderkurs` fixture:
- The "Autor" paragraph style renders as `<div data-custom-style="Autor"><p>…name…</p></div>`, as the last block in the body.
- The creation timestamp lives in the package part `docProps/core.xml` as `<dcterms:created>2025-04-26T17:52:00Z</dcterms:created>` (namespace `http://purl.org/dc/terms/`).

See proposal.md for motivation; the spec (`specs/article-metadata/spec.md`) defines the required behavior.

## Goals / Non-Goals

**Goals:**
- Populate `Article.created_by_alias` (author), `Article.created_date` (creation timestamp), and `Article.note` (missing / anomalous author) during `.docx` conversion.
- Remove the "Autor" line from `Article.body`.
- Keep the change dependency-free and consistent with the existing soup-based pipeline.

**Non-Goals:**
- The Joomla publishing / REST step that consumes `Article` (out of scope).
- Using the `dc:creator` core property as the author (the author always comes from the body "Autor" line).
- Populating `publish_up`, `metadesc`, `metakey`, `tags`.

## Decisions

**1. Extract the author from the rendered soup, keyed on the `data-custom-style="Autor"` element.**
Find the element(s) carrying `data-custom-style="Autor"` in the BeautifulSoup soup, take the **last** in document order, read its text, and strip an optional leading `Autor:` label plus surrounding whitespace.
- *Why:* The converter already operates on this soup (title, lead images), so one parsing path handles everything, and removing the line from the same soup is natural.
- *Alternative considered:* parse `word/document.xml` directly for `w:pStyle w:val="Autor"`. Rejected — it duplicates parsing, diverges from the soup-based flow, and the body we publish *is* the soup.
- The selector is a pandoc output detail, so it is held in a single module-level constant to keep it in one place.

**2. Remove the "Autor" element from the soup before serializing the body.**
Call `.decompose()` on the matched element(s), mirroring how the heading and lead images are already removed, so the published `Article.body` no longer contains the author line.

**3. Read the creation timestamp with stdlib `zipfile` + `xml.etree.ElementTree`.**
Open the `.docx` as a zip, read `docProps/core.xml`, and parse `dcterms:created`.
- *Why:* The project has no `python-docx` dependency; stdlib is sufficient for one well-known element and keeps the dependency footprint flat.
- *Alternative considered:* add `python-docx` and use `core_properties.created`. Rejected — a new dependency to read a single XML element.

**4. Normalize `created_date` to Joomla's `YYYY-MM-DD HH:MM:SS` format** (e.g. `2025-04-26T17:52:00Z` → `2025-04-26 17:52:00`).
- *Why:* The user confirmed Joomla expects this format; the transform is a small, lossless reformat of the date-time, and doing it here makes `Article.created_date` directly publishable — the point of this change.
- *Timezone:* the core `created` is UTC (`Z`); this is a format normalization that preserves the UTC wall-clock. Any site-local conversion is a publisher-boundary concern (non-blocking; can be added where `Article` is consumed).

**5. Author / note semantics (one `note`, distinct messages).**
- Author found → `created_by_alias = author`; no author-related `note`.
- No "Autor" line, **or** empty after label stripping → `created_by_alias` left empty; `note` set to a message stating the author is missing.
- More than one "Autor" line → `created_by_alias = last`; `note` set to a message flagging the anomaly (multiple "Autor" lines found; the last was used). The messages are worded so the two cases are distinguishable.

**6. Keep the work inside the converter as private helpers — no separate "metadata" component.**
Both metadata sources are coupled to the conversion: the author is read from the BeautifulSoup soup that `convert()` already builds, and the creation date requires opening the same source `.docx` (zip) that is being converted. A separate component would have to be handed the soup and the source path (and the `Article`), adding a wiring layer with no reuse boundary to justify it. So the logic stays in `src/docxwire/converter/docx.py` as small private helper functions (e.g. `_read_created_date(src)`, `_extract_author(soup)`) alongside the existing `_flag_lead_images`, keeping `convert()` readable and each helper unit-testable.
- *Why:* YAGNI — there is no second consumer of a standalone "metadata" unit; the `Article` is the converter's output, and populating its fields is part of producing it.
- *Alternative considered:* a dedicated `metadata` module/class. Rejected — premature abstraction; it would duplicate the soup/`Article` context and couple to the converter's internals without a clear seam.

## Risks / Trade-offs

- [`data-custom-style` is a pandoc output detail; a pandoc version bump could change it] → the real-fixture tests assert both the extracted author and the body no longer containing the "Autor" block, so a regression fails the suite; the selector lives in one constant.
- [`dcterms:created` may be absent] → treated as an empty `created_date`, no failure (per spec).
- [The `Autor:` label and the name may sit in separate runs/spans] → the label is a text prefix, not a structural boundary, so reading the element's full text and regex-stripping a leading `Autor:` + whitespace handles it.
- [Core `created` is UTC (`Z`); Joomla may expect site-local time] → the converter normalizes format only (preserving the UTC wall-clock); any site-local conversion is deferred to the publisher boundary (non-blocking).

## Migration Plan

No data migration — the change only adds population of existing `Article` fields. Rollback is a straight revert of the converter change.

## Open Questions

- Timezone handling for `created_date`: the core `created` is UTC; if Joomla needs site-local time, that conversion is a publisher-boundary concern and non-blocking. The format itself (`YYYY-MM-DD HH:MM:SS`) is confirmed and handled in the converter.

# Tasks

Commit plan — two atomic commits: **commit 1** = groups 1–4 (note rework, verified by
integration/CI); **commit 2** = group 5 (title-fallback item).

## 1. Note builder

- [ ] 1.1 Add a note builder (collector) that accumulates item labels and renders `Prüfe: <a>, <b>` (empty string when nothing was added), de-duplicating identical items. Verify: unit tests pass for de-duplication, the `Prüfe:` prefix, and the empty case.
- [ ] 1.2 Give the builder a fixed item vocabulary and order — `Titel`, `Autor`, `Erstellungsdatum`, then image references — independent of insertion order. Verify: a unit test asserting the rendered order for a known multi-item set passes.

## 2. Metadata items (author, creation date)

- [ ] 2.1 Rework the author extraction to report the *condition* (missing, or multiple) instead of a free-form note string, and have the builder map both to the single `Autor` item (multiple still uses the last line as the author). Verify: failing tests first (no "Autor" line → `Prüfe: Autor`; two "Autor" lines → author is the last and the note carries `Autor`), then green.
- [ ] 2.2 Replace the inline `date_note` so a missing/unreadable creation date contributes the `Erstellungsdatum` item. Verify: a failing test (no creation timestamp → `Prüfe: Erstellungsdatum`) passes after the change.

## 3. Image ordering and positional references

- [ ] 3.1 Order `Article.images` by document position — lead images in encounter order, then in-body images in body order, then any unreferenced extracted media. Verify: a test asserting a multi-image document returns its images in document order passes.
- [ ] 3.2 Reference in-body images with guessed captions by a condensed ordinal (`1. & 2. Bild`, `1., 2. & 3. Bild`; non-contiguous keep their numbers, sorted ascending) instead of their media filenames. Verify: failing tests for the two- and three-image condensation and the non-contiguous case pass after the change.
- [ ] 3.3 Reference a lead image with a guessed caption by its lead-slot label, resolved through a single `_lead_label` function that returns a generic placeholder for now. Verify: a failing test (lead image guessed → the placeholder label) passes after the change.

## 4. Integration (commit 1)

- [ ] 4.1 End-to-end note behavior: a clean document yields an empty note; a document with several issues yields a single `Prüfe:` line in fixed order with no line breaks. Verify: a test covering both cases passes.
- [ ] 4.2 Run `make ci` (lint, type check, tests at 100% coverage). Verify: `make ci` exits 0.

## 5. Title fallback item (commit 2)

- [ ] 5.1 When the document has no heading (title falls back to the source file name), contribute the `Titel` item. Verify: a failing test (no heading → note includes `Titel`) passes after the change.
- [ ] 5.2 When a heading is present, contribute no `Titel` item. Verify: a test asserting no `Titel` item for a headed document passes.
- [ ] 5.3 Run `make ci` (lint, type check, tests at 100% coverage). Verify: `make ci` exits 0.

## Workflow follow-up

- Archive the change (`openspec archive`) once `make ci` is green and the publisher-UI rollout is confirmed; this moves it to `changes/archive/` and syncs the delta specs into `openspec/specs/`.
- Verify the archived result (main specs updated, change no longer in the active list).

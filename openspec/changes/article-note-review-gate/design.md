# Design

## Context

`DocxConverter.convert()` (`src/docxwire/converter/docx.py`) builds `Article.note` by
joining, with `"; "`, the note strings returned from three scattered sources:
`_extract_author` (author), an inline `date_note` (creation date), and
`_guessed_caption_note` (guessed captions). `Article.note` is a plain `str`
(`src/docxwire/converter/base.py`) and is the sole carrier of these issues. The
`Article.images` list is built by globbing the extracted-media temp dir
(`media_path.glob("**/*")`), i.e. in **filesystem order**, not document order. Lead-slot
assignment (Intro / full-article) does not exist yet — every pre-heading image is only
`is_lead=True`. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- One `Prüfe:` one-line German, actionable note; empty iff nothing to review.
- A single builder that owns collection, de-duplication, stable ordering, and joining.
- Positional image references (in-body ordinal; lead slot label) instead of filenames.
- A clean seam so the lead label upgrades to `Einleitungsbild` / `Komplettes Beitragsbild`
  when slot assignment lands, with no other change.

**Non-Goals:**
- No new public field on `Article` (`note` stays `str`).
- No hard character cap / truncation / elision.
- No lead-slot assignment itself (that ships with the Joomla client / orchestration work).

## Decisions

**1. `Article.note` stays a single `str`.**
The consumer is a human reading one small UI field; a structured `list[Issue]` with codes and
severities would be consumed by no program. Alternatives considered: adding `issues:
list[Issue]` (rejected — over-engineered for a one-line human field); keeping the three
helpers (rejected — see 2).

**2. One internal note builder replaces the three note sources + the ad-hoc join.**
A small collector (e.g. a `NoteBuilder` with `.add(item)` and `.build() -> str`) is called
from `convert()`. It de-duplicates items, orders them by a fixed sequence, and renders
`Prüfe: <a>, <b>, …` (empty when nothing was added). `_extract_author`, the inline
`date_note`, and `_guessed_caption_note` stop returning free-form note strings; they report
*which condition held* and the builder maps it to the item label. This removes the coupled
"edit the join tuple" extension point and gives one place for dedup + order + language.
Alternative considered: keep helpers returning strings and join — rejected (no dedup/order,
scattered wording, the join tuple is a fragile extension point).

**3. Fixed item vocabulary and order (German).**
`Prüfe:` prefix; items in this order: `Titel`, `Autor`, `Erstellungsdatum`, then image
references. Metadata first, images last. Labels: `Titel`, `Autor`, `Erstellungsdatum`;
in-body ordinals `1. Bild`, `2. Bild`, …; lead labels `Einleitungsbild` /
`Komplettes Beitragsbild` (placeholder until slot assignment exists).

**4. Image references are positional.**
- In-body: 1-based ordinal among in-body images in document order, rendered **condensed** to
  one shared `Bild` — numbers listed ascending, joined with `, ` and `& ` before the last
  (`1. & 2. Bild`, `1., 2. & 3. Bild`); non-contiguous ordinals keep their own numbers.
- Lead: the image's lead-slot label, resolved through a single function
  `_lead_label(image) -> str` that returns the generic placeholder now and the assigned slot
  label later. This is the phased seam.

**5. `Article.images` is ordered by document position.**
Document order = lead images (in the order their `<img>` was encountered before the heading)
followed by in-body images (in `soup.find_all("img")` order). Each is matched to its
extracted media file by filename, as today. Images that are extracted but never referenced in
the body are ordered after the referenced ones. In-body ordinals are computed from the
in-body subset of this ordering. This makes `1. Bild` / `2. Bild` match what the reader sees.

**6. No length cap.**
The builder never truncates or elides; shortness comes from terse items and positional
references. (Alternative considered: cap + `… +N mehr` — rejected per the UX decision.)

## Risks / Trade-offs

- [Note content/language is a breaking change to the string] → It feeds an out-of-tree UI
  field the publisher reads; the German actionable format *is* the intended contract. Update
  the substring-based tests; coordinate the rollout with the publisher UI.
- [A very image-heavy document yields a long line] → Accepted trade-off: positional
  references are short and more valuable than a count; strict budgeting is out of scope.
- [Reordering `Article.images` may affect downstream] → Verify the publishing/upload path does
  not depend on the current glob order (leads are already distinguished by `is_lead`, body
  figures reference by filename). If it does, order a copy for the note and leave the list
  untouched.
- [Ordinal correctness depends on body order] → The body HTML is the source of truth for
  in-body document order; derive ordinals from it, not from the media dir.

## Migration Plan

Converter-internal; `Article.note` stays a `str`, so no data migration. Two atomic commits:
the first lands the builder, the German format, image ordering with positional references, and
the integration/CI checks; the second lands the `Titel` (title-fallback) item. The lead label
is a no-op placeholder until slot assignment lands, at which point only `_lead_label` changes.
Rollback is a single-converter revert.

## Open Questions

- The exact word for the generic unassigned-lead placeholder (e.g. `Leitbild` / `Deckblatt` /
  `Titelbild`). Deferrable — the spec only requires "a single generic placeholder label."

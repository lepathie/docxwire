# Proposal

## Why

`Article.note` is the publisher's review signal: it maps 1:1 to a small, single-line
field in the publishing UI. An **empty** note means "nothing to check, publish fast"; a
**non-empty** note tells the publisher *what to look at* before publishing.

Today the note is an ad-hoc, English, diagnostic `"; ".join` of three scattered helper
strings. It overflows the small field (a guessed-caption note dumps every affected
filename), reads as a conversion post-mortem rather than an action list, and silently
swallows review-worthy conditions (e.g. the no-heading → filename-title fallback) — so an
empty note is not a trustworthy green light.

## What Changes

- Rework `Article.note` into a compact, one-line, **German**, actionable review prompt:
  `Prüfe: <item, …>`, **empty when nothing needs checking**.
- Replace the three scattered note helpers and the ad-hoc join with a **single note
  builder** that collects short item labels, de-duplicates them, orders them stably, and
  joins them. There is **no hard character cap** — the line stays short through terse
  items (design-for-length, do not enforce).
- **Image references become positional / role-based** instead of media filenames:
  - in-body images → condensed document-order ordinal (`1. & 2. Bild`, `1., 2. & 3. Bild`);
  - lead images → slot label. A generic placeholder for now; `Einleitungsbild` /
    `Komplettes Beitragsbild` once lead-slot assignment lands (phased — that feature ships
    with the Joomla client / orchestration work).
- **Order `Article.images` by body position** so ordinals are correct (the list is
  currently built from a media-dir `glob`, i.e. filesystem order, not article order).
- **New condition:** a missing heading (title fell back to the source filename) is surfaced
  as a `Titel` item, so an empty note is honest.
- `Article.note` **remains a single `str`** (it maps 1:1 to the UI field); no new public
  field is added.
- **BREAKING (behavioral):** the note's content, language, and format change. It is now
  German and action-oriented; the existing English diagnostic strings and the
  substring-based test assertions are replaced.

## Capabilities

### New Capabilities

- `article-note`: The cross-cutting contract for the publisher review note — the `Prüfe:`
  one-line German format, the item set and stable ordering, the honest-empty invariant,
  the design-for-length (not enforced) policy, the single builder, and the
  positional/role-based image-reference scheme (ordinal now, lead slots phased).

### Modified Capabilities

- `article-metadata`: The author / creation-date / (new) title conditions now emit the
  `Autor` / `Erstellungsdatum` / `Titel` items into the note (reworded from "recorded in
  the note" diagnostics). "Multiple Autor lines" folds into the single `Autor` item.
- `article-images`: A guessed caption now references the image **positionally** (in-body
  ordinal now; lead slot placeholder now) instead of naming media filenames. The existing
  "single concise line, no caption text, no line breaks" constraint is preserved and
  re-expressed in terms of the note item.

## Impact

- **Code:** `src/docxwire/converter/docx.py` — a note builder replaces the note returns of
  `_extract_author`, the inline `date_note`, and `_guessed_caption_note`; images are ordered
  by body position; a new title-fallback condition is added. `src/docxwire/converter/base.py`
  is unchanged at the data-model level (`note` stays `str`); a small internal builder helper
  is introduced.
- **Tests:** `tests/converter/test_docx.py` note assertions are updated to the German item
  format.
- **Data model / dependencies:** none — `Article.note` stays a `str`; no new dependencies.
- **Consumer:** the (out-of-tree) Joomla publishing UI field receives a German, bounded,
  actionable string.
- **Follow-up seam:** lead slot labels (`Einleitungsbild` / `Komplettes Beitragsbild`) are a
  placeholder until the lead-slot assignment feature lands; the builder keeps a single swap
  point for it.

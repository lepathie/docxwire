# Design

## Context

`build_article_payload` in `src/docxwire/joomla/mapping.py` is the single place
Joomla field knowledge lives; it maps a converted `Article` to the flat create
payload. `Article.note` is already populated by the converter's note builder
(`Prüfe: …` or `""`), but the payload has no `note` key. The live site confirms
the content API accepts `note` on create and persists it.

## Goals / Non-Goals

**Goals:**

- The create payload carries the article's note verbatim in `note`.

**Non-Goals:**

- No changes to how the note is built (article-note capability), to the client
  transport, or to update/delete payloads.

## Decisions

- **Emit `note` unconditionally, like `metadesc`/`metakey`.** The field is part
  of the fixed payload dict, so a clean article sends `note: ""`. Alternative
  considered: emit only when non-empty (like `created` and `images`) — rejected
  because the note is a plain metadata field with no absence semantics, and
  conditional emission would add a branch for no behavioral benefit.

## Risks / Trade-offs

- [Re-publishing an article with a changed note does not update it] → Out of
  scope: create payloads only; re-publishing behavior is not part of this
  change.

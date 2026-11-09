# Proposal

## Why

The Joomla content API accepts a `note` attribute on article create and persists it
(verified against the live site), but the payload mapping never sends one. The
publisher review note that the converter builds (`Prüfe: …`, the article-note
capability) is therefore silently dropped on publish, so the review prompt never
reaches the published article.

## What Changes

- The mapping from a converted article to the create payload carries the article's
  `note` into the payload's `note` field, always (including the empty string for a
  clean article).
- The `joomla-client` spec's "Article metadata is carried into the payload"
  requirement is extended to include `note`, with a scenario.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `joomla-client`: the "Article metadata is carried into the payload" requirement
  gains the `note` field — the mapping SHALL carry the article's note into the
  create payload's `note` attribute.

## Impact

- Code: `src/docxwire/joomla/mapping.py` — `build_article_payload` gains one line
  (`"note": article.note`).
- Tests: `tests/joomla/test_mapping.py` — the note is asserted on the payload.
- No API, dependency, or converter changes; `Article.note` is already populated by
  the existing note builder.

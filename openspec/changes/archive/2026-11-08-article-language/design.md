# Design

## Context

The `joomla-client` change's Verified contract established that the club's Joomla 5 site has multilingual support enabled: a create without `language` fails with 400 "Field 'language' doesn't have a default value". The current mapping therefore hard-sends the all-languages sentinel `*` (the value the Joomla API manual uses in its examples). The club publishes in German; the site-wide default belongs in the settings, and a per-article override (e.g. a translation) belongs on the article.

## Goals / Non-Goals

**Goals:**

- A single site-wide language default in the `[joomla]` settings (optional, `*` by default).
- A per-article override on the `Article` (optional, empty by default).
- Deterministic resolution: article → settings → `*`.

**Non-Goals:**

- Extracting a language from the `.docx` (the converter stays language-agnostic).
- Managing multiple language variants of one article (a later orchestration concern).

## Decisions

1. **Resolution order: article, then settings, then the sentinel.** The settings default covers the club's everyday case (`de-DE`); the article field is the escape hatch; `*` keeps a settings file without the new key working unchanged.
2. **The mapping takes the `JoomlaSettings`, not scalars** — `build_article_payload(article, settings)`. It already needs `default_catid`; the language would be a second scalar, and the settings object is the single coupling point (`joomla-client` design decision 3).
3. **`Article.language: str = ""`** — empty means "unset". The converter never sets it; a caller (the pipeline) sets it for the rare per-article case. All `Article` fields are defaulted and constructed by keyword, so the field is additive.

## Risks / Trade-offs

- **Sequencing:** the `joomla-client` delta is a MODIFIED of the archived "Article metadata is carried into the payload" requirement (the resolution is folded into it, replacing the "how that value is resolved is a separate concern" deferral). The `settings` delta's example-file block is written as the union of the current requirement and the `settings-example-base-path` pin (five keys, `base_path` pinned, `default_language` placeholder) — a MODIFIED block replaces the requirement wholesale at archive time, so this change must land after `settings-example-base-path` or it would drop the pin.
- **`settings.toml.example` is a contract** → a test asserts the keys and placeholders, so the example cannot drift from the loader again.

## Migration Plan

None breaking: an existing `settings.toml` without `default_language` loads with `*` exactly as before. The club's `settings.toml` (gitignored) gains `default_language = "de-DE"`.

## Open Questions

(None)

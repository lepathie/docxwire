# Proposal

## Why

The `joomla-client` change's live verification established that the club's Joomla 5 site has multilingual support enabled: a create without `language` fails with 400 "Field 'language' doesn't have a default value". The mapping therefore hard-sends the all-languages sentinel `*`. The club publishes in German — a single site-wide default (`de-DE`) belongs in the settings, and the occasional per-article language (e.g. a translation) belongs on the article.

## What Changes

- The `[joomla]` settings section gains an optional `language` key (string, default `*`), validated by the settings loader; `settings.toml.example` documents it.
- The `Article` dataclass gains an optional `language` field (empty by default) as a per-article override; the converter never sets it.
- `build_article_payload` resolves the payload's `language`: the article's language, else the settings' `language`, else the all-languages sentinel `*`. The mapping takes the `JoomlaSettings` (it already needs `default_catid` from it).

## Capabilities

### New Capabilities

(None)

### Modified Capabilities

- `settings`: the `[joomla]` section accepts an optional `language` (default `*`); the example file documents it.
- `joomla-client`: the payload's `language` is resolved (article → settings → `*`) instead of hard-coded.

## Impact

- **Code:** `src/docxwire/settings.py` (optional key + type check), `src/docxwire/converter/base.py` (one new `Article` field), `src/docxwire/joomla/mapping.py` (signature + resolution).
- **Files:** `settings.toml.example` (one placeholder line); tests for the loader, the example file, and the mapping.
- **Settings:** the club's gitignored `settings.toml` gains `language = "de-DE"`.
- **Sequencing:** apply after `settings-example-base-path` is archived.

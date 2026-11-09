# Design

## Context

All flow parts exist and are tested in isolation: `DocxConverter.convert`
produces an `Article` (with `created_date` as `YYYY-MM-DD HH:MM:SS` or `""`),
`build_article_payload(article, settings)` shapes the create payload (including
`note`), and `JoomlaClient` exposes article CRUD and image upload.
`load_settings()` already defaults to `settings.toml` in the current working
directory. Nothing composes them, and there is no console entry point
(`src/docxwire/__init__.py` is empty, no `[project.scripts]`).

Verified against the staging site: a create without `state` lands in the
site's default state (0, draft); a create without `created` is accepted and
the site fills the current date.

## Goals / Non-Goals

**Goals:**

- One command, `docxwire <file.docx>`, drives the whole flow and reports the
  result.
- The orchestration is a plain, unit-testable function separate from argument
  parsing, so later front-ends (batch, `--dry-run`) reuse it.
- Zero new runtime dependencies.

**Non-Goals:**

- Config discovery beyond the CWD, CLI options of any kind, batch/multi-doc
  runs, dry-run, article links, onboarding — all deferred to follow-up
  changes (see proposal).

## Decisions

### 1. `argparse`, not a CLI framework

Stdlib `argparse` parses one positional argument; `click`/`typer` would add a
runtime dependency for no capability gain at this size. Revisit if a follow-up
change adds subcommands.

### 2. Two new modules: `cli.py` and `publish.py`

- `src/docxwire/publish.py` — the orchestration. One public function
  `publish_article(docx_path, settings) -> dict` that converts, derives and
  uploads the image paths, builds the payload, and creates the article; it
  returns the created article's data and raises the existing typed errors
  (`SettingsError` is not its concern — settings are in; `JoomlaApiError` and
  the converter's `RuntimeError` propagate).
- `src/docxwire/cli.py` — the thin entry point. Parses the argument, checks
  the file exists, loads settings from the CWD, calls `publish_article`,
  prints the result, and maps exceptions to `error: …` on stderr with a
  non-zero exit. Exit codes: `0` success, `1` operational failure
  (settings/conversion/API), `2` usage (argparse default).

The split keeps every spec requirement testable at a seam: argument and
output behavior in `cli.py` (invoked in-process), flow behavior in
`publish.py` (with a stubbed client).

### 3. Image path derivation lives in `publish.py`

For each image: rel-path `articles/<YYYY>/<MM>/<slug>/<media_filename>`,
where `<YYYY>-<MM>` is the date part of `Article.created_date` (its first ten
characters) or, when the article has no created date, the current local date.
`Image.upload_path` is set to `/images/<rel-path>` for **every** image before
`build_article_payload` runs — the mapping's body-rewrite and `images` object
both read those values, and all images upload so an editor can swap the lead
later. The media upload itself uses the rel-path (the client prefixes the
images adapter).

### 4. Output shape

```
Created draft article 503: <title>
<note>            # the Prüfe: … line, verbatim
```

with `Nothing to review.` in place of the note when it is empty. The created
id is read from the create response's data.

### 5. Operation order

argument → file-exists check → settings load → convert → upload all images →
create article. File and settings checks happen before any conversion or
network activity, per the spec.

## Risks / Trade-offs

- **Re-running the same document** may hit an alias collision (or create a
  duplicate, depending on the site) → the typed `JoomlaApiError` message is
  surfaced as-is; upsert semantics are a follow-up change.
- **Partial failure** (a later image upload or the create fails) leaves
  already-uploaded images on the site unreferenced → harmless: re-runs
  override the same paths idempotently; accepted.
- **"Today" is client-local** while the site fills `created` with its
  server-local date → in a time-zone edge the folder date can be one day off
  from the article's `created` → cosmetic folder organization only; accepted.
- **pandoc failures** surface as the converter's `RuntimeError` with a
  `conversion of <file> failed:` prefix → already actionable; the CLI passes
  it through.

## Open Questions

(None)

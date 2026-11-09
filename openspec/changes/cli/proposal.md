# Proposal

## Why

The converter and the Joomla publisher are complete as libraries, but nothing
connects them: there is no way to run the whole flow on a single `.docx`
document. This change adds the `docxwire` command that takes one document and
drives the existing parts end to end — the tool's first runnable form.

## What Changes

- A new `docxwire` console command (`[project.scripts]` entry, `argparse` — no
  new dependency) taking a single `.docx` path as its only argument.
- A publishing flow composing the existing parts: load settings from
  `settings.toml` in the current working directory → `DocxConverter.convert`
  → upload every article image via the Media API → `build_article_payload` →
  `JoomlaClient.create_article`.
- Image target-path derivation: `articles/<YYYY>/<MM>/<slug>/<basename>` under
  the site's `images/` tree (i.e. `Image.upload_path` =
  `/images/articles/…`), with `<YYYY>/<MM>` taken from the article's created
  date and falling back to the current day when the article has none — the same
  date the site then fills into the article's `created` field.
- The command reports the created article's id and the review note
  (`Prüfe: …`, or that nothing needs review) and exits 0; settings,
  conversion, and API failures print an actionable message and exit non-zero.
- The article is created in the site's default state (draft); the payload sends
  no `state`.

## Capabilities

### New Capabilities

- `cli`: the user-facing `docxwire` command — the single-document publishing
  flow driven from the command line: the command's argument surface, settings
  loading from the current working directory, the convert → image upload →
  article create orchestration, result reporting, and failure/exit-code
  behavior.

### Modified Capabilities

(None)

## Impact

- **Code:** new `src/docxwire/cli.py` (entry point, argument parsing,
  reporting) and a new orchestration module (e.g. `src/docxwire/pipeline.py`);
  a `[project.scripts]` entry in `pyproject.toml`.
- **Tests:** new tests for the CLI and the pipeline (settings loading,
  path derivation, upload-then-create ordering, output, exit codes).
- **Dependencies:** none (`argparse` is stdlib).
- **Out of scope** (follow-up changes): `--config` / nearest-config-file
  discovery, folder batch with multi-document output, `--dry-run`, direct
  admin/live article links, onboarding (`docxwire init`, environment
  variables), alias-collision handling on re-runs.

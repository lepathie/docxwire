# Tasks

## 1. Publishing flow (`src/docxwire/publish.py`)

- [ ] 1.1 Write a failing test for `publish_article`: given a document and Joomla settings it converts, derives each image's rel-path `articles/<YYYY>/<MM>/<slug>/<media_filename>` from the article's `created_date`, sets every `Image.upload_path` to `/images/<rel-path>`, uploads every image, then builds the payload and creates the article, returning the created article's data — and the image uploads happen before the create call; verify the test fails (no module yet)
- [ ] 1.2 Implement `src/docxwire/publish.py` with `publish_article(docx_path, settings)` per design.md decisions 2–3; verify the 1.1 test passes
- [ ] 1.3 Add tests: an article without a `created_date` uses the current date in the derived path; a conversion failure propagates as the converter's `RuntimeError` with no upload or create call; an image-upload failure propagates as `JoomlaApiError` with no create call; verify they pass

## 2. CLI (`src/docxwire/cli.py`)

- [ ] 2.1 Write failing tests for the command: invoked without a path it exits 2 with a usage message; invoked with a nonexistent path it exits 1 with an actionable error naming the file and performs no conversion or network activity; verify the tests fail (no module yet)
- [ ] 2.2 Implement `src/docxwire/cli.py` with an in-process-invocable `main`: argparse with one positional, file-exists check, `load_settings` from the CWD, `publish_article`, success output `Created draft article <id>: <title>` plus the note line (or `Nothing to review.`), `error: …` on stderr with exit 1 for settings/conversion/API failures; verify the 2.1 tests pass
- [ ] 2.3 Add tests: a missing `settings.toml` in the CWD exits 1 with a message pointing to the example file and no conversion or network activity; a `JoomlaApiError` from the flow exits 1 with the API error's message; verify they pass

## 3. Entry point

- [ ] 3.1 Add a `[project.scripts]` entry `docxwire = "docxwire.cli:main"` to `pyproject.toml`; verify `uv run docxwire --help` prints the command's usage
- [ ] 3.2 Smoke test the installed command against the staging site: run `docxwire` on a real `.docx` from the folder holding `settings.toml`; verify a draft article with working images exists on the site and the printed id matches

## 4. Integration

- [ ] 4.1 Run `make ci` (lint, type check, tests at 100% coverage); verify it is green

## Workflow follow-up

- Apply only after any in-flight changes this one depends on are archived (none at proposal time).
- Archive this change (move to `changes/archive/` + spec sync) once `make ci` is green and the user has reviewed — its own commit, per repo convention.

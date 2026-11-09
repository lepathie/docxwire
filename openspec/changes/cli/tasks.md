# Tasks

## 1. Publishing flow (`src/docxwire/publish.py`)

- [x] 1.1 Write a failing test for `publish_article`: given a document and Joomla settings it converts, derives each image's rel-path `articles/<YYYY>/<MM>/<slug>/<media_filename>` from the article's `created_date`, sets every `Image.upload_path` to `/images/<rel-path>`, uploads every image, then builds the payload and creates the article, returning the created article's data — and the image uploads happen before the create call; verify the test fails (no module yet)
- [x] 1.2 Implement `src/docxwire/publish.py` with `publish_article(docx_path, settings)` per design.md decisions 2–3; verify the 1.1 test passes
- [x] 1.3 Add tests: an article without a `created_date` uses the current date in the derived path; a conversion failure propagates as the converter's `RuntimeError` with no upload or create call; an image-upload failure propagates as `JoomlaApiError` with no create call; verify they pass

## 2. CLI (`src/docxwire/cli.py`)

- [x] 2.1 Write failing tests for the command: invoked without a path it exits 2 with a usage message; invoked with a nonexistent path it exits 1 with an actionable error naming the file and performs no conversion or network activity; verify the tests fail (no module yet)
- [x] 2.2 Implement `src/docxwire/cli.py` with an in-process-invocable `main`: argparse with one positional, file-exists check, `load_settings` from the CWD, `publish_article`, success output `Created draft article <id>: <title>` plus the note line (or `Nothing to review.`), `error: …` on stderr with exit 1 for settings/conversion/API failures; verify the 2.1 tests pass
- [x] 2.3 Add tests: a missing `settings.toml` in the CWD exits 1 with a message pointing to the example file and no conversion or network activity; a `JoomlaApiError` from the flow exits 1 with the API error's message; verify they pass

## 3. Entry point

- [x] 3.1 Add a `[project.scripts]` entry `docxwire = "docxwire.cli:main"` to `pyproject.toml`; verify `uv run docxwire --help` prints the command's usage
- [x] 3.2 Smoke test the installed command against the staging site: run `docxwire` on a real `.docx` from the folder holding `settings.toml`; verify a draft article with working images exists on the site and the printed id matches

## 4. Integration

- [x] 4.1 Run `make ci` (lint, type check, tests at 100% coverage); verify it is green

## 5. Image path refinement (`publish.py`)

- [x] 5.1 Write a failing test: an article whose images have media filenames `media/lead.jpg` / `media/body.jpg` and whose title is `2026.03 Regatta` uploads to `articles/2026/03/<slug>/lead.jpg` (no `media` component), and the title date wins over a later created date; verify the tests fail
- [x] 5.2 Implement: a `title_date` helper in `src/docxwire/converter/base.py` (leading `YYYY.MM`-style title prefix → `YYYY/MM`, `""` when absent) and `publish.py` using the basename plus the title-date → created-date → current-date chain; verify the tests pass
- [x] 5.3 Add tests: a dateless title uses the created date; a dateless title with no created date uses the current date (retarget the existing fallback test at a dateless title); `title_date` unit tests; verify they pass

## 6. Body image reference robustness (`mapping.py`, `cli.py`)

- [x] 6.1 Write a failing test: a body `<img src>` that is an absolute temporary-directory path (`/tmp/media-XXXX/media/image1.jpeg`) is matched by basename to the image with media filename `media/image1.jpeg` and rewritten to its uploaded path; a `src` whose basename matches no image fails the build; verify the tests fail
- [x] 6.2 Implement basename matching in `_rewrite_body_images`; verify the tests pass
- [x] 6.3 Write a failing CLI test: a `ValueError` from the flow is reported as `error: …` with exit 1; implement by extending the CLI's exception mapping; verify the test passes

## 7. Final integration

- [x] 7.1 Run `make ci` (lint, type check, tests at 100% coverage); verify it is green

## 8. Slug-based folder date

- [x] 8.1 Write failing tests: an article with slug `regatta-2026-03` and a dateless title files its images under `2026/03`; a slug date wins over a conflicting title prefix; verify the tests fail
- [x] 8.2 Implement: a `slug_date` helper in `src/docxwire/converter/base.py` (trailing `-YYYY-MM` of the slug → `YYYY/MM`) and `publish.py` precedence slug → title → created → current; verify the tests pass
- [x] 8.3 Add `slug_date` unit tests and retarget the title-date tests at dateless slugs; run `make ci`; verify it is green
- [x] 8.4 Republish Adams Acht on staging: trash and delete the article filed under `2026/10`, re-run `docxwire`, verify the article's images sit under `2026/09`

## 9. Drop the title from the folder-date chain

- [x] 9.1 Remove the `title_date` helper and its unit tests; `publish.py` derives the folder date from slug → created → current; retarget the affected tests; run `make ci`; verify it is green

## Workflow follow-up

- Apply only after any in-flight changes this one depends on are archived (none at proposal time).
- Archive this change (move to `changes/archive/` + spec sync) once `make ci` is green and the user has reviewed — its own commit, per repo convention.

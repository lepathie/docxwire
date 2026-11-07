# Tasks

## 1. Media upload transport (`src/docxwire/joomla/client.py`)

- [ ] 1.1 Add the media endpoint constant and a `JoomlaClient.upload_image` method that POSTs the JSON body (adapter-prefixed `path`, base64 `content`, `override` flag) to `/media/files` under the existing auth/accept headers and returns the created item's data; verify with a unit test on a mocked session asserting the request URL, headers, and body shape and the returned data passes
- [ ] 1.2 Surface failed uploads as the typed `JoomlaApiError` (status + server error entries, no retry); verify with a unit test for a non-2xx upload response asserting the typed error is raised

## 2. Image-aware payload mapping (`src/docxwire/joomla/mapping.py`)

- [ ] 2.1 Rewrite every body `<img>` reference from the local media filename to the image's `upload_path` via the exact `{media_filename → upload_path}` map; verify with a unit test for a body referencing an uploaded image asserting the `introtext` carries the corrected reference
- [ ] 2.2 Fail the payload build (raised error, no payload) when a body-referenced image has no `upload_path`; verify with a unit test asserting the raised error
- [ ] 2.3 Emit the `images` object carrying the first lead image in list order in both `image_intro` and `image_fulltext` with its caption and empty alt, and omit the key when the article has no lead image; verify with unit tests for one lead, two leads (only the first referenced), and no lead
- [ ] 2.4 Combined mapping test: an article with a lead image and in-body images (all `upload_path` populated) yields one payload with the corrected body and the `images` object together; verify the test passes

## 3. Integration check

- [ ] 3.1 Run `make ci` and verify it is green (lint, type check, full test suite at 100% coverage)

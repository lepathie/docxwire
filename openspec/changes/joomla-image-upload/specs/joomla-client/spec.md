# Spec Delta

## ADDED Requirements

### Requirement: The client exposes media upload
The client SHALL upload an image file to the site's Media API (the `/media/files` endpoint under the API base) with a JSON body carrying the target path prefixed by the images adapter, the file content base64-encoded, and an override flag, under the same authentication and content negotiation as the article endpoints, and SHALL return the created item's data. A non-2xx response SHALL surface as the typed API error with no automatic retry.

#### Scenario: Uploading an image
- **WHEN** an image is uploaded to a target path
- **THEN** the request is a POST to the media endpoint carrying the adapter-prefixed path, the base64 content, and the override flag, and the created item's data is returned

#### Scenario: Upload failure is a typed error
- **WHEN** an upload is answered with a non-2xx status carrying the Joomla error envelope
- **THEN** a typed API error is raised carrying the status and the server's error entries

### Requirement: The payload's body image references point to uploaded media
The mapping SHALL rewrite every `<img>` reference in the article body from the image's local media filename to that image's uploaded site-relative path, matched exactly by media filename. Building the payload SHALL fail when any image referenced in the body has no uploaded path.

#### Scenario: Body references are rewritten
- **WHEN** a payload is built for an article whose body references an image that has an uploaded path
- **THEN** the body's `<img>` reference for that image is the uploaded site-relative path

#### Scenario: Unuploaded body image fails the build
- **WHEN** a payload is built for an article whose body references an image without an uploaded path
- **THEN** the payload build fails with an error and no payload is produced

### Requirement: The lead image is carried in the images object
When the article has lead images, the mapping SHALL emit an `images` object carrying the first lead image in the article's image list in both `image_intro` and `image_fulltext`, with the image's caption in the corresponding caption fields and an empty alt; no other lead image SHALL be referenced. When the article has no lead images, the payload SHALL carry no `images` object.

#### Scenario: A lead image is carried in both slots
- **WHEN** a payload is built for an article with a lead image that has an uploaded path
- **THEN** the payload's `images` object carries that image's uploaded path in both `image_intro` and `image_fulltext` and its caption in the corresponding caption fields

#### Scenario: Secondary lead images are not referenced
- **WHEN** a payload is built for an article with two or more lead images
- **THEN** only the first lead image in the image list appears in the `images` object

#### Scenario: No lead image means no images object
- **WHEN** a payload is built for an article with no lead images
- **THEN** the payload contains no `images` object

## MODIFIED Requirements

### Requirement: The article body goes into a single body field
The mapping SHALL send the entire article body in a single body field: the whole body in `introtext` and an empty `fulltext`, so that no read-more split is implied. The body's image references SHALL be the corrected references to the uploaded media. The deprecated `articletext` field SHALL NOT be used. Live verification confirmed `introtext` is accepted on create and persists; the API exposes the stored body as the `text` attribute on read.

#### Scenario: Body is placed in the single body field
- **WHEN** a payload is built for an article with a non-empty body
- **THEN** the payload's `introtext` is the full article body, with its image references corrected to the uploaded media, and its `fulltext` is empty

#### Scenario: The deprecated field is not used
- **WHEN** a payload is built for any article
- **THEN** the payload does not contain an `articletext` field

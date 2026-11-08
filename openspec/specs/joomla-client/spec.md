# joomla-client Specification

## Purpose

Defines the behavior of DOCxWIRE's thin client for the Joomla 5 REST content API: how it is configured and authenticated, the article CRUD surface it exposes, how a converted article is mapped to an API payload, and how API failures are surfaced.

## Requirements

### Requirement: The client is configured from Joomla settings
The client SHALL be constructed from the validated Joomla settings (base URL, base path, API token, default category) and SHALL address the article endpoint as `<base_url><base_path>/content/articles`. Every request SHALL carry `Accept: application/vnd.api+json` (the API answers 406 without a matching Accept header), and create/update requests SHALL send their payload as a flat JSON object body with `Content-Type: application/json` (the API does not parse JSON:API-shaped write bodies).

#### Scenario: Endpoint is composed from settings
- **WHEN** the client is created with a base URL and base path
- **THEN** all article requests are sent to the composed article endpoint

#### Scenario: Token is sent on every request
- **WHEN** the client performs any article request
- **THEN** the request carries the API token in the `X-Joomla-Token` header

#### Scenario: Accept header is sent on every request
- **WHEN** the client performs any article request
- **THEN** the request carries `Accept: application/vnd.api+json`

#### Scenario: Write bodies are flat JSON
- **WHEN** an article is created or updated
- **THEN** the request body is the flat payload object encoded as JSON with `Content-Type: application/json`

### Requirement: The client sends an optional Basic Auth header
When the Joomla settings include a Basic Auth value, the client SHALL send `Authorization: Basic <value>` on every request, with the value sent verbatim (not re-encoded). When no Basic Auth value is configured, the client SHALL send no `Authorization` header. The header composes with the Joomla token, which is sent separately in `X-Joomla-Token`.

#### Scenario: Basic Auth header is sent when configured
- **WHEN** the client is created with a Basic Auth value and performs any article request
- **THEN** the request carries `Authorization: Basic <value>` with the value sent verbatim

#### Scenario: No Authorization header when not configured
- **WHEN** the client is created without a Basic Auth value and performs any article request
- **THEN** the request carries no `Authorization` header

#### Scenario: Basic Auth composes with the Joomla token
- **WHEN** the client is created with both a Basic Auth value and an API token and performs a request
- **THEN** the request carries both `Authorization: Basic <value>` and the API token in `X-Joomla-Token`

### Requirement: The client exposes the full article CRUD surface
The client SHALL support listing articles, getting one article by ID, creating an article, updating an article by ID, and deleting an article by ID, and SHALL return the API's JSON data for each operation.

#### Scenario: Listing articles
- **WHEN** articles are listed
- **THEN** the data items of the API's collection response are returned

#### Scenario: Getting an article
- **WHEN** an article is requested by ID
- **THEN** the article object with that ID is returned

#### Scenario: Creating an article
- **WHEN** an article is created from a payload
- **THEN** the created article, including its new ID, is returned

#### Scenario: Updating an article
- **WHEN** an article is updated by ID with a partial payload
- **THEN** the updated article is returned

#### Scenario: Deleting an article
- **WHEN** an article is deleted by ID
- **THEN** the DELETE request is sent and the API's response is surfaced (the verified site answers 204 with an empty body; on a live article the DELETE is a no-op — the client's `delete_article` documents the two-step removal)

### Requirement: The client exposes media upload
The client SHALL upload an image file to the site's Media API (the `/media/files` endpoint under the API base) with a JSON body carrying the target path prefixed by the images adapter, the file content base64-encoded, and an override flag, under the same authentication and content negotiation as the article endpoints, and SHALL return the created item's data. A non-2xx response SHALL surface as the typed API error with no automatic retry.

#### Scenario: Uploading an image
- **WHEN** an image is uploaded to a target path
- **THEN** the request is a POST to the media endpoint carrying the adapter-prefixed path, the base64 content, and the override flag, and the created item's data is returned

#### Scenario: Upload failure is a typed error
- **WHEN** an upload is answered with a non-2xx status carrying the Joomla error envelope
- **THEN** a typed API error is raised carrying the status and the server's error entries

### Requirement: Listing passes through API filters and ordering
List requests SHALL accept the content API's filter and ordering query parameters (such as `filter[category]`, `filter[state]`, `filter[search]`, `list[ordering]`, `list[direction]`) and SHALL forward them to the API without transforming them.

#### Scenario: Category filter is forwarded
- **WHEN** articles are listed with a category filter
- **THEN** the request carries the corresponding `filter[category]` query parameter

#### Scenario: Ordering is forwarded
- **WHEN** articles are listed with an ordering field and direction
- **THEN** the request carries the corresponding `list[ordering]` and `list[direction]` query parameters

### Requirement: The payload carries title, alias, and category
The mapping from a converted article to a create payload SHALL set `title` from the article title, `alias` from the article slug, and `catid` from the article's category, and SHALL map an unset article category (sentinel `0`) to the settings' default category.

#### Scenario: Title, alias, and category are mapped
- **WHEN** a payload is built for an article with a set category
- **THEN** the payload's `title` is the article title, its `alias` is the article slug, and its `catid` is the article's category

#### Scenario: Unset category falls back to the default
- **WHEN** a payload is built for an article whose category is the unset sentinel
- **THEN** the payload's `catid` is the settings' default category

### Requirement: The article body goes into a single body field
The mapping SHALL send the entire article body in a single body field: the whole body in `introtext` and an empty `fulltext`, so that no read-more split is implied. The body's image references SHALL be the corrected references to the uploaded media. The deprecated `articletext` field SHALL NOT be used. Live verification confirmed `introtext` is accepted on create and persists; the API exposes the stored body as the `text` attribute on read.

#### Scenario: Body is placed in the single body field
- **WHEN** a payload is built for an article with a non-empty body
- **THEN** the payload's `introtext` is the full article body, with its image references corrected to the uploaded media, and its `fulltext` is empty

#### Scenario: The deprecated field is not used
- **WHEN** a payload is built for any article
- **THEN** the payload does not contain an `articletext` field

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

### Requirement: Article metadata is carried into the payload
The mapping SHALL carry the article's author alias (`created_by_alias`), metadata description (`metadesc`), metadata keywords (`metakey`), and creation date (`created`) into the create payload, and SHALL set a `language` (the target site rejects creates without one; how that value is resolved is a separate concern).

#### Scenario: Author is carried
- **WHEN** a payload is built for an article with an extracted author
- **THEN** the payload's `created_by_alias` is that author

#### Scenario: Metadata is carried
- **WHEN** a payload is built for an article with a metadata description and keywords
- **THEN** the payload's `metadesc` and `metakey` are the article's values

#### Scenario: Creation date is carried
- **WHEN** a payload is built for an article with a creation date
- **THEN** the payload's `created` represents that date in a form the API accepts

### Requirement: API failures are surfaced as a typed error
A non-2xx API response carrying the Joomla error envelope (`{"errors": [...]}`) SHALL raise a typed API error carrying the HTTP status and the server-provided error entries. The client SHALL NOT retry failed requests automatically and SHALL NOT swallow them.

#### Scenario: Authentication failure
- **WHEN** a request is answered with 401 and a `Forbidden` error entry
- **THEN** a typed API error is raised carrying status 401 and the server's error entry

#### Scenario: Missing article
- **WHEN** an article is requested by an unknown ID
- **THEN** a typed API error with status 404 is raised

#### Scenario: Server failure
- **WHEN** a request is answered with a 5xx status
- **THEN** a typed API error carrying that status is raised and no automatic retry is attempted

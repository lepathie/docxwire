# cli Specification

## Purpose
The user-facing `docxwire` command: it takes a single `.docx` document and
publishes it to the configured Joomla site — converting the document,
uploading its images, and creating a draft article — and reports the outcome.

## Requirements

### Requirement: The command takes a single document path
The `docxwire` command SHALL accept exactly one positional argument: the path
to a `.docx` file. A missing argument, or a missing or unreadable file, SHALL
be reported as an actionable error and SHALL exit non-zero without
contacting the site.

#### Scenario: A single document path is accepted
- **WHEN** the command is invoked with one existing `.docx` path
- **THEN** the run proceeds with that document

#### Scenario: A missing argument is a usage error
- **WHEN** the command is invoked without a document path
- **THEN** a usage error is reported and the command exits non-zero

#### Scenario: A missing file is reported
- **WHEN** the command is invoked with a path that does not exist
- **THEN** an actionable error naming the file is reported and the command
  exits non-zero without contacting the site

### Requirement: Settings are loaded from the current working directory
The command SHALL load its settings from the `settings.toml` file in the
current working directory. A missing or invalid settings file SHALL be
reported with an actionable message and SHALL exit non-zero before any
conversion or network activity.

#### Scenario: The settings file in the working directory is used
- **WHEN** a `settings.toml` exists in the current working directory and the
  command is invoked with a valid document
- **THEN** the run uses that file's Joomla settings

#### Scenario: A missing settings file is reported
- **WHEN** no `settings.toml` exists in the current working directory
- **THEN** an actionable error pointing to the example settings file is
  reported and the command exits non-zero without contacting the site

### Requirement: A run publishes the document end to end
On a valid run the command SHALL convert the document, upload every image of
the converted article to the site, and create a single article carrying the
converted title, body, metadata, and review note. All of the article's images
SHALL be uploaded, and the images SHALL be uploaded before the article is
created, so that the created article's body references resolve. The created
article SHALL be left in the site's default state (draft).

#### Scenario: A successful run creates the article
- **WHEN** the command is invoked with a valid document and a valid settings
  file
- **THEN** every image of the converted article is uploaded and one article
  is created carrying the converted title, body, and metadata

#### Scenario: Images are uploaded before the article
- **WHEN** a run uploads the article's images and creates the article
- **THEN** every image upload completes before the article create request is
  sent

#### Scenario: The created article is a draft
- **WHEN** a run creates the article
- **THEN** the article is left in the site's default state (draft), the
  create payload carrying no explicit state

### Requirement: Image paths are derived from the article
Each image SHALL be uploaded to `images/articles/<YYYY>/<MM>/<slug>/<filename>`
on the site, where `<filename>` is the media file's basename (no directory
components — in particular, no pandoc `media/` extraction prefix), `<slug>`
is the article's slug, and `<YYYY>/<MM>` is the article's folder date. The
article body's image references SHALL point to the corresponding
site-relative uploaded paths.

#### Scenario: The slug date drives the path
- **WHEN** an article with the slug `adams-acht-2026-09` and a dateless
  title is published
- **THEN** its images are uploaded under `images/articles/2026/09/<slug>/…`
  and its body references the corresponding site-relative paths

#### Scenario: A media extraction prefix is not part of the path
- **WHEN** an article's image has the media file name `media/image1.jpeg`
- **THEN** it is uploaded under `images/articles/<YYYY>/<MM>/<slug>/image1.jpeg`
  with no `media` component, and the body reference points to that path

#### Scenario: A dateless slug falls back to the created date
- **WHEN** an article whose slug has no date suffix and whose created date
  is in March 2026 is published
- **THEN** its images are uploaded under `images/articles/2026/03/<slug>/…`

#### Scenario: A missing created date falls back to the current date
- **WHEN** an article with a dateless slug and no created date is
  published
- **THEN** its images are uploaded under the current date's
  `images/articles/<YYYY>/<MM>/…` path

### Requirement: A successful run reports the created article
On success the command SHALL report the created article's id and the
article's review note — the `Prüfe: …` line when items need review, and an
indication that nothing needs review when the note is empty — and SHALL exit
0.

#### Scenario: The id and note are reported
- **WHEN** a run creates an article whose note is `Prüfe: Titel`
- **THEN** the output carries the created article's id and the note line and
  the command exits 0

#### Scenario: A clean article is reported as clean
- **WHEN** a run creates an article with an empty note
- **THEN** the output carries the created article's id and indicates that
  nothing needs review, and the command exits 0

### Requirement: Failures stop the run without publishing
When settings loading, conversion, an image upload, the article creation,
or the payload build fails, the command SHALL report an actionable error
and SHALL exit non-zero, and no article SHALL be created for the run.

#### Scenario: An image upload failure stops the run
- **WHEN** an image upload fails with an API error
- **THEN** the error is reported, the command exits non-zero, and no article
  is created

#### Scenario: A conversion failure stops the run
- **WHEN** converting the document fails
- **THEN** an actionable error is reported, the command exits non-zero, and
  no image is uploaded and no article is created

#### Scenario: A payload-build failure stops the run
- **WHEN** building the article payload fails (for example a body image
  reference matches no uploaded image)
- **THEN** an actionable error is reported, the command exits non-zero, and
  no article is created

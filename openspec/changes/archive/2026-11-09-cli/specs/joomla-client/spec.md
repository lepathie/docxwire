# Spec Delta

## MODIFIED Requirements

### Requirement: The payload's body image references point to uploaded media
The mapping SHALL rewrite every `<img>` reference in the article body from
the image's local media filename to that image's uploaded site-relative
path, matched by the media file's basename. Building the payload SHALL
fail when any image referenced in the body has no matching image with an
uploaded path.

#### Scenario: Body references are rewritten
- **WHEN** a payload is built for an article whose body references an image
  that has an uploaded path
- **THEN** the body's `<img>` reference for that image is the uploaded
  site-relative path

#### Scenario: A path-carrying reference is matched by basename
- **WHEN** a payload is built for an article whose body references an image
  by a path-carrying reference (for example an absolute path into the
  temporary media-extraction directory) and the referenced media file has
  an uploaded path
- **THEN** the reference is matched to the image by its file name and
  rewritten to the uploaded site-relative path

#### Scenario: Unuploaded body image fails the build
- **WHEN** a payload is built for an article whose body references a file
  name that matches no image with an uploaded path
- **THEN** the payload build fails with an error and no payload is produced

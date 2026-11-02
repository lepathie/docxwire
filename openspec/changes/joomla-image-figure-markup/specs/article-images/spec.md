# Spec Delta

## ADDED Requirements

### Requirement: In-body image markup matches the site's figure conventions
Every in-body image SHALL be wrapped in a `figure` element carrying `class="image align-center"`, and its `img` element SHALL carry `loading="lazy"` and no other styling: no `class`, `style`, `width`, or `height` attributes. This applies to in-body images with and without a caption line.

#### Scenario: In-body image with a caption line
- **WHEN** an in-body image has a caption line directly below it
- **THEN** the article body contains a `figure` with `class="image align-center"` wrapping an `img` with `loading="lazy"` and a `figcaption` carrying the caption text

#### Scenario: In-body image without a caption line
- **WHEN** an in-body image has no caption line directly below it
- **THEN** the article body contains a `figure` with `class="image align-center"` wrapping an `img` with `loading="lazy"` and no `figcaption`

#### Scenario: Styling attributes on the source img are stripped
- **WHEN** the source markup of an in-body image carries `class`, `style`, `width`, or `height` attributes
- **THEN** the `img` in the article body carries none of those attributes, only `src` and `loading="lazy"`

#### Scenario: The img keeps its src
- **WHEN** an in-body image is wrapped in a figure
- **THEN** the `img` element in the article body carries the image's `src` attribute

#### Scenario: Lead images are not wrapped
- **WHEN** a leading image is removed from the article body
- **THEN** no figure element for that image appears in the article body

## MODIFIED Requirements

### Requirement: In-body images are preserved
Image elements that appear after the first heading SHALL remain in the article body and SHALL NOT be marked as lead. When an in-body image has a caption line directly below it, the image and its caption line SHALL be rewritten in the article body as a figure containing the image and a figcaption containing the caption text. An in-body image without a caption line SHALL likewise be rewritten in the article body as a figure containing the image.

#### Scenario: Image after the heading stays in the body
- **WHEN** the document body contains an image after the first heading
- **THEN** that image remains in the article body and its `is_lead` is `false`

#### Scenario: Mixed leading and in-body images
- **WHEN** the document body contains one image before the first heading and one image after it
- **THEN** the first image is removed from the body and flagged `is_lead = true`, and the second image remains in the body with `is_lead = false`

#### Scenario: In-body image with a caption line becomes a figure
- **WHEN** an in-body image has a line of text directly below it
- **THEN** the article body contains a figure wrapping that image and a figcaption carrying the caption text, and the original plain caption paragraph is no longer present in the body

#### Scenario: In-body image without a caption line becomes a figure
- **WHEN** an in-body image has no line of text directly below it
- **THEN** the article body contains a figure wrapping that image without a figcaption, and the image is not left as a bare img element

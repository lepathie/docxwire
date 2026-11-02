# Spec Delta

## ADDED Requirements

### Requirement: Image captions are captured on article images
The caption of an image — the line of text directly below it, usually carrying the `Bildunterschrift` paragraph style — SHALL be captured in the `caption` field of the corresponding entry in the article's image list, matched by the image's source filename. Detection SHALL be positional (next block in document order being a non-heading text paragraph) and SHALL NOT require the `Bildunterschrift` style.

#### Scenario: Lead image caption is captured
- **WHEN** a leading image (before the first heading) has a line of text directly below it and is removed from the body
- **THEN** the corresponding image entry carries that line's text in its `caption` field

#### Scenario: In-body image caption is captured
- **WHEN** an in-body image (after the first heading) has a line of text directly below it
- **THEN** the corresponding image entry carries that line's text in its `caption` field

#### Scenario: Caption line without the Bildunterschrift style
- **WHEN** the line directly below an image is a text paragraph that does not carry the `Bildunterschrift` style
- **THEN** it is still captured as that image's caption

#### Scenario: Image without a caption line
- **WHEN** the next block in document order after an image is not a text paragraph (for example a heading or another image)
- **THEN** the image's `caption` field remains empty

### Requirement: Guessed captions are flagged in the article note
When a captured caption line does not carry the `Bildunterschrift` paragraph style, the converter is guessing what the caption is. The article's `note` field SHALL then flag this concisely: a single short line naming each affected image by its media filename and stating that its caption was captured without the `Bildunterschrift` style. The note SHALL NOT contain the caption text or line breaks.

#### Scenario: In-body guessed caption is flagged
- **WHEN** an in-body image's caption line does not carry the `Bildunterschrift` style
- **THEN** the caption is captured and the article's `note` is a single concise line naming the image by its media filename

#### Scenario: Lead guessed caption is flagged
- **WHEN** a leading image's caption line does not carry the `Bildunterschrift` style
- **THEN** the caption is captured and the article's `note` names the image by its media filename

#### Scenario: Multiple guessed captions share one concise line
- **WHEN** two images have caption lines without the `Bildunterschrift` style
- **THEN** the article's `note` names both images in a single line without line breaks

#### Scenario: Styled caption is not flagged
- **WHEN** a captured caption line carries the `Bildunterschrift` style
- **THEN** the article's `note` is not modified for that image

## MODIFIED Requirements

### Requirement: Leading images are removed from the article body
When converting a document, any image element that appears in the article body before the first heading SHALL be removed from the resulting article body, together with the image's caption line (the line of text directly below the image). The removal leaves no empty paragraph shell or orphaned caption text in the body. The removal is anchored on the first heading; when no heading is present, no image is treated as leading.

#### Scenario: Single image before the heading
- **WHEN** the document body contains one image before the first heading
- **THEN** that image is removed from the article body

#### Scenario: Multiple images before the heading
- **WHEN** the document body contains two or more images before the first heading
- **THEN** all of those images are removed from the article body

#### Scenario: No image before the heading
- **WHEN** the document body has no image before the first heading
- **THEN** no image is removed from the body and no image is marked as lead

#### Scenario: No heading present
- **WHEN** the document body contains images but no heading
- **THEN** no image is treated as leading and the body is left unchanged with respect to images

#### Scenario: Lead image with a caption line
- **WHEN** a leading image has a line of text directly below it
- **THEN** both the image and that caption line are removed from the article body and no empty paragraph or orphaned caption text remains in the body

### Requirement: In-body images are preserved
Image elements that appear after the first heading SHALL remain in the article body and SHALL NOT be marked as lead. When an in-body image has a caption line directly below it, the image and its caption line SHALL be rewritten in the article body as a figure containing the image and a figcaption containing the caption text.

#### Scenario: Image after the heading stays in the body
- **WHEN** the document body contains an image after the first heading
- **THEN** that image remains in the article body and its `is_lead` is `false`

#### Scenario: Mixed leading and in-body images
- **WHEN** the document body contains one image before the first heading and one image after it
- **THEN** the first image is removed from the body and flagged `is_lead = true`, and the second image remains in the body with `is_lead = false`

#### Scenario: In-body image with a caption line becomes a figure
- **WHEN** an in-body image has a line of text directly below it
- **THEN** the article body contains a figure wrapping that image and a figcaption carrying the caption text, and the original plain caption paragraph is no longer present in the body

#### Scenario: In-body image without a caption line stays unchanged
- **WHEN** an in-body image has no line of text directly below it
- **THEN** the image remains in the article body in its original markup, without a figure wrapper

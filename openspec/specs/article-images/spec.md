# article-images Specification

## Purpose

Defines how the article converter treats images: which images count as "lead" (those appearing before the first heading), how they are removed from the body, and how they are flagged so downstream publishing can distinguish lead imagery from in-body imagery.

## Requirements

### Requirement: Leading images are removed from the article body
When converting a document, any image element that appears in the article body before the first heading SHALL be removed from the resulting article body. The removal is anchored on the first heading; when no heading is present, no image is treated as leading.

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

### Requirement: Leading images are flagged as lead
Each leading image removed from the body SHALL be marked with `is_lead = true` on the corresponding entry in the article's image list, matched by the image's source.

#### Scenario: Lead image is flagged
- **WHEN** a leading image is removed from the body and a corresponding extracted image exists
- **THEN** that image's `is_lead` is set to `true`

#### Scenario: Multiple leading images are all flagged
- **WHEN** two leading images are removed from the body and both have corresponding extracted images
- **THEN** both images' `is_lead` is set to `true`

### Requirement: In-body images are preserved
Image elements that appear after the first heading SHALL remain in the article body and SHALL NOT be marked as lead.

#### Scenario: Image after the heading stays in the body
- **WHEN** the document body contains an image after the first heading
- **THEN** that image remains in the article body and its `is_lead` is `false`

#### Scenario: Mixed leading and in-body images
- **WHEN** the document body contains one image before the first heading and one image after it
- **THEN** the first image is removed from the body and flagged `is_lead = true`, and the second image remains in the body with `is_lead = false`

### Requirement: Lead image must map to an extracted local image
A leading image removed from the body SHALL correspond to an extracted local media file. If a detected leading image cannot be matched to an extracted local media file, the conversion SHALL fail with an error.

#### Scenario: Lead image with no local file fails conversion
- **WHEN** a detected leading image has no matching extracted local media file
- **THEN** the conversion fails with an error

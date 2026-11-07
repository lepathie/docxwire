# article-metadata Specification

## Purpose

Defines how the article converter extracts and attaches article metadata — the author and the creation date — from a `.docx` source during conversion, and how a missing author or creation date is surfaced to downstream publishing.

## Requirements

### Requirement: Author is taken from the "Autor" line
The article's author SHALL be the text of the body line that carries the "Autor" style, with any leading `Autor:` label removed. If the document contains more than one "Autor" line, the last one in document order SHALL be used.

#### Scenario: Single "Autor" line yields the author
- **WHEN** the body contains a line styled "Autor" with the text `Bernhard M.`
- **THEN** the article author is `Bernhard M.`

#### Scenario: "Autor:" label is stripped
- **WHEN** the "Autor" line text is `Autor: Bernhard M.`
- **THEN** the article author is `Bernhard M.`

#### Scenario: Multiple "Autor" lines use the last
- **WHEN** the body contains two "Autor" lines, `First A.` followed by `Second B.`
- **THEN** the article author is `Second B.`

### Requirement: Multiple "Autor" lines are flagged in the note
When the document contains more than one "Autor" line, the converter SHALL use the last one (in document order) as the author and SHALL contribute the `Autor` item to the note.

#### Scenario: Multiple "Autor" lines flag the anomaly
- **WHEN** the body contains two "Autor" lines, `First A.` followed by `Second B.`
- **THEN** the article author is `Second B.` and the note includes the `Autor` item

### Requirement: Extracted author is attached to the article
When an author is determined, it SHALL be stored in `Article.created_by_alias`.

#### Scenario: Author stored on the article
- **WHEN** an author is extracted from the "Autor" line
- **THEN** `Article.created_by_alias` equals that author

### Requirement: The "Autor" line is removed from the body
The body line that carries the "Autor" style SHALL be removed from the resulting article body.

#### Scenario: "Autor" line removed from body
- **WHEN** the body contains an "Autor" line
- **THEN** that line is not present in the resulting article body

### Requirement: A missing author is recorded in the note
When no author can be determined — because there is no "Autor" line, or the line is empty after the label is removed — the converter SHALL contribute the `Autor` item to the note and SHALL NOT set `Article.created_by_alias`.

#### Scenario: No "Autor" line records the missing author
- **WHEN** the body contains no "Autor" line
- **THEN** the note includes the `Autor` item and `Article.created_by_alias` is left empty

#### Scenario: Empty "Autor" line records the missing author
- **WHEN** the "Autor" line is empty after removing the `Autor:` label
- **THEN** the note includes the `Autor` item and `Article.created_by_alias` is left empty

### Requirement: Creation date is read from the document
The article's creation date SHALL be taken from the source document's creation timestamp and stored in `Article.created_date`.

#### Scenario: Creation date stored on the article
- **WHEN** the source document has a creation timestamp of 26 April 2025, 17:52:00 UTC
- **THEN** `Article.created_date` is set to a value representing that timestamp

### Requirement: A missing creation date is recorded in the note
When the source document has no creation timestamp, `Article.created_date` SHALL be left empty, the `Erstellungsdatum` item SHALL be contributed to the note, and the conversion SHALL NOT fail.

#### Scenario: No creation timestamp
- **WHEN** the source document has no creation timestamp
- **THEN** `Article.created_date` is empty, the note includes the `Erstellungsdatum` item, and the conversion succeeds

### Requirement: A missing heading is recorded as a title item
When the document contains no heading and the article title falls back to the source file name, the converter SHALL contribute the `Titel` item to the note.

#### Scenario: No heading records the title item
- **WHEN** the document body contains no heading
- **THEN** the article title is the source file name and the note includes the `Titel` item

#### Scenario: A present heading records no title item
- **WHEN** the document body contains a heading
- **THEN** the note includes no `Titel` item

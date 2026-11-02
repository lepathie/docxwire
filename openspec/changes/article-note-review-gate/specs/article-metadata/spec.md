# Spec Delta

## ADDED Requirements

### Requirement: A missing heading is recorded as a title item
When the document contains no heading and the article title falls back to the source file
name, the converter SHALL contribute the `Titel` item to the note.

#### Scenario: No heading records the title item
- **WHEN** the document body contains no heading
- **THEN** the article title is the source file name and the note includes the `Titel` item

#### Scenario: A present heading records no title item
- **WHEN** the document body contains a heading
- **THEN** the note includes no `Titel` item

## MODIFIED Requirements

### Requirement: Multiple "Autor" lines are flagged in the note
When the document contains more than one "Autor" line, the converter SHALL use the last one
(in document order) as the author and SHALL contribute the `Autor` item to the note.

#### Scenario: Multiple "Autor" lines flag the anomaly
- **WHEN** the body contains two "Autor" lines, `First A.` followed by `Second B.`
- **THEN** the article author is `Second B.` and the note includes the `Autor` item

### Requirement: A missing author is recorded in the note
When no author can be determined — because there is no "Autor" line, or the line is empty
after the label is removed — the converter SHALL contribute the `Autor` item to the note and
SHALL NOT set `Article.created_by_alias`.

#### Scenario: No "Autor" line records the missing author
- **WHEN** the body contains no "Autor" line
- **THEN** the note includes the `Autor` item and `Article.created_by_alias` is left empty

#### Scenario: Empty "Autor" line records the missing author
- **WHEN** the "Autor" line is empty after removing the `Autor:` label
- **THEN** the note includes the `Autor` item and `Article.created_by_alias` is left empty

### Requirement: A missing creation date is recorded in the note
When the source document has no creation timestamp, `Article.created_date` SHALL be left
empty, the `Erstellungsdatum` item SHALL be contributed to the note, and the conversion SHALL
NOT fail.

#### Scenario: No creation timestamp
- **WHEN** the source document has no creation timestamp
- **THEN** `Article.created_date` is empty, the note includes the `Erstellungsdatum` item, and
the conversion succeeds

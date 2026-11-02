# Spec Delta

## MODIFIED Requirements

### Requirement: Guessed captions are flagged in the article note
When a captured caption line does not carry the `Bildunterschrift` paragraph style, the
converter is guessing what the caption is. The note SHALL then reference each affected image
positionally — an in-body image by its document-order ordinal and a lead image by its
lead-slot label — instead of by its media filename. The note SHALL NOT contain the caption
text or line breaks.

#### Scenario: In-body guessed caption is flagged
- **WHEN** an in-body image's caption line does not carry the `Bildunterschrift` style
- **THEN** the caption is captured and the note references the image by its in-body ordinal

#### Scenario: Lead guessed caption is flagged
- **WHEN** a leading image's caption line does not carry the `Bildunterschrift` style
- **THEN** the caption is captured and the note references the image by its lead-slot label

#### Scenario: Multiple guessed captions share one concise line
- **WHEN** two images have caption lines without the `Bildunterschrift` style
- **THEN** the note references both images positionally in a single line without line breaks

#### Scenario: Styled caption is not flagged
- **WHEN** a captured caption line carries the `Bildunterschrift` style
- **THEN** the note is not modified for that image

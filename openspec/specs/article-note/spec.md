# article-note Specification

## Purpose

Defines the publisher review note on an article: a compact, single-line, German, actionable
prompt that tells the publisher what to verify before publishing, and whose emptiness signals
a clean article.

## Requirements

### Requirement: The note is a single-line German review prompt
The article's note SHALL be a single line of German text. When one or more issues require
review, it SHALL begin with the prefix `Prüfe:` followed by the comma-separated items to
check. When no issue requires review, the note SHALL be empty. The note SHALL NOT contain
line breaks.

#### Scenario: Clean article yields an empty note
- **WHEN** no issue requires review
- **THEN** the note is empty

#### Scenario: A single issue yields a prompted line
- **WHEN** exactly one issue requires review
- **THEN** the note is `Prüfe: <item>`

#### Scenario: Multiple issues are listed on one line
- **WHEN** two or more issues require review
- **THEN** the note is `Prüfe: <item1>, <item2>, …` on a single line

#### Scenario: The note never contains line breaks
- **WHEN** the note is non-empty
- **THEN** it contains no line breaks

### Requirement: Note items are de-duplicated and stably ordered
Each distinct issue SHALL contribute a short German item label. The builder SHALL
de-duplicate identical items and SHALL order items in a fixed sequence, independent of the
order in which the issues were detected.

#### Scenario: A repeated issue contributes one item
- **WHEN** the same issue is detected more than once
- **THEN** its item appears once in the note

#### Scenario: Items appear in a fixed order
- **WHEN** two issues are detected in either relative order
- **THEN** their items appear in the same fixed sequence

### Requirement: The note length is designed for, not enforced
The note SHALL be kept short through terse item labels and positional image references. The
system SHALL NOT truncate or elide the note to satisfy a hard character limit.

#### Scenario: Many affected images are all listed
- **WHEN** many in-body images have guessed captions
- **THEN** every one is referenced positionally and none is replaced by a count or ellipsis

### Requirement: An empty note means nothing to review
The note SHALL be empty if and only if no review condition holds. Every condition that leaves
article data as a best-guess or fallback — a missing author, a missing creation date, a
guessed caption, or a title derived from the file name — SHALL contribute a note item.

#### Scenario: A filename-derived title is not silent
- **WHEN** the title fell back to the source file name and no other issue holds
- **THEN** the note is `Prüfe: Titel`

#### Scenario: No conditions yields an empty note
- **WHEN** no review condition holds
- **THEN** the note is empty

### Requirement: In-body images are referenced by a condensed ordinal
When one or more in-body images have guessed captions, the note SHALL reference them by their
ordinal position among in-body images in document order, not by media filename. Multiple
ordinals are condensed to a single shared `Bild`: the numbers are listed ascending and joined
with `, ` and an `& ` before the last (e.g. `1. & 2. Bild`, `1., 2. & 3. Bild`). Non-contiguous
ordinals keep their own numbers.

#### Scenario: A single in-body image is referenced
- **WHEN** exactly one in-body image has a guessed caption
- **THEN** the note references it as `1. Bild`

#### Scenario: Two in-body images are condensed
- **WHEN** the first and second in-body images have guessed captions
- **THEN** the note references them as `1. & 2. Bild`

#### Scenario: Three in-body images are condensed
- **WHEN** the first, second, and third in-body images have guessed captions
- **THEN** the note references them as `1., 2. & 3. Bild`

#### Scenario: Non-contiguous ordinals keep their numbers, sorted
- **WHEN** the first and third in-body images (but not the second) have guessed captions
- **THEN** the note references them as `1. & 3. Bild`

### Requirement: Lead images are referenced by lead-slot label
When a lead image's caption is a guessed item, the note SHALL reference it by its lead-slot
label. While lead-slot assignment does not yet exist, a single generic placeholder label SHALL
be used for every lead image; once assignment exists, the label SHALL be the image's assigned
slot.

#### Scenario: A lead image is referenced by the placeholder label
- **WHEN** a lead image has a guessed caption and slot assignment does not yet exist
- **THEN** the note references it by the generic placeholder label

#### Scenario: A lead image is referenced by its assigned slot
- **WHEN** a lead image has a guessed caption and is assigned a lead slot
- **THEN** the note references it by that slot's label

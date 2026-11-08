# Spec Delta

## MODIFIED Requirements

### Requirement: Article metadata is carried into the payload
The mapping SHALL carry the article's author alias (`created_by_alias`), metadata description (`metadesc`), metadata keywords (`metakey`), and creation date (`created`) into the create payload, and SHALL set the payload's `language` to the article's language when the article carries one (the `Article` carries an optional `language` field, empty when unset), otherwise to the Joomla settings' `default_language`, and otherwise to the all-languages sentinel `*`.

#### Scenario: Author is carried
- **WHEN** a payload is built for an article with an extracted author
- **THEN** the payload's `created_by_alias` is that author

#### Scenario: Metadata is carried
- **WHEN** a payload is built for an article with a metadata description and keywords
- **THEN** the payload's `metadesc` and `metakey` are the article's values

#### Scenario: Creation date is carried
- **WHEN** a payload is built for an article with a creation date
- **THEN** the payload's `created` represents that date in a form the API accepts

#### Scenario: The article's language wins
- **WHEN** a payload is built for an article whose language is `de-DE`
- **THEN** the payload's `language` is `de-DE`

#### Scenario: The settings' default_language is used when the article has none
- **WHEN** a payload is built for an article without a language and the settings' `default_language` is `de-DE`
- **THEN** the payload's `language` is `de-DE`

#### Scenario: The sentinel is used when neither is set
- **WHEN** a payload is built for an article without a language and the settings' `default_language` is `*`
- **THEN** the payload's `language` is `*`

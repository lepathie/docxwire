# Spec Delta

## MODIFIED Requirements

### Requirement: An example settings file is committed
The repository SHALL provide a `settings.toml.example` file at the repository root containing a `[joomla]` section that documents every supported key — `base_url`, `base_path`, `token`, `default_catid`, and `language` — with placeholder values, and SHALL NOT contain real credentials. The `base_path` placeholder SHALL be the Joomla 5 API path shape `/api/index.php/v1`, and the `language` placeholder SHALL be the all-languages sentinel `*`.

#### Scenario: Example documents all keys
- **WHEN** a developer inspects `settings.toml.example`
- **THEN** the `[joomla]` section lists `base_url`, `base_path`, `token`, `default_catid`, and `language`, each with a placeholder value, `base_path` is `/api/index.php/v1`, and `language` is `*`

#### Scenario: Example carries no real secrets
- **WHEN** the example file is committed to the repository
- **THEN** it contains no real API token or other live credential

### Requirement: The joomla section is validated
The keys `base_url`, `base_path`, and `token` SHALL be required, and `default_catid` and `language` SHALL be optional with defaults of `0` and the all-languages sentinel `*` respectively. Loaded values SHALL have the expected types: strings for `base_url`, `base_path`, `token`, and `language`, and an integer for `default_catid`.

#### Scenario: Missing joomla section
- **WHEN** the file contains no `[joomla]` section
- **THEN** the loader raises a settings error naming the missing section

#### Scenario: Missing required key
- **WHEN** the `[joomla]` section lacks `token`
- **THEN** the loader raises a settings error naming `token`

#### Scenario: Optional catid defaults to zero
- **WHEN** the `[joomla]` section omits `default_catid`
- **THEN** the loaded settings carry `default_catid` of `0`

#### Scenario: Optional language defaults to all languages
- **WHEN** the `[joomla]` section omits `language`
- **THEN** the loaded settings carry `language` of `*`

#### Scenario: Wrong type for catid
- **WHEN** `default_catid` is not an integer
- **THEN** the loader raises a settings error

#### Scenario: Wrong type for language
- **WHEN** `language` is not a string
- **THEN** the loader raises a settings error

# Spec Delta

## MODIFIED Requirements

### Requirement: An example settings file is committed
The repository SHALL provide a `settings.toml.example` file at the repository root containing a `[joomla]` section that documents every supported key — `base_url`, `base_path`, `token`, `default_catid`, `basic_auth`, and `language` — with placeholder values, and SHALL NOT contain real credentials. The `basic_auth` entry SHALL include a short note explaining how to obtain the value, including base64-encoding a `username:password`. The `base_path` placeholder SHALL be the Joomla 5 API path shape `/api/index.php/v1`, and the `language` placeholder SHALL be the all-languages sentinel `*`.

#### Scenario: Example documents all keys
- **WHEN** a developer inspects `settings.toml.example`
- **THEN** the `[joomla]` section lists `base_url`, `base_path`, `token`, `default_catid`, `basic_auth`, and `language`, each with a placeholder value, `base_path` is `/api/index.php/v1`, and `language` is `*`

#### Scenario: Example explains the Basic Auth value
- **WHEN** a developer reads the `basic_auth` entry in `settings.toml.example`
- **THEN** it explains how to obtain the value, including base64-encoding a `username:password` pair

#### Scenario: Example carries no real secrets
- **WHEN** the example file is committed to the repository
- **THEN** it contains no real API token or other live credential

### Requirement: The joomla section is validated
The keys `base_url`, `base_path`, and `token` SHALL be required, `default_catid` SHALL be optional with a default of `0`, `language` SHALL be optional with a default of the all-languages sentinel `*`, and `basic_auth` SHALL be optional with no default (unset when omitted). Loaded values SHALL have the expected types: strings for `base_url`, `base_path`, `token`, `basic_auth`, and `language`, and an integer for `default_catid`.

#### Scenario: Missing joomla section
- **WHEN** the file contains no `[joomla]` section
- **THEN** the loader raises a settings error naming the missing section

#### Scenario: Missing required key
- **WHEN** the `[joomla]` section lacks `token`
- **THEN** the loader raises a settings error naming `token`

#### Scenario: Optional catid defaults to zero
- **WHEN** the `[joomla]` section omits `default_catid`
- **THEN** the loaded settings carry `default_catid` of `0`

#### Scenario: Optional basic_auth defaults to unset
- **WHEN** the `[joomla]` section omits `basic_auth`
- **THEN** the loaded settings carry no Basic Auth value

#### Scenario: Optional language defaults to all languages
- **WHEN** the `[joomla]` section omits `language`
- **THEN** the loaded settings carry `language` of `*`

#### Scenario: Wrong type for catid
- **WHEN** `default_catid` is not an integer
- **THEN** the loader raises a settings error

#### Scenario: Wrong type for basic_auth
- **WHEN** `basic_auth` is present but not a string
- **THEN** the loader raises a settings error

#### Scenario: Wrong type for language
- **WHEN** `language` is not a string
- **THEN** the loader raises a settings error

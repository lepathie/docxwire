# settings Specification

## Purpose

Defines how DOCxWIRE stores and reads per-environment configuration: a committed example file, a gitignored customization file, and the contract for loading and validating the `[joomla]` section from it.

## Requirements

### Requirement: An example settings file is committed
The repository SHALL provide a `settings.toml.example` file at the repository root containing a `[joomla]` section that documents every supported key — `base_url`, `base_path`, `token`, `default_catid`, and the optional `basic_auth` — with placeholder values, and SHALL NOT contain real credentials.

#### Scenario: Example documents all keys
- **WHEN** a developer inspects `settings.toml.example`
- **THEN** the `[joomla]` section lists `base_url`, `base_path`, `token`, `default_catid`, and `basic_auth`, each with a placeholder value, and `base_path` is `/api/index.php/v1`

#### Scenario: Example explains the Basic Auth value
- **WHEN** a developer reads the `basic_auth` entry in `settings.toml.example`
- **THEN** it explains how to obtain the value, including base64-encoding a `username:password` pair

#### Scenario: Example carries no real secrets
- **WHEN** the example file is committed to the repository
- **THEN** it contains no real API token or other live credential

### Requirement: The example explains the Basic Auth value
The `basic_auth` entry in `settings.toml.example` SHALL include a short note explaining how to obtain the value, including base64-encoding a `username:password` pair.

#### Scenario: Example explains the Basic Auth value
- **WHEN** a developer reads the `basic_auth` entry in `settings.toml.example`
- **THEN** it explains how to obtain the value, including base64-encoding a `username:password` pair

### Requirement: The example pins the Joomla 5 base_path
The `base_path` placeholder in `settings.toml.example` SHALL be the Joomla 5 API path shape `/api/index.php/v1`.

#### Scenario: Example pins the Joomla 5 base_path
- **WHEN** a developer inspects the `base_path` entry in `settings.toml.example`
- **THEN** it is `/api/index.php/v1`

### Requirement: The custom settings file is gitignored
`settings.toml` SHALL be listed in the repository's `.gitignore` so that custom values, including the API token, are never committed.

#### Scenario: Settings file is not tracked
- **WHEN** a developer creates `settings.toml` in the repository root
- **THEN** git reports the file as ignored

### Requirement: Settings are read from a TOML file
The settings loader SHALL read configuration from a TOML file, using `settings.toml` in the current working directory by default and an explicitly supplied path when given, and SHALL surface the values of the `[joomla]` section in the returned settings.

#### Scenario: Default path is used
- **WHEN** the loader is invoked without a path and `settings.toml` exists in the working directory
- **THEN** the settings are read from that file

#### Scenario: Explicit path is honored
- **WHEN** the loader is invoked with an explicit path
- **THEN** the settings are read from the file at that path

#### Scenario: Values are preserved
- **WHEN** a file whose `[joomla]` section sets `base_url`, `base_path`, `token`, and `default_catid` is loaded
- **THEN** the returned settings carry exactly those values

### Requirement: The joomla section is validated
The keys `base_url`, `base_path`, and `token` SHALL be required, `default_catid` SHALL be optional with a default of `0`, and `basic_auth` SHALL be optional with no default (unset when omitted). Loaded values SHALL have the expected types: strings for `base_url`, `base_path`, `token`, and `basic_auth`, and an integer for `default_catid`.

#### Scenario: Missing joomla section
- **WHEN** the file contains no `[joomla]` section
- **THEN** the loader raises a settings error naming the missing section

#### Scenario: Missing required key
- **WHEN** the `[joomla]` section lacks `token`
- **THEN** the loader raises a settings error naming `token`

#### Scenario: Optional catid defaults to zero
- **WHEN** the `[joomla]` section omits `default_catid`
- **THEN** the loaded settings carry `default_catid` of `0`

#### Scenario: Wrong type for catid
- **WHEN** `default_catid` is not an integer
- **THEN** the loader raises a settings error

#### Scenario: Optional basic_auth defaults to unset
- **WHEN** the `[joomla]` section omits `basic_auth`
- **THEN** the loaded settings carry no Basic Auth value

#### Scenario: Wrong type for basic_auth
- **WHEN** `basic_auth` is present but not a string
- **THEN** the loader raises a settings error

### Requirement: A missing or malformed file produces an actionable error
When the settings file does not exist, the loader SHALL raise a settings error that directs the user to create it from `settings.toml.example`. When the file is not valid TOML, the loader SHALL raise a settings error rather than letting the underlying parse failure propagate.

#### Scenario: Missing file points at the example
- **WHEN** the loader is invoked without a path and no `settings.toml` exists in the working directory
- **THEN** it raises a settings error referencing `settings.toml.example`

#### Scenario: Malformed TOML is wrapped
- **WHEN** the settings file contains invalid TOML
- **THEN** the loader raises a settings error, not the raw parse exception

### Requirement: Conversion works without settings
Document conversion SHALL succeed in a working directory that has no `settings.toml`; reading settings SHALL be required only by the publishing step, not by conversion.

#### Scenario: Convert with no settings file
- **WHEN** the converter runs in a working directory without `settings.toml`
- **THEN** the conversion succeeds

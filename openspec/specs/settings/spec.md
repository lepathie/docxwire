# settings Specification

## Purpose

Defines how DOCxWIRE stores and reads per-environment configuration: a committed example file, a gitignored customization file, and the contract for loading and validating the `[joomla]` section from it.

## Requirements

### Requirement: An example settings file is committed
The repository SHALL provide a `settings.toml.example` file at the repository root containing a `[joomla]` section that documents every supported key — `base_url`, `base_path`, `token`, and `default_catid` — with placeholder values, and SHALL NOT contain real credentials.

#### Scenario: Example documents all keys
- **WHEN** a developer inspects `settings.toml.example`
- **THEN** the `[joomla]` section lists `base_url`, `base_path`, `token`, and `default_catid`, each with a placeholder value

#### Scenario: Example carries no real secrets
- **WHEN** the example file is committed to the repository
- **THEN** it contains no real API token or other live credential

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
The keys `base_url`, `base_path`, and `token` SHALL be required, and `default_catid` SHALL be optional with a default of `0`. Loaded values SHALL have the expected types: strings for `base_url`, `base_path`, and `token`, and an integer for `default_catid`.

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

# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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

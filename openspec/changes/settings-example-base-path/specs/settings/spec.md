# Spec Delta

## MODIFIED Requirements

### Requirement: An example settings file is committed
The repository SHALL provide a `settings.toml.example` file at the repository root containing a `[joomla]` section that documents every supported key — `base_url`, `base_path`, `token`, and `default_catid` — with placeholder values, and SHALL NOT contain real credentials. The `base_path` placeholder SHALL be the Joomla 5 API path shape `/api/index.php/v1`.

#### Scenario: Example documents all keys
- **WHEN** a developer inspects `settings.toml.example`
- **THEN** the `[joomla]` section lists `base_url`, `base_path`, `token`, and `default_catid`, each with a placeholder value, and `base_path` is `/api/index.php/v1`

#### Scenario: Example carries no real secrets
- **WHEN** the example file is committed to the repository
- **THEN** it contains no real API token or other live credential

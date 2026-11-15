# Spec Delta

## ADDED Requirements

### Requirement: Settings can be loaded from environment variables
The settings module SHALL provide an environment-based loader that reads the Joomla settings from the `DOXXWIRE_JOOMLA_*` environment variables — `DOXXWIRE_JOOMLA_BASE_URL`, `DOXXWIRE_JOOMLA_BASE_PATH`, and `DOXXWIRE_JOOMLA_TOKEN` (required), `DOXXWIRE_JOOMLA_DEFAULT_CATID` (default `0`), `DOXXWIRE_JOOMLA_BASIC_AUTH` (no default), and `DOXXWIRE_JOOMLA_DEFAULT_LANGUAGE` (default `*`) — and SHALL return the same validated settings that a TOML file with the same values produces.

#### Scenario: All variables set
- **WHEN** the environment sets `DOXXWIRE_JOOMLA_BASE_URL`, `DOXXWIRE_JOOMLA_BASE_PATH`, `DOXXWIRE_JOOMLA_TOKEN`, and `DOXXWIRE_JOOMLA_DEFAULT_CATID`
- **THEN** the environment loader returns settings carrying exactly those values

#### Scenario: Optional catid defaults to zero
- **WHEN** the environment omits `DOXXWIRE_JOOMLA_DEFAULT_CATID`
- **THEN** the environment loader returns settings with `default_catid` of `0`

#### Scenario: Optional basic_auth defaults to unset
- **WHEN** the environment omits `DOXXWIRE_JOOMLA_BASIC_AUTH`
- **THEN** the environment loader returns settings with no Basic Auth value

#### Scenario: Optional default_language defaults to all languages
- **WHEN** the environment omits `DOXXWIRE_JOOMLA_DEFAULT_LANGUAGE`
- **THEN** the environment loader returns settings with `default_language` of `*`

### Requirement: Env-based loading behaves like the TOML source
The environment-based loader SHALL validate its input exactly as the TOML
loader validates a file with the same values: a missing required variable
SHALL raise a settings error naming that variable (as a missing required
TOML key does), an empty-string value SHALL pass the same type checks as the
corresponding TOML value, and optional variables SHALL keep the TOML
loader's defaults — so the two sources cannot drift.

#### Scenario: Missing required variable is named
- **WHEN** the environment lacks `DOXXWIRE_JOOMLA_TOKEN`
- **THEN** the environment loader raises a settings error naming `DOXXWIRE_JOOMLA_TOKEN`

#### Scenario: Wrong type for catid
- **WHEN** `DOXXWIRE_JOOMLA_DEFAULT_CATID` is set to a non-integer value
- **THEN** the environment loader raises a settings error

# Spec Delta

## ADDED Requirements

### Requirement: The client sends an optional Basic Auth header
When the Joomla settings include a Basic Auth value, the client SHALL send `Authorization: Basic <value>` on every request, with the value sent verbatim (not re-encoded). When no Basic Auth value is configured, the client SHALL send no `Authorization` header. The header composes with the Joomla token, which is sent separately in `X-Joomla-Token`.

#### Scenario: Basic Auth header is sent when configured
- **WHEN** the client is created with a Basic Auth value and performs any article request
- **THEN** the request carries `Authorization: Basic <value>` with the value sent verbatim

#### Scenario: No Authorization header when not configured
- **WHEN** the client is created without a Basic Auth value and performs any article request
- **THEN** the request carries no `Authorization` header

#### Scenario: Basic Auth composes with the Joomla token
- **WHEN** the client is created with both a Basic Auth value and an API token and performs a request
- **THEN** the request carries both `Authorization: Basic <value>` and the API token in `X-Joomla-Token`

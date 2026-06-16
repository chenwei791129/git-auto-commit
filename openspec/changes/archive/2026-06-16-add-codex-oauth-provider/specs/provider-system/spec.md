## MODIFIED Requirements

### Requirement: Provider selection via CLI flag

The system SHALL accept a `--provider` CLI flag to select the AI provider.
The flag value MUST override all other provider selection methods.
Valid values SHALL include `gemini`, `claude-cli`, and `codex-oauth`.

#### Scenario: Provider specified via CLI flag

- **WHEN** user runs `commit-with-ai --provider claude-cli`
- **THEN** the system uses the Claude CLI provider regardless of environment variable settings

#### Scenario: Codex OAuth provider specified via CLI flag

- **WHEN** user runs `commit-with-ai --provider codex-oauth`
- **THEN** the system uses the Codex OAuth provider regardless of environment variable settings

#### Scenario: Invalid provider specified

- **WHEN** user runs `commit-with-ai --provider unknown`
- **THEN** the system exits with an error message listing valid provider names including `codex-oauth`

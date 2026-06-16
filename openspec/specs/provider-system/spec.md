# Provider System

## Purpose

Manages AI provider selection, model configuration, and the shared interface contract for commit message generation.

## Requirements

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


<!-- @trace
source: add-codex-oauth-provider
updated: 2026-06-16
code:
  - commit_with_ai/providers/gemini.py
  - pyproject.toml
  - README.md
  - uv.lock
  - commit_with_ai/__main__.py
  - scripts/poc_codex_oauth.py
  - commit_with_ai/providers/claude_cli.py
  - commit_with_ai/providers/codex_oauth.py
  - commit_with_ai/providers/_prompt.py
tests:
  - tests/test_cli.py
  - tests/test_providers_codex_oauth.py
-->

---
### Requirement: Provider selection via environment variable

The system SHALL read the `COMMIT_AI_PROVIDER` environment variable to select the AI provider.
This value MUST be used when no `--provider` CLI flag is provided.

#### Scenario: Provider specified via environment variable

- **WHEN** `COMMIT_AI_PROVIDER=claude-cli` is set and no `--provider` flag is given
- **THEN** the system uses the Claude CLI provider

#### Scenario: CLI flag overrides environment variable

- **WHEN** `COMMIT_AI_PROVIDER=gemini` is set and user runs `commit-with-ai --provider claude-cli`
- **THEN** the system uses the Claude CLI provider (flag takes precedence)


<!-- @trace
source: add-claude-cli-provider
updated: 2026-03-23
code:
  - commit_with_ai/providers/base.py
  - commit_with_ai/providers/gemini.py
  - commit_with_ai.py
  - tests/__init__.py
  - commit_with_ai/providers/claude_cli.py
  - uv.lock
  - commit_with_ai/providers/__init__.py
  - commit_with_ai/core.py
  - commit_with_ai/__init__.py
  - pyproject.toml
  - commit_with_ai/__main__.py
  - README.md
  - scripts/poc_claude_cli.py
tests:
  - tests/test_providers_gemini.py
  - tests/test_core.py
  - tests/test_providers_base.py
  - tests/test_cli.py
  - tests/test_providers_claude_cli.py
-->

---
### Requirement: Default provider is gemini

The system SHALL default to the `gemini` provider when neither `--provider` flag nor `COMMIT_AI_PROVIDER` environment variable is set.

#### Scenario: No provider configuration

- **WHEN** no `--provider` flag is given and `COMMIT_AI_PROVIDER` is not set
- **THEN** the system uses the Gemini provider


<!-- @trace
source: add-claude-cli-provider
updated: 2026-03-23
code:
  - commit_with_ai/providers/base.py
  - commit_with_ai/providers/gemini.py
  - commit_with_ai.py
  - tests/__init__.py
  - commit_with_ai/providers/claude_cli.py
  - uv.lock
  - commit_with_ai/providers/__init__.py
  - commit_with_ai/core.py
  - commit_with_ai/__init__.py
  - pyproject.toml
  - commit_with_ai/__main__.py
  - README.md
  - scripts/poc_claude_cli.py
tests:
  - tests/test_providers_gemini.py
  - tests/test_core.py
  - tests/test_providers_base.py
  - tests/test_cli.py
  - tests/test_providers_claude_cli.py
-->

---
### Requirement: Model selection via CLI flag and environment variable

The system SHALL accept a `--model` CLI flag and read the `COMMIT_AI_MODEL` environment variable to select the AI model.
The CLI flag MUST take precedence over the environment variable.
Each provider SHALL define its own default model when neither flag nor variable is set.

#### Scenario: Model specified via CLI flag

- **WHEN** user runs `commit-with-ai --provider claude-cli --model sonnet`
- **THEN** the system uses the `sonnet` model for the Claude CLI provider

#### Scenario: Model specified via environment variable

- **WHEN** `COMMIT_AI_MODEL=opus` is set and no `--model` flag is given
- **THEN** the system uses the `opus` model

#### Scenario: Default model per provider

- **WHEN** no `--model` flag is given and `COMMIT_AI_MODEL` is not set
- **THEN** the Gemini provider uses `gemini-3-flash-preview` and the Claude CLI provider uses `haiku`


<!-- @trace
source: add-claude-cli-provider
updated: 2026-03-23
code:
  - commit_with_ai/providers/base.py
  - commit_with_ai/providers/gemini.py
  - commit_with_ai.py
  - tests/__init__.py
  - commit_with_ai/providers/claude_cli.py
  - uv.lock
  - commit_with_ai/providers/__init__.py
  - commit_with_ai/core.py
  - commit_with_ai/__init__.py
  - pyproject.toml
  - commit_with_ai/__main__.py
  - README.md
  - scripts/poc_claude_cli.py
tests:
  - tests/test_providers_gemini.py
  - tests/test_core.py
  - tests/test_providers_base.py
  - tests/test_cli.py
  - tests/test_providers_claude_cli.py
-->

---
### Requirement: Provider interface contract

Each provider SHALL implement a `generate_commit_messages` method that accepts a git diff string and returns a list of exactly 5 commit message objects.
Each commit message object SHALL contain `type`, `scope`, `description`, and `full_message` fields.

#### Scenario: Provider returns structured messages

- **WHEN** a provider's `generate_commit_messages` is called with a valid diff
- **THEN** it returns a list of exactly 5 objects, each with `type` (string), `scope` (string), `description` (string), and `full_message` (string) fields

<!-- @trace
source: add-claude-cli-provider
updated: 2026-03-23
code:
  - commit_with_ai/providers/base.py
  - commit_with_ai/providers/gemini.py
  - commit_with_ai.py
  - tests/__init__.py
  - commit_with_ai/providers/claude_cli.py
  - uv.lock
  - commit_with_ai/providers/__init__.py
  - commit_with_ai/core.py
  - commit_with_ai/__init__.py
  - pyproject.toml
  - commit_with_ai/__main__.py
  - README.md
  - scripts/poc_claude_cli.py
tests:
  - tests/test_providers_gemini.py
  - tests/test_core.py
  - tests/test_providers_base.py
  - tests/test_cli.py
  - tests/test_providers_claude_cli.py
-->
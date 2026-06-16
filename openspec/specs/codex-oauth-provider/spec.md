# codex-oauth-provider Specification

## Purpose

TBD - created by archiving change 'add-codex-oauth-provider'. Update Purpose after archive.

## Requirements

### Requirement: Codex OAuth credential reading

The Codex OAuth provider SHALL read the locally stored codex OAuth credentials from `~/.codex/auth.json`.
The provider SHALL extract the `tokens.access_token` and `tokens.account_id` fields and the `auth_mode` field.
When the file does not exist or cannot be parsed as JSON, the system SHALL exit with a clear error message instructing the user to install and log in with codex.

#### Scenario: Credentials present and readable

- **WHEN** the Codex OAuth provider is selected and `~/.codex/auth.json` exists with a valid `tokens.access_token`
- **THEN** the provider reads the access token and account id and proceeds to generate commit messages

#### Scenario: Credentials file missing

- **WHEN** the Codex OAuth provider is selected and `~/.codex/auth.json` does not exist
- **THEN** the system exits with an error message instructing the user to install codex and complete login

#### Scenario: Credentials file malformed

- **WHEN** `~/.codex/auth.json` exists but cannot be parsed as JSON or lacks `tokens.access_token`
- **THEN** the system exits with an error message indicating the codex credentials are invalid


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
### Requirement: ChatGPT auth mode requirement

The Codex OAuth provider SHALL require `auth_mode` to equal `"chatgpt"` in the codex credentials.
When `auth_mode` is any other value, the system SHALL exit with an error message indicating that only the codex ChatGPT login mode is supported.

#### Scenario: ChatGPT login mode

- **WHEN** `~/.codex/auth.json` has `auth_mode` equal to `"chatgpt"`
- **THEN** the provider proceeds using the OAuth access token

#### Scenario: Non-ChatGPT auth mode

- **WHEN** `~/.codex/auth.json` has `auth_mode` equal to `"apikey"` or any value other than `"chatgpt"`
- **THEN** the system exits with an error message indicating only the ChatGPT login mode is supported


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
### Requirement: Access token expiry detection

The Codex OAuth provider SHALL decode the access token JWT and inspect its `exp` claim before calling the backend.
When the access token is expired, the system SHALL exit with an error message instructing the user to run codex once to refresh the login.
The provider SHALL NOT attempt to refresh the token itself and SHALL NOT write back to `~/.codex/auth.json`.

#### Scenario: Token is valid

- **WHEN** the access token `exp` claim is in the future
- **THEN** the provider proceeds to call the backend

#### Scenario: Token is expired

- **WHEN** the access token `exp` claim is in the past
- **THEN** the system exits with an error message instructing the user to run codex to refresh the login, and does not modify `~/.codex/auth.json`


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
### Requirement: Commit message generation via codex backend

The Codex OAuth provider SHALL call the OpenAI backend Responses endpoint used by codex, authenticating with `Authorization: Bearer <access_token>` and identifying the account with a `chatgpt-account-id` header set to the account id.
The request SHALL include the git diff content and request exactly 5 conventional commit messages.
When the backend responds with a non-success status or an unparseable body, the system SHALL exit with an error message that surfaces the backend failure.

#### Scenario: Successful generation

- **WHEN** the provider sends a valid request with a valid access token and account id
- **THEN** the backend returns a response that yields exactly 5 commit message objects

#### Scenario: Backend returns an error status

- **WHEN** the backend responds with a non-2xx status code
- **THEN** the system displays the backend error and exits with a non-zero code

#### Scenario: Backend returns an unparseable body

- **WHEN** the backend responds with a 2xx status code but the body cannot be parsed into the expected `messages` structure
- **THEN** the system displays a parse error surfacing the backend failure and exits with a non-zero code


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
### Requirement: Structured output with exactly five messages

The Codex OAuth provider SHALL request structured output enforcing a `messages` array of exactly 5 items.
Each item SHALL contain `type`, `scope`, `description`, and `full_message` string fields.
The provider SHALL return the parsed list of 5 message objects from `generate_commit_messages`.

#### Scenario: Structured output conforms

- **WHEN** the backend returns structured output for a valid diff
- **THEN** `generate_commit_messages` returns a list of exactly 5 objects, each with `type`, `scope`, `description`, and `full_message`


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
### Requirement: Model selection with default

The Codex OAuth provider SHALL define a default model and SHALL accept a model override via the `--model` flag and `COMMIT_AI_MODEL` environment variable through the shared provider selection mechanism.

#### Scenario: Default model

- **WHEN** no `--model` flag or `COMMIT_AI_MODEL` environment variable is set
- **THEN** the provider uses its default model

#### Scenario: Custom model

- **WHEN** the user specifies `--model <name>`
- **THEN** the provider uses `<name>` for the backend request

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
"""Codex OAuth provider for commit message generation.

Reuses the OAuth access token that codex stores locally in ~/.codex/auth.json to
call the OpenAI backend Responses endpoint used by codex (ChatGPT login mode).
Credential acquisition and refresh remain codex's responsibility; this provider
only reads and uses the existing token, and reports an actionable error when it
is missing, in the wrong mode, or expired.
"""

import base64
import json
import sys
import time
import uuid
from pathlib import Path

import httpx

from commit_with_ai.providers._prompt import PROMPT_TEMPLATE
from commit_with_ai.providers.base import BaseProvider

# codex backend Responses endpoint for ChatGPT-mode OAuth tokens (validated by
# scripts/poc_codex_oauth.py; this is codex's non-public backend interface).
BASE_URL = "https://chatgpt.com/backend-api/codex"
RESPONSES_PATH = "/responses"

REQUEST_TIMEOUT = 120

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "messages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "scope": {"type": "string"},
                    "description": {"type": "string"},
                    "full_message": {"type": "string"},
                },
                "required": ["type", "scope", "description", "full_message"],
                "additionalProperties": False,
            },
            "minItems": 5,
            "maxItems": 5,
        }
    },
    "required": ["messages"],
    "additionalProperties": False,
}

INSTRUCTIONS = "You are a helpful assistant that writes Conventional Commits messages."


class CodexOAuthProvider(BaseProvider):
    """Provider that reuses codex's local OAuth token to call the codex backend."""

    default_model = "gpt-5.4-mini"

    def __init__(self, model: str | None = None):
        self.model = model or self.default_model
        self.auth_path = Path.home() / ".codex" / "auth.json"

    def _read_credentials(self) -> tuple[str, str]:
        """Read and validate codex OAuth credentials from ~/.codex/auth.json.

        Returns (access_token, account_id). Exits with an actionable error when
        the file is missing/unparseable, not in ChatGPT mode, lacks required
        fields, or holds an expired access token. Never writes back to the file.
        """
        if not self.auth_path.exists():
            print(f"Error: codex credentials not found at {self.auth_path}")
            print("Please install codex and complete login first.")
            sys.exit(1)

        try:
            data = json.loads(self.auth_path.read_text())
        except (json.JSONDecodeError, OSError):
            print(f"Error: failed to read codex credentials at {self.auth_path}")
            print("The file is not valid JSON. Re-run codex to repair the login.")
            sys.exit(1)

        tokens = data.get("tokens") if isinstance(data, dict) else None
        if not isinstance(tokens, dict):
            print("Error: codex credentials are invalid (missing 'tokens').")
            sys.exit(1)

        access_token = tokens.get("access_token")
        account_id = tokens.get("account_id")
        if not access_token or not account_id:
            print("Error: codex credentials are invalid (missing access token or account id).")
            sys.exit(1)

        if data.get("auth_mode") != "chatgpt":
            print("Error: only the codex ChatGPT login mode is supported.")
            print("Log in with codex using a ChatGPT account, then retry.")
            sys.exit(1)

        self._check_not_expired(access_token)
        return access_token, account_id

    def _check_not_expired(self, access_token: str) -> None:
        """Exit if the access token JWT is expired. Fails closed on undecodable tokens."""
        exp = self._decode_jwt_exp(access_token)
        if exp is None:
            print("Error: could not read expiry from codex access token.")
            print("Run codex once to refresh the login, then retry.")
            sys.exit(1)
        if exp <= time.time():
            print("Error: codex access token has expired.")
            print("Run codex once to refresh the login, then retry.")
            sys.exit(1)

    @staticmethod
    def _decode_jwt_exp(token: str) -> int | None:
        """Decode a JWT's exp claim without verifying the signature.

        We only read our own token to decide whether to call the backend; we do
        not authenticate it here, so signature verification is unnecessary.
        """
        try:
            payload_b64 = token.split(".")[1]
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        except (IndexError, ValueError):
            return None
        if not isinstance(payload, dict):
            return None
        exp = payload.get("exp")
        # bool is an int subclass; a boolean exp is never a valid NumericDate.
        if isinstance(exp, bool) or not isinstance(exp, (int, float)):
            return None
        return exp

    def generate_commit_messages(self, diff_content: str) -> list[dict[str, str]]:
        """Generate commit messages via the codex backend Responses endpoint."""
        access_token, account_id = self._read_credentials()
        return self._request_commit_messages(access_token, account_id, diff_content)

    def _request_commit_messages(
        self, access_token: str, account_id: str, diff_content: str
    ) -> list[dict[str, str]]:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "chatgpt-account-id": account_id,
            "OpenAI-Beta": "responses=experimental",
            "originator": "codex_cli_rs",
            "session_id": str(uuid.uuid4()),
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        body = {
            "model": self.model,
            "instructions": INSTRUCTIONS,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": PROMPT_TEMPLATE.format(diff_content=diff_content),
                        }
                    ],
                }
            ],
            "stream": True,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "commit_messages",
                    "strict": True,
                    "schema": RESPONSE_SCHEMA,
                }
            },
        }

        url = BASE_URL + RESPONSES_PATH
        try:
            output_text = self._stream_output_text(url, headers, body)
        except httpx.HTTPError as e:
            print(f"Error: failed to reach codex backend: {e}")
            sys.exit(1)

        try:
            parsed = json.loads(output_text)
            messages = parsed["messages"]
        except (json.JSONDecodeError, KeyError, TypeError):
            print("Error: codex backend returned an unparseable response.")
            print(f"Output: {output_text[:500]}")
            sys.exit(1)

        # The json_schema enforces exactly 5 message objects server-side, but this
        # is codex's non-public backend; guard against drift so a wrong shape
        # surfaces a clean error instead of crashing later in the menu rendering.
        if not isinstance(messages, list) or len(messages) != 5:
            print("Error: codex backend did not return exactly 5 commit messages.")
            print(f"Output: {output_text[:500]}")
            sys.exit(1)

        return messages

    def _stream_output_text(self, url: str, headers: dict, body: dict) -> str:
        """POST to the Responses endpoint and assemble the structured output text.

        With store=false the response.completed event carries no output, so we
        accumulate response.output_text.delta and fall back to the text on
        response.output_text.done.
        """
        deltas: list[str] = []
        done_text: str | None = None

        with (
            httpx.Client(timeout=REQUEST_TIMEOUT) as client,
            client.stream("POST", url, headers=headers, json=body) as resp,
        ):
            if resp.status_code // 100 != 2:
                resp.read()
                print(f"Error: codex backend returned status {resp.status_code}")
                print(resp.text[:500])
                sys.exit(1)

            for line in resp.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                payload = line[len("data:") :].strip()
                if payload == "[DONE]":
                    break
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                event_type = event.get("type")
                if event_type == "response.output_text.delta":
                    deltas.append(event.get("delta", ""))
                elif event_type == "response.output_text.done":
                    done_text = event.get("text")

        # Prefer the done event's text, but fall back to accumulated deltas when
        # it is missing or empty so streamed content is never discarded.
        return done_text or "".join(deltas)

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["httpx>=0.28.1"]
# ///
"""POC: verify the codex backend Responses endpoint using local OAuth credentials.

This one-shot script validates, against a real ~/.codex/auth.json token:
  - the base URL / path of the codex backend Responses endpoint,
  - the required headers (Authorization, chatgpt-account-id, OpenAI-Beta, originator,
    session_id),
  - a usable model name, and
  - the json_schema structured-output format that yields exactly 5 commit messages.

Run with:  uv run scripts/poc_codex_oauth.py

It prints the parsed 5-message structured output on success. The confirmed
endpoint / headers / model are recorded in design.md's Open Questions.
"""

import base64
import json
import signal
import sys
import time
import uuid
from pathlib import Path

import httpx

AUTH_PATH = Path.home() / ".codex" / "auth.json"

# Candidate backend used by codex for ChatGPT-mode OAuth tokens.
BASE_URL = "https://chatgpt.com/backend-api/codex"
RESPONSES_PATH = "/responses"

# Default model candidate to validate (fast/cheap, sufficient for commit messages).
MODEL = "gpt-5.4-mini"

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

SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 111..222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,6 @@
 def main():
-    print("hello")
+    print("hello world")
+
+def goodbye():
+    print("bye")
"""

PROMPT = f"""Analyze the following git diff and generate 5 distinct, concise, and descriptive commit messages.

Requirements:
1. MUST strictly follow the Conventional Commits specification
2. Format: <type>(<scope>): <description>
3. MUST be written in English
4. Each message should offer a different perspective or level of detail

Git diff:
{SAMPLE_DIFF}

Output a JSON object with a "messages" array containing exactly 5 commit message objects.
Each object should have: type, scope (empty string if N/A), description, and full_message."""


def _decode_jwt_exp(token: str) -> int | None:
    """Decode a JWT's exp claim without verifying the signature."""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("exp")
    except Exception:
        return None


def main() -> None:
    if not AUTH_PATH.exists():
        print(f"Error: {AUTH_PATH} not found. Install and log in with codex first.")
        sys.exit(1)

    data = json.loads(AUTH_PATH.read_text())
    auth_mode = data.get("auth_mode")
    tokens = data.get("tokens") or {}
    access_token = tokens.get("access_token")
    account_id = tokens.get("account_id")

    print(f"auth_mode = {auth_mode!r}")
    print(f"account_id present = {bool(account_id)}")

    if auth_mode != "chatgpt":
        print(f"Error: auth_mode is {auth_mode!r}, expected 'chatgpt'.")
        sys.exit(1)

    exp = _decode_jwt_exp(access_token)
    print(f"access_token exp = {exp} (now = {int(time.time())})")
    if exp and exp < time.time():
        print("Error: access token expired. Run codex once to refresh login.")
        sys.exit(1)

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
        "model": MODEL,
        "instructions": "You are a helpful assistant that writes Conventional Commits.",
        "input": [{"role": "user", "content": [{"type": "input_text", "text": PROMPT}]}],
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
    print(f"\nPOST {url}")
    print(f"model = {MODEL}\n")

    # The backend streams SSE events. With store=false, response.completed
    # carries no output, so we accumulate response.output_text.delta and fall
    # back to the text on response.output_text.done.
    final_text = None
    deltas: list[str] = []
    with (
        httpx.Client(timeout=120) as client,
        client.stream("POST", url, headers=headers, json=body) as resp,
    ):
        if resp.status_code // 100 != 2:
            resp.read()
            print(f"Error: backend returned {resp.status_code}")
            print(resp.text[:1000])
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
                final_text = event.get("text")

    if final_text is None and deltas:
        final_text = "".join(deltas)
    if final_text is None:
        print("Error: no output_text found in streamed response.")
        sys.exit(1)

    parsed = json.loads(final_text)
    messages = parsed["messages"]
    print(f"\n✓ Received {len(messages)} messages:\n")
    for i, m in enumerate(messages, 1):
        print(f"  {i}. {m['full_message']}")

    if len(messages) != 5:
        print(f"\nError: expected 5 messages, got {len(messages)}.")
        sys.exit(1)

    print("\n✓ POC succeeded. Record endpoint/headers/model in design.md Open Questions.")


def _handle_sigterm(signum, frame):
    sys.exit(128 + signum)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)

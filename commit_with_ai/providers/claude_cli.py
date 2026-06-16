"""Claude CLI provider for commit message generation via subprocess."""

import json
import shutil
import subprocess
import sys

from commit_with_ai.providers._prompt import PROMPT_TEMPLATE
from commit_with_ai.providers.base import BaseProvider

RESPONSE_SCHEMA = json.dumps(
    {
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
                    "required": ["type", "description", "full_message"],
                },
                "minItems": 5,
                "maxItems": 5,
            }
        },
        "required": ["messages"],
    }
)


class ClaudeCliProvider(BaseProvider):
    """Claude CLI provider using `claude -p` subprocess for commit message generation."""

    default_model = "haiku"

    def __init__(self, model: str | None = None):
        self.model = model or self.default_model
        self._check_cli_available()

    def _check_cli_available(self) -> None:
        """Verify that the claude CLI is installed and available on PATH."""
        if shutil.which("claude") is None:
            print("Error: Claude CLI not found in PATH")
            print("Please install Claude Code: https://docs.anthropic.com/en/docs/claude-code")
            sys.exit(1)

    def generate_commit_messages(self, diff_content: str) -> list[dict[str, str]]:
        """Generate commit messages by invoking claude -p with structured output."""
        prompt = PROMPT_TEMPLATE.format(diff_content=diff_content)

        try:
            result = subprocess.run(
                [
                    "claude",
                    "-p",
                    "--no-session-persistence",
                    "--output-format",
                    "json",
                    "--json-schema",
                    RESPONSE_SCHEMA,
                    "--model",
                    self.model,
                ],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            print("Error: Claude CLI timed out after 120 seconds")
            sys.exit(1)

        if result.returncode != 0:
            print(f"Error: Claude CLI exited with code {result.returncode}")
            if result.stderr:
                print(f"Details: {result.stderr}")
            sys.exit(1)

        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError:
            print("Error: Failed to parse Claude CLI output as JSON")
            print(f"Output: {result.stdout[:500]}")
            sys.exit(1)

        # Structured output is in the "structured_output" field
        content = response.get("structured_output")
        if content is None:
            print("Error: No structured_output in Claude CLI response")
            print(f"Response keys: {list(response.keys())}")
            sys.exit(1)

        if "messages" not in content:
            print("Error: No 'messages' field in structured output")
            sys.exit(1)

        return content["messages"]

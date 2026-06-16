"""Gemini provider for commit message generation."""

import json
import os
import sys

from google import genai

from commit_with_ai.providers._prompt import PROMPT_TEMPLATE
from commit_with_ai.providers.base import BaseProvider

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
                "required": ["type", "description", "full_message"],
            },
            "minItems": 5,
            "maxItems": 5,
        }
    },
    "required": ["messages"],
}


class GeminiProvider(BaseProvider):
    """Gemini API provider for commit message generation."""

    default_model = "gemini-3-flash-preview"

    def __init__(self, model: str | None = None):
        self.model = model or self.default_model
        self._validate_api_key()

    def _validate_api_key(self) -> None:
        """Check that a Gemini API key is configured."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY or GOOGLE_API_KEY not set")
            print("Please set one of these environment variables with your API key")
            sys.exit(1)

    def generate_commit_messages(self, diff_content: str) -> list[dict[str, str]]:
        """Generate commit messages using Gemini API with structured JSON output."""
        client = genai.Client()
        prompt = PROMPT_TEMPLATE.format(diff_content=diff_content)

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": RESPONSE_SCHEMA,
                },
            )
            data = json.loads(response.text)
            return data["messages"]

        except Exception as e:
            print(f"Error: Failed to generate commit messages: {e}")
            sys.exit(1)

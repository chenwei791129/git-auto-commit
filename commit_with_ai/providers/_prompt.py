"""Shared prompt template for commit message generation.

All providers send the same instruction to their backend; only the structured
output mechanism differs. Keep the prompt here so the wording stays in lockstep
across providers.
"""

PROMPT_TEMPLATE = """Analyze the following git diff and generate 5 distinct, concise, and descriptive commit messages.

Requirements:
1. MUST strictly follow the Conventional Commits specification
2. Format: <type>(<scope>): <description>
   - type: feat, fix, docs, style, refactor, test, chore, etc.
   - scope: optional, can be empty string if not applicable
   - description: concise description in imperative mood
3. MUST be written in English
4. Each message should offer a different perspective or level of detail
5. Keep descriptions under 72 characters

Git diff:
{diff_content}

Output a JSON object with a "messages" array containing exactly 5 commit message objects.
Each object should have: type, scope (empty string if N/A), description, and full_message."""

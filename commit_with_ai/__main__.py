"""Entry point for commit-with-ai package."""

import argparse
import os
import signal
import sys

from commit_with_ai.core import (
    check_staged_changes,
    commit_changes,
    display_menu,
    get_staged_diff,
    get_user_selection,
)

VALID_PROVIDERS = ["gemini", "claude-cli", "codex-oauth"]


def _handle_sigterm(signum, frame):
    sys.exit(128 + signum)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="commit-with-ai",
        description="AI-powered git commit message generator",
    )
    parser.add_argument(
        "--provider",
        choices=VALID_PROVIDERS,
        default=None,
        help="AI provider to use (default: gemini, env: COMMIT_AI_PROVIDER)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="AI model to use (env: COMMIT_AI_MODEL, default varies by provider)",
    )
    return parser.parse_args(argv)


def resolve_provider_name(flag_value: str | None) -> str:
    """Resolve provider name: --provider flag > COMMIT_AI_PROVIDER env > 'gemini'."""
    if flag_value is not None:
        return flag_value
    return os.environ.get("COMMIT_AI_PROVIDER", "gemini")


def resolve_model(flag_value: str | None, provider_default: str) -> str:
    """Resolve model: --model flag > COMMIT_AI_MODEL env > provider default."""
    if flag_value is not None:
        return flag_value
    return os.environ.get("COMMIT_AI_MODEL", provider_default)


def get_provider(provider_name: str, model: str):
    """Get provider instance by name."""
    if provider_name == "gemini":
        from commit_with_ai.providers.gemini import GeminiProvider

        return GeminiProvider(model=model)
    elif provider_name == "claude-cli":
        from commit_with_ai.providers.claude_cli import ClaudeCliProvider

        return ClaudeCliProvider(model=model)
    elif provider_name == "codex-oauth":
        from commit_with_ai.providers.codex_oauth import CodexOAuthProvider

        return CodexOAuthProvider(model=model)
    else:
        print(f"Error: Unknown provider '{provider_name}'. Valid: {', '.join(VALID_PROVIDERS)}")
        sys.exit(1)


def main():
    """Main entry point."""
    signal.signal(signal.SIGTERM, _handle_sigterm)

    try:
        args = parse_args()
        provider_name = resolve_provider_name(args.provider)
        provider_obj = get_provider(provider_name, "")  # model resolved after provider init
        model = resolve_model(args.model, provider_obj.default_model)
        provider_obj.model = model

        if not check_staged_changes():
            print("Error: No staged changes found. Please stage your changes first.")
            print("\nTip: Use 'git add <files>' to stage changes")
            sys.exit(1)

        print("Analyzing staged changes...")
        diff_content = get_staged_diff()

        print(f"Generating commit message options with {provider_name} ({model})...")
        messages = provider_obj.generate_commit_messages(diff_content)

        display_menu(messages)
        selected_message = get_user_selection(messages)
        commit_changes(selected_message)

    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()

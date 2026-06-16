"""Tests for CLI argument parsing and provider/model selection."""

import os
from unittest.mock import patch

import pytest

from commit_with_ai.__main__ import (
    get_provider,
    parse_args,
    resolve_model,
    resolve_provider_name,
)


class TestParseArgs:
    def test_no_args_defaults(self):
        args = parse_args([])
        assert args.provider is None
        assert args.model is None

    def test_provider_flag(self):
        args = parse_args(["--provider", "claude-cli"])
        assert args.provider == "claude-cli"

    def test_codex_oauth_provider_flag_accepted(self):
        args = parse_args(["--provider", "codex-oauth"])
        assert args.provider == "codex-oauth"


class TestGetProvider:
    def test_unknown_provider_lists_codex_oauth(self, capsys):
        # argparse choices intercepts `--provider unknown`, so the unknown branch
        # is reached only via non-flag paths (e.g. COMMIT_AI_PROVIDER).
        with pytest.raises(SystemExit):
            get_provider("unknown", "")
        assert "codex-oauth" in capsys.readouterr().out

    def test_model_flag(self):
        args = parse_args(["--model", "sonnet"])
        assert args.model == "sonnet"

    def test_both_flags(self):
        args = parse_args(["--provider", "claude-cli", "--model", "opus"])
        assert args.provider == "claude-cli"
        assert args.model == "opus"


class TestResolveProviderName:
    def test_flag_takes_precedence_over_env(self):
        with patch.dict(os.environ, {"COMMIT_AI_PROVIDER": "gemini"}):
            assert resolve_provider_name("claude-cli") == "claude-cli"

    def test_env_used_when_no_flag(self):
        with patch.dict(os.environ, {"COMMIT_AI_PROVIDER": "claude-cli"}):
            assert resolve_provider_name(None) == "claude-cli"

    def test_defaults_to_gemini(self):
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("COMMIT_AI_PROVIDER", None)
            with patch.dict(os.environ, env, clear=True):
                assert resolve_provider_name(None) == "gemini"

    def test_flag_overrides_env(self):
        with patch.dict(os.environ, {"COMMIT_AI_PROVIDER": "gemini"}):
            assert resolve_provider_name("claude-cli") == "claude-cli"


class TestResolveModel:
    def test_flag_takes_precedence(self):
        with patch.dict(os.environ, {"COMMIT_AI_MODEL": "opus"}):
            assert resolve_model("sonnet", "haiku") == "sonnet"

    def test_env_used_when_no_flag(self):
        with patch.dict(os.environ, {"COMMIT_AI_MODEL": "opus"}):
            assert resolve_model(None, "haiku") == "opus"

    def test_provider_default_when_no_flag_no_env(self):
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("COMMIT_AI_MODEL", None)
            with patch.dict(os.environ, env, clear=True):
                assert resolve_model(None, "haiku") == "haiku"

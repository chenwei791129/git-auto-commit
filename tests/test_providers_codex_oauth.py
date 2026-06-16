"""Tests for Codex OAuth provider.

These tests target only this project's own logic: credential reading, auth-mode
and expiry validation, the request body we build, and SSE response parsing.
They mock httpx and use temp auth files; they do not exercise httpx or the codex
backend itself.
"""

import base64
import json
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import httpx
import pytest

from commit_with_ai.providers.base import BaseProvider
from commit_with_ai.providers.codex_oauth import CodexOAuthProvider


def _make_jwt(exp: int) -> str:
    """Build an unsigned JWT-shaped token whose payload carries the given exp."""
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    payload_raw = json.dumps({"exp": exp}).encode()
    payload = base64.urlsafe_b64encode(payload_raw).rstrip(b"=").decode()
    return f"{header}.{payload}.sig"


def _write_auth(tmp_path, *, auth_mode="chatgpt", access_token="default", account_id="acct-123"):
    """Write a ~/.codex/auth.json-shaped file and return its path."""
    if access_token == "default":
        access_token = _make_jwt(9999999999)  # far-future exp
    auth_file = tmp_path / "auth.json"
    payload = {
        "auth_mode": auth_mode,
        "tokens": {"access_token": access_token, "account_id": account_id},
    }
    auth_file.write_text(json.dumps(payload))
    return auth_file


def _make_provider(tmp_path, *, model=None, **auth_kwargs):
    provider = CodexOAuthProvider(model=model)
    provider.auth_path = _write_auth(tmp_path, **auth_kwargs)
    return provider


def _sse_lines(text: str) -> list[str]:
    """Build SSE lines that stream the given text as output_text deltas + done."""
    return [
        'data: {"type": "response.created"}',
        f"data: {json.dumps({'type': 'response.output_text.delta', 'delta': text})}",
        f"data: {json.dumps({'type': 'response.output_text.done', 'text': text})}",
        'data: {"type": "response.completed", "response": {"output": []}}',
        "data: [DONE]",
    ]


def _five_messages_text() -> str:
    return json.dumps(
        {
            "messages": [
                {
                    "type": "feat",
                    "scope": "app",
                    "description": f"change {i}",
                    "full_message": f"feat(app): change {i}",
                }
                for i in range(5)
            ]
        }
    )


@contextmanager
def _mock_httpx(status_code=200, lines=None, error_body=""):
    """Patch httpx in the codex_oauth module to simulate a streamed response.

    Yields the patched httpx mock so callers can inspect the request via
    mock_httpx.Client.return_value.__enter__.return_value.stream.call_args.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.iter_lines.return_value = lines or []
    resp.text = error_body
    resp.read.return_value = None

    stream_cm = MagicMock()
    stream_cm.__enter__.return_value = resp
    stream_cm.__exit__.return_value = False

    client = MagicMock()
    client.stream.return_value = stream_cm

    client_cm = MagicMock()
    client_cm.__enter__.return_value = client
    client_cm.__exit__.return_value = False

    with patch("commit_with_ai.providers.codex_oauth.httpx") as mock_httpx:
        mock_httpx.Client.return_value = client_cm
        # Keep the real exception type so `except httpx.HTTPError` stays valid.
        mock_httpx.HTTPError = httpx.HTTPError
        yield mock_httpx


class TestInit:
    def test_is_base_provider_subclass(self):
        assert issubclass(CodexOAuthProvider, BaseProvider)

    def test_default_model(self):
        assert CodexOAuthProvider(model="").model == "gpt-5.4-mini"
        assert CodexOAuthProvider().default_model == "gpt-5.4-mini"

    def test_custom_model_retained(self):
        assert CodexOAuthProvider(model="gpt-5.5").model == "gpt-5.5"


class TestCredentialReading:
    def test_credentials_present_and_readable(self, tmp_path):
        provider = _make_provider(tmp_path)
        with _mock_httpx(lines=_sse_lines(_five_messages_text())):
            result = provider.generate_commit_messages("diff")
        assert len(result) == 5

    def test_credentials_file_missing(self, tmp_path):
        provider = CodexOAuthProvider(model="")
        provider.auth_path = tmp_path / "does-not-exist.json"
        with pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")

    def test_credentials_file_malformed_json(self, tmp_path):
        provider = CodexOAuthProvider(model="")
        bad = tmp_path / "auth.json"
        bad.write_text("{not valid json")
        provider.auth_path = bad
        with pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")

    def test_credentials_missing_access_token(self, tmp_path):
        provider = CodexOAuthProvider(model="")
        f = tmp_path / "auth.json"
        f.write_text(json.dumps({"auth_mode": "chatgpt", "tokens": {"account_id": "x"}}))
        provider.auth_path = f
        with pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")


class TestAuthMode:
    def test_chatgpt_mode_proceeds(self, tmp_path):
        provider = _make_provider(tmp_path, auth_mode="chatgpt")
        with _mock_httpx(lines=_sse_lines(_five_messages_text())):
            result = provider.generate_commit_messages("diff")
        assert len(result) == 5

    def test_apikey_mode_exits(self, tmp_path):
        provider = _make_provider(tmp_path, auth_mode="apikey")
        with pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")


class TestExpiry:
    def test_valid_token_proceeds(self, tmp_path):
        provider = _make_provider(tmp_path, access_token=_make_jwt(9999999999))
        with _mock_httpx(lines=_sse_lines(_five_messages_text())):
            result = provider.generate_commit_messages("diff")
        assert len(result) == 5

    def test_expired_token_exits_without_writing(self, tmp_path):
        auth_file = _write_auth(tmp_path, access_token=_make_jwt(1))  # exp in the past
        provider = CodexOAuthProvider(model="")
        provider.auth_path = auth_file
        before = auth_file.read_text()
        with pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")
        # The provider must not refresh or rewrite the credential file.
        assert auth_file.read_text() == before

    def test_non_dict_jwt_payload_exits_cleanly(self, tmp_path):
        # A token whose payload decodes to valid JSON that is not an object must
        # produce a clean exit, not an unhandled AttributeError.
        header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(b"12345").rstrip(b"=").decode()
        provider = _make_provider(tmp_path, access_token=f"{header}.{payload}.sig")
        with pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")


class TestBackendCall:
    def test_successful_generation_returns_five(self, tmp_path):
        provider = _make_provider(tmp_path)
        with _mock_httpx(lines=_sse_lines(_five_messages_text())):
            result = provider.generate_commit_messages("diff")
        assert len(result) == 5
        assert result[0]["type"] == "feat"
        assert result[0]["full_message"] == "feat(app): change 0"
        for m in result:
            assert {"type", "scope", "description", "full_message"} <= set(m)

    def test_sends_auth_and_account_headers(self, tmp_path):
        provider = _make_provider(
            tmp_path, access_token=_make_jwt(9999999999), account_id="acct-xyz"
        )
        with _mock_httpx(lines=_sse_lines(_five_messages_text())) as mock_httpx:
            provider.generate_commit_messages("diff")
        client = mock_httpx.Client.return_value.__enter__.return_value
        headers = client.stream.call_args.kwargs["headers"]
        assert headers["Authorization"].startswith("Bearer ")
        assert headers["chatgpt-account-id"] == "acct-xyz"

    def test_non_2xx_exits(self, tmp_path):
        provider = _make_provider(tmp_path)
        with _mock_httpx(status_code=400, error_body="bad request"), pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")

    def test_unparseable_body_exits(self, tmp_path):
        provider = _make_provider(tmp_path)
        with _mock_httpx(lines=_sse_lines("not json at all")), pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")

    def test_wrong_message_count_exits(self, tmp_path):
        provider = _make_provider(tmp_path)
        three = json.dumps(
            {
                "messages": [
                    {"type": "feat", "scope": "", "description": "x", "full_message": "feat: x"}
                ]
                * 3
            }
        )
        with _mock_httpx(lines=_sse_lines(three)), pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")

    def test_non_list_messages_exits(self, tmp_path):
        provider = _make_provider(tmp_path)
        bad = json.dumps({"messages": "oops"})
        with _mock_httpx(lines=_sse_lines(bad)), pytest.raises(SystemExit):
            provider.generate_commit_messages("diff")

    def test_falls_back_to_deltas_when_done_text_empty(self, tmp_path):
        # When the done event carries an empty text, accumulated deltas must not
        # be discarded.
        provider = _make_provider(tmp_path)
        text = _five_messages_text()
        lines = [
            f"data: {json.dumps({'type': 'response.output_text.delta', 'delta': text})}",
            f"data: {json.dumps({'type': 'response.output_text.done', 'text': ''})}",
            "data: [DONE]",
        ]
        with _mock_httpx(lines=lines):
            result = provider.generate_commit_messages("diff")
        assert len(result) == 5


class TestModelSelection:
    def test_request_uses_custom_model(self, tmp_path):
        provider = _make_provider(tmp_path, access_token=_make_jwt(9999999999))
        provider.model = "gpt-5.5"
        with _mock_httpx(lines=_sse_lines(_five_messages_text())) as mock_httpx:
            provider.generate_commit_messages("diff")
        client = mock_httpx.Client.return_value.__enter__.return_value
        body = client.stream.call_args.kwargs["json"]
        assert body["model"] == "gpt-5.5"

    def test_request_uses_default_model(self, tmp_path):
        provider = _make_provider(tmp_path)
        with _mock_httpx(lines=_sse_lines(_five_messages_text())) as mock_httpx:
            provider.generate_commit_messages("diff")
        client = mock_httpx.Client.return_value.__enter__.return_value
        body = client.stream.call_args.kwargs["json"]
        assert body["model"] == "gpt-5.4-mini"

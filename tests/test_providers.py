import base64
from unittest.mock import patch

import requests

from llama_scan.errors import ProviderError
from llama_scan.prompts import BASE_TRANSCRIPTION_PROMPT
from llama_scan.providers import get_provider
from llama_scan.providers.openrouter import API_URL


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_omitted_provider_is_ollama():
    provider = get_provider(None)
    assert provider.name == "ollama"
    assert provider.default_model == "qwen2.5vl:latest"


def test_unknown_provider_raises():
    try:
        get_provider("anthropic")
    except ValueError as exc:
        assert "anthropic" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_ollama_sends_the_default_prompt(tmp_path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")
    provider = get_provider("ollama", server_url="http://127.0.0.1:11434/")
    response = FakeResponse(200, {"response": "local text"})

    with patch("llama_scan.providers.ollama.requests.post", return_value=response) as post:
        text = provider.transcribe_image(str(image_path), model="qwen2.5vl:latest")

    assert text == "local text"
    assert post.call_args.args[0] == "http://127.0.0.1:11434/api/generate"
    body = post.call_args.kwargs["json"]
    assert body["prompt"] == BASE_TRANSCRIPTION_PROMPT
    assert body["images"] == [base64.b64encode(b"png-bytes").decode()]


def test_ollama_prompt_replaces_the_default(tmp_path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")
    provider = get_provider("ollama")
    response = FakeResponse(200, {"response": "local text"})

    with patch("llama_scan.providers.ollama.requests.post", return_value=response) as post:
        provider.transcribe_image(
            str(image_path),
            model="qwen2.5vl:latest",
            prompt="Keep the letterhead.",
        )

    assert post.call_args.kwargs["json"]["prompt"] == "Keep the letterhead."


def test_ollama_api_error_raises_provider_error(tmp_path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")
    provider = get_provider("ollama")
    response = FakeResponse(500, {"error": "nope"}, text="nope")

    with patch("llama_scan.providers.ollama.requests.post", return_value=response):
        try:
            provider.transcribe_image(str(image_path), model="qwen2.5vl:latest")
        except ProviderError as exc:
            assert "500" in str(exc)
        else:
            raise AssertionError("expected ProviderError")


def test_ollama_check_failure_raises_provider_error():
    provider = get_provider("ollama")
    with patch(
        "llama_scan.providers.ollama.requests.get",
        side_effect=requests.exceptions.ConnectionError("down"),
    ):
        try:
            provider.check()
        except ProviderError as exc:
            assert "Ollama server not running" in str(exc)
        else:
            raise AssertionError("expected ProviderError")


def test_openrouter_sends_image_and_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")
    provider = get_provider("openrouter")
    response = FakeResponse(
        200, {"choices": [{"message": {"content": "hosted text"}}]}
    )

    with patch(
        "llama_scan.providers.openrouter.requests.post", return_value=response
    ) as post:
        text = provider.transcribe_image(
            str(image_path),
            model="qwen/qwen2.5-vl-72b-instruct",
            prompt="Keep the letterhead.",
        )

    assert text == "hosted text"
    assert post.call_args.args[0] == API_URL
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer sk-or-test"
    content = post.call_args.kwargs["json"]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "Keep the letterhead."}
    encoded = base64.b64encode(b"png-bytes").decode()
    assert content[1]["image_url"]["url"] == f"data:image/png;base64,{encoded}"


def test_openrouter_api_error_raises_provider_error(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")
    provider = get_provider("openrouter")
    response = FakeResponse(401, {"error": {"message": "bad key"}}, text="bad key")

    with patch("llama_scan.providers.openrouter.requests.post", return_value=response):
        try:
            provider.transcribe_image(str(image_path), model="m")
        except ProviderError as exc:
            assert "401" in str(exc)
            assert "bad key" in str(exc)
        else:
            raise AssertionError("expected ProviderError")


def test_openrouter_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    provider = get_provider("openrouter")
    try:
        provider.check()
    except ProviderError as exc:
        assert "OPENROUTER_API_KEY" in str(exc)
    else:
        raise AssertionError("expected ProviderError")


def _install_fake_litellm(monkeypatch, response=None, error=None):
    """Replace the litellm package with a stub that records the request."""
    import sys
    import types
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    if response is None:
        message = SimpleNamespace(content="gateway text")
        response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
    module = types.ModuleType("litellm")
    module.completion = MagicMock(return_value=response, side_effect=error)
    monkeypatch.setitem(sys.modules, "litellm", module)
    return module


def test_litellm_is_registered():
    provider = get_provider("LiteLLM")
    assert provider.name == "litellm"
    assert provider.default_model == "openai/gpt-4o-mini"


def test_litellm_sends_image_and_prompt(tmp_path, monkeypatch):
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.delenv("LITELLM_API_BASE", raising=False)
    fake = _install_fake_litellm(monkeypatch)
    image_path = tmp_path / "page.jpg"
    image_path.write_bytes(b"jpg-bytes")
    provider = get_provider("litellm")

    text = provider.transcribe_image(
        str(image_path),
        model="anthropic/claude-sonnet-4-5",
        prompt="Keep the letterhead.",
    )

    assert text == "gateway text"
    request = fake.completion.call_args.kwargs
    assert request["model"] == "anthropic/claude-sonnet-4-5"
    assert request["drop_params"] is True
    assert request["timeout"] == 300
    # Unset, LiteLLM reads the upstream provider's own credentials from the environment.
    assert "api_key" not in request
    assert "api_base" not in request
    content = request["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "Keep the letterhead."}
    encoded = base64.b64encode(b"jpg-bytes").decode()
    assert content[1]["image_url"]["url"] == f"data:image/jpeg;base64,{encoded}"
    assert fake.suppress_debug_info is True


def test_litellm_sends_the_default_prompt(tmp_path, monkeypatch):
    fake = _install_fake_litellm(monkeypatch)
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")

    get_provider("litellm").transcribe_image(str(image_path), model="m")

    content = fake.completion.call_args.kwargs["messages"][0]["content"]
    assert content[0]["text"] == BASE_TRANSCRIPTION_PROMPT


def test_litellm_sends_key_and_base_url_when_set(tmp_path, monkeypatch):
    monkeypatch.setenv("LITELLM_API_KEY", "sk-proxy")
    monkeypatch.setenv("LITELLM_API_BASE", "http://localhost:4000/")
    fake = _install_fake_litellm(monkeypatch)
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")

    get_provider("litellm").transcribe_image(
        str(image_path), model="litellm_proxy/vision"
    )

    request = fake.completion.call_args.kwargs
    assert request["api_key"] == "sk-proxy"
    assert request["api_base"] == "http://localhost:4000"


def test_litellm_joins_text_parts(tmp_path, monkeypatch):
    from types import SimpleNamespace

    message = SimpleNamespace(
        content=[
            {"type": "text", "text": "line one\n"},
            {"type": "image_url", "image_url": {"url": "ignored"}},
            {"type": "text", "text": "line two"},
        ]
    )
    _install_fake_litellm(
        monkeypatch, SimpleNamespace(choices=[SimpleNamespace(message=message)])
    )
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")

    text = get_provider("litellm").transcribe_image(str(image_path), model="m")

    assert text == "line one\nline two"


def test_litellm_empty_response_raises_provider_error(tmp_path, monkeypatch):
    from types import SimpleNamespace

    message = SimpleNamespace(content="")
    _install_fake_litellm(
        monkeypatch, SimpleNamespace(choices=[SimpleNamespace(message=message)])
    )
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")

    try:
        get_provider("litellm").transcribe_image(str(image_path), model="m")
    except ProviderError as exc:
        assert "empty response" in str(exc)
    else:
        raise AssertionError("expected ProviderError")


def test_litellm_api_error_raises_provider_error(tmp_path, monkeypatch):
    class AuthenticationError(Exception):
        def __init__(self, message):
            super().__init__(message)
            self.message = message

    _install_fake_litellm(monkeypatch, error=AuthenticationError("invalid x-api-key"))
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"png-bytes")

    try:
        get_provider("litellm").transcribe_image(
            str(image_path), model="anthropic/claude-sonnet-4-5"
        )
    except ProviderError as exc:
        assert "AuthenticationError" in str(exc)
        assert "invalid x-api-key" in str(exc)
    else:
        raise AssertionError("expected ProviderError")


def test_litellm_requires_the_package(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "litellm", None)
    try:
        get_provider("litellm").check()
    except ProviderError as exc:
        assert "llama-scan[litellm]" in str(exc)
    else:
        raise AssertionError("expected ProviderError")

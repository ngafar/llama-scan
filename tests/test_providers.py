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

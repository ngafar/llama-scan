import base64
import os
from pathlib import Path

import requests

from .base import TranscriptionProvider, build_prompt

API_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_URL = "https://openrouter.ai/api/v1/key"

_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class OpenRouterProvider(TranscriptionProvider):
    """Transcribe page images with the OpenRouter chat completions API."""

    name = "openrouter"
    default_model = "qwen/qwen2.5-vl-72b-instruct"

    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()

    def check(self) -> None:
        """Check that an OpenRouter API key is set and accepted."""
        if not self.api_key:
            raise RuntimeError(
                "OpenRouter API key not set. "
                "Set the OPENROUTER_API_KEY environment variable and try again."
            )

        try:
            response = requests.get(
                KEY_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Could not reach the OpenRouter API: {exc}") from exc

        if response.status_code != 200:
            raise RuntimeError(
                "OpenRouter API key check failed "
                f"({response.status_code}): {response.text}"
            )

    def transcribe_image(
        self,
        image_path: str,
        model: str,
        custom_instructions: str | None = None,
    ) -> str:
        """
        Transcribe an image using the OpenRouter chat completions API.

        Args:
            image_path (str): Path to the image file.
            model (str): OpenRouter model slug to use for transcription.
            custom_instructions (str, optional): Additional instructions to include in the prompt.
        """
        suffix = Path(image_path).suffix.lower()
        mime_type = _MIME_TYPES.get(suffix, "image/png")
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
        data_url = f"data:{mime_type};base64,{image_data}"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_prompt(custom_instructions)},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ngafar/llama-scan",
            "X-OpenRouter-Title": "llama-scan",
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)

        try:
            data = response.json()
        except ValueError:
            raise Exception(
                "OpenRouter returned a non-JSON response "
                f"({response.status_code}): {response.text}"
            )

        if response.status_code != 200:
            message = ""
            if isinstance(data, dict):
                error = data.get("error")
                if isinstance(error, dict):
                    message = error.get("message") or ""
                elif isinstance(error, str):
                    message = error
            raise Exception(
                "OpenRouter API call failed with status code "
                f"{response.status_code}: {message or response.text}"
            )

        choices = data.get("choices") or []
        if not choices:
            raise Exception(f"OpenRouter returned no choices: {data}")

        content = (choices[0].get("message") or {}).get("content")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type", "text") == "text"
            )
        if not content:
            raise Exception(f"OpenRouter returned an empty response: {data}")
        return content

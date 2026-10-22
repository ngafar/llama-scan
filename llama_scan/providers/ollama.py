import base64

import requests

from ..errors import ProviderError
from .base import TranscriptionProvider, build_prompt


class OllamaProvider(TranscriptionProvider):
    """Transcribe page images with a local Ollama server."""

    name = "ollama"
    default_model = "qwen2.5vl:latest"

    def __init__(self, server_url: str = "http://localhost:11434"):
        self.server_url = server_url.rstrip("/")

    def check(self) -> None:
        """Check if the Ollama server is running."""
        try:
            requests.get(f"{self.server_url}/api/tags", timeout=10)
        except requests.exceptions.RequestException as exc:
            raise ProviderError(
                "Ollama server not running. Please start the server and try again."
            ) from exc

    def transcribe_image(
        self,
        image_path: str,
        model: str,
        prompt: str | None = None,
    ) -> str:
        """
        Transcribe an image using the specified Ollama model.

        Args:
            image_path (str): Path to the image file.
            model (str): The model to use for transcription.
            prompt (str, optional): Prompt that replaces the default transcription prompt.
        """
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        payload = {
            "model": model,
            "prompt": build_prompt(prompt),
            "stream": False,
            "images": [image_data],
        }

        try:
            response = requests.post(f"{self.server_url}/api/generate", json=payload)
        except requests.exceptions.RequestException as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError(
                "Ollama returned a non-JSON response "
                f"({response.status_code}): {response.text}"
            ) from exc

        if response.status_code == 200:
            try:
                return data["response"]
            except KeyError as exc:
                raise ProviderError(
                    f"Ollama returned an unexpected response: {data}"
                ) from exc

        raise ProviderError(
            f"API call failed with status code {response.status_code}: {response.text}"
        )

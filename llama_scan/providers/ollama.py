import base64

import requests

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
        except requests.exceptions.RequestException:
            raise RuntimeError(
                "Ollama server not running. Please start the server and try again."
            )

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

        response = requests.post(f"{self.server_url}/api/generate", json=payload)

        if response.status_code == 200:
            return response.json()["response"]

        raise Exception(
            f"API call failed with status code {response.status_code}: {response.text}"
        )

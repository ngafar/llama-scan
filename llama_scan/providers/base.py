import base64
from pathlib import Path

from ..prompts import BASE_TRANSCRIPTION_PROMPT

_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class TranscriptionProvider:
    """A backend that transcribes a page image into text."""

    name: str
    default_model: str

    def check(self) -> None:
        """Raise if this provider is not ready to accept requests."""
        raise NotImplementedError

    def transcribe_image(
        self,
        image_path: str,
        model: str,
        prompt: str | None = None,
    ) -> str:
        """Transcribe one page image and return the text."""
        raise NotImplementedError


def build_prompt(prompt: str | None = None) -> str:
    """Return `prompt` when set, otherwise the default transcription prompt."""
    if prompt is not None and prompt.strip():
        return prompt.strip()
    return BASE_TRANSCRIPTION_PROMPT


def image_data_url(image_path: str) -> str:
    """Return the image at `image_path` as a base64 `data:` URL."""
    mime_type = _MIME_TYPES.get(Path(image_path).suffix.lower(), "image/png")
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{image_data}"


def chat_message_text(content) -> str | None:
    """Return the text of a chat completion message, joining text parts if listed."""
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type", "text") == "text"
        )
    return content

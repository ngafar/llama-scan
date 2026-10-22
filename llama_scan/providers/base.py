from ..prompts import BASE_TRANSCRIPTION_PROMPT


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

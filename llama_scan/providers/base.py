from ..constants import BASE_TRANSCRIPTION_PROMPT


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
        custom_instructions: str | None = None,
    ) -> str:
        """Transcribe one page image and return the text."""
        raise NotImplementedError


def build_prompt(custom_instructions: str | None) -> str:
    """Build the transcription prompt, appending any custom instructions."""
    prompt = BASE_TRANSCRIPTION_PROMPT
    if custom_instructions:
        prompt = prompt + f"\n\n{custom_instructions}"
    return prompt

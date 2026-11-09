import os

from ..errors import ProviderError
from .base import TranscriptionProvider, build_prompt, chat_message_text, image_data_url


class LiteLLMProvider(TranscriptionProvider):
    """
    Transcribe page images with any vision model LiteLLM supports.

    The model names the upstream provider, e.g. `anthropic/claude-sonnet-4-5`,
    `gemini/gemini-2.5-flash`, `bedrock/...`, `vertex_ai/...`, `azure/<deployment>`
    or `litellm_proxy/<alias>`, and LiteLLM reads that provider's credentials
    from its usual environment variables. `LITELLM_API_KEY` and
    `LITELLM_API_BASE` are optional and only sent when set, e.g. to use a
    LiteLLM proxy.
    """

    name = "litellm"
    default_model = "openai/gpt-4o-mini"

    def __init__(self):
        self.api_key = os.environ.get("LITELLM_API_KEY", "").strip()
        self.api_base = os.environ.get("LITELLM_API_BASE", "").strip().rstrip("/")

    def check(self) -> None:
        """Check that the litellm package is installed."""
        try:
            import litellm  # noqa: F401
        except ImportError as exc:
            raise ProviderError(
                "The litellm package is not installed. "
                "Install it with `pip install 'llama-scan[litellm]'` and try again."
            ) from exc

    def transcribe_image(
        self,
        image_path: str,
        model: str,
        prompt: str | None = None,
    ) -> str:
        """
        Transcribe an image using LiteLLM's chat completions API.

        Args:
            image_path (str): Path to the image file.
            model (str): LiteLLM model name, `<provider>/<model>`.
            prompt (str, optional): Prompt that replaces the default transcription prompt.
        """
        self.check()
        import litellm

        litellm.suppress_debug_info = True

        request = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_prompt(prompt)},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url(image_path)},
                        },
                    ],
                }
            ],
            "timeout": 300,
            # Skip parameters the selected model does not accept instead of failing.
            "drop_params": True,
        }
        if self.api_key:
            request["api_key"] = self.api_key
        if self.api_base:
            request["api_base"] = self.api_base

        try:
            response = litellm.completion(**request)
        except Exception as exc:
            message = getattr(exc, "message", None) or str(exc)
            raise ProviderError(
                f"LiteLLM request failed ({type(exc).__name__}): {message}"
            ) from exc

        choices = response.choices or []
        if not choices:
            raise ProviderError(f"LiteLLM returned no choices: {response}")

        content = chat_message_text(choices[0].message.content)
        if not content:
            raise ProviderError(f"LiteLLM returned an empty response: {response}")
        return content

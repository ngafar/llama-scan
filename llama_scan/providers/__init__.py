from .base import TranscriptionProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider

PROVIDERS: dict[str, type[TranscriptionProvider]] = {
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
}


def get_provider(
    name: str | None = None, *, server_url: str | None = None
) -> TranscriptionProvider:
    """
    Return the transcription provider for `name`.

    An omitted or blank name falls back to Ollama.
    """
    provider_name = (name or "ollama").strip().lower() or "ollama"
    provider_cls = PROVIDERS.get(provider_name)
    if provider_cls is None:
        known = ", ".join(PROVIDERS)
        raise ValueError(f"Unknown provider '{name}'. Available providers: {known}.")

    if provider_cls is OllamaProvider:
        return OllamaProvider(server_url=server_url or "http://localhost:11434")
    return provider_cls()

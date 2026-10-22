class LlamaScanError(Exception):
    """Base class for errors raised by llama-scan."""


class ProviderError(LlamaScanError):
    """A transcription provider failed to complete a request."""

"""Transcribe PDF pages with Ollama or OpenRouter."""

from .providers import PROVIDERS, TranscriptionProvider, get_provider
from .transcribe import PageTranscriptionError, process_pdf

__all__ = [
    "PROVIDERS",
    "PageTranscriptionError",
    "TranscriptionProvider",
    "get_provider",
    "process_pdf",
]

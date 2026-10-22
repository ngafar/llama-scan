"""Transcribe PDF pages with Ollama or OpenRouter."""

from .processor import PageTranscriptionError, process_pdf
from .providers import PROVIDERS, TranscriptionProvider, get_provider

__all__ = [
    "PROVIDERS",
    "PageTranscriptionError",
    "TranscriptionProvider",
    "get_provider",
    "process_pdf",
]

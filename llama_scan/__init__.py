"""Transcribe PDF pages with Ollama or OpenRouter."""

from .processor import process_pdf
from .providers import PROVIDERS, TranscriptionProvider, get_provider

__all__ = [
    "PROVIDERS",
    "TranscriptionProvider",
    "get_provider",
    "process_pdf",
]

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .processor import process_pdf
from .providers import PROVIDERS


def cli():
    parser = argparse.ArgumentParser(
        description="Convert PDF pages to images and transcribe them."
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the input PDF file",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help="Output directory (default: output_YYYYMMDD_HHMMSS)",
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="ollama",
        choices=list(PROVIDERS),
        help="Transcription provider (default: ollama)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help=(
            "Model to use. Defaults to qwen2.5vl:latest for Ollama and "
            "qwen/qwen2.5-vl-72b-instruct for OpenRouter."
        ),
    )
    parser.add_argument(
        "--start",
        "-s",
        type=int,
        default=0,
        help="Start page number (default: 0)",
    )
    parser.add_argument(
        "--end",
        "-e",
        type=int,
        default=0,
        help="End page number (default: 0)",
    )
    parser.add_argument(
        "--prompt",
        help="Path to a text file that replaces the default transcription prompt",
    )
    parser.add_argument(
        "--server-url",
        "-u",
        help="Ollama server URL (default: http://localhost:11434)",
        default="http://localhost:11434",
    )
    parser.add_argument(
        "--width",
        "-w",
        type=int,
        default=0,
        help="Width of the resized images. Set to 0 to skip resizing (default: 0)",
    )
    parser.add_argument(
        "--keep-images",
        "-k",
        action="store_true",
        default=False,
        help="Keep the intermediate image files (default: False)",
    )

    args = parser.parse_args()

    try:
        process_pdf(
            pdf_path=args.pdf_path,
            output_dir=args.output,
            provider=args.provider,
            model=args.model,
            prompt=_read_prompt(args.prompt),
            keep_images=args.keep_images,
            width=args.width,
            start=args.start,
            end=args.end,
            server_url=args.server_url,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _read_prompt(path: str | None) -> str | None:
    """Read a prompt file. Returns None when no path was given."""
    if not path:
        return None

    prompt_path = Path(path)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except OSError as e:
        raise OSError(f"Error reading prompt file: {e}") from e


if __name__ == "__main__":
    cli()

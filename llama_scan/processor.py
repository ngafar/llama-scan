import sys
from pathlib import Path
from tqdm import tqdm

from .providers import TranscriptionProvider, get_provider
from .utils import setup_output_dirs, merge_text_files, pdf_to_images, resize_image


def process_pdf(
    pdf_path: str | Path,
    output_dir: str | Path,
    *,
    provider: str | TranscriptionProvider = "ollama",
    model: str | None = None,
    custom_instructions: str | None = None,
    keep_images: bool = False,
    width: int = 0,
    start: int = 0,
    end: int = 0,
    server_url: str | None = None,
    show_progress: bool = True,
) -> Path:
    """
    Convert a PDF to page images and transcribe them.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory where images and text are written.
        provider: Provider name (`ollama` or `openrouter`) or a provider instance.
            Defaults to Ollama.
        model: Model to use. Defaults to the provider's model.
        custom_instructions: Extra prompt text appended to the transcription instructions.
        keep_images: Whether to keep the page images after processing.
        width: Resize images to this width. `0` leaves them unchanged.
        start: First page to process (1-based). `0` starts at the first page.
        end: Last page to process (1-based). `0` stops at the last page.
        server_url: Ollama server URL, used when `provider` is a name.
        show_progress: Whether to display progress bars.

    Returns:
        Path to the merged transcription, `output_dir/text/merged.txt`.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If the provider name or page range is invalid.
        RuntimeError: If the provider is unavailable or no pages were transcribed.
    """
    pdf_path = Path(pdf_path)
    output_base = Path(output_dir)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not isinstance(provider, TranscriptionProvider):
        provider = get_provider(provider, server_url=server_url)
    model = model or provider.default_model

    provider.check()
    print(f"Using {provider.name} ({model})", file=sys.stderr)

    image_dir, text_dir = setup_output_dirs(output_base)

    pdf_to_images(str(pdf_path), image_dir, start, end, show_progress=show_progress)

    image_files = sorted(image_dir.glob("page_*.png"))
    total_pages = len(image_files)

    if width > 0:
        for image_file in tqdm(
            image_files, desc="Resizing images", disable=not show_progress
        ):
            resize_image(str(image_file), str(image_file), width)

    for i, image_file in tqdm(
        enumerate(image_files, 1),
        desc="Transcribing pages",
        total=total_pages,
        disable=not show_progress,
    ):
        try:
            transcription = provider.transcribe_image(
                str(image_file),
                model=model,
                custom_instructions=custom_instructions,
            )

            text_file = text_dir / f"{image_file.stem}.txt"
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(transcription)
        except Exception as e:
            print(f"Error processing page {i}: {str(e)}", file=sys.stderr)

        if not keep_images:
            image_file.unlink()

    merged_file = merge_text_files(text_dir)
    print(f"Processing complete! Output saved to: {output_base}", file=sys.stderr)
    return merged_file

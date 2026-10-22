import sys
from pathlib import Path

from tqdm import tqdm

from .errors import LlamaScanError, ProviderError
from .providers import TranscriptionProvider, get_provider
from .utils import (
    clear_previous_outputs,
    merge_text_files,
    pdf_to_images,
    prepare_pdf,
    resize_image,
    setup_output_dirs,
)


class PageTranscriptionError(LlamaScanError):
    """One or more pages failed to transcribe."""

    def __init__(self, failures: list[tuple[int, str]]):
        self.failures = failures
        detail = ", ".join(f"page {number} ({message})" for number, message in failures)
        noun = "page" if len(failures) == 1 else "pages"
        super().__init__(f"Failed to transcribe {len(failures)} {noun}: {detail}")


def process_pdf(
    pdf_path: str | Path,
    output_dir: str | Path,
    *,
    provider: str | TranscriptionProvider = "ollama",
    model: str | None = None,
    prompt: str | None = None,
    keep_images: bool = False,
    width: int = 0,
    dpi: int = 72,
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
        prompt: Transcription prompt. When set, replaces the default book prompt.
        keep_images: Whether to keep the page images after processing.
        width: Resize images to this width. `0` leaves them unchanged.
        dpi: Resolution used when rendering PDF pages. Defaults to 72.
        start: First page to process (1-based). `0` starts at the first page.
        end: Last page to process (1-based). `0` stops at the last page.
        server_url: Ollama server URL, used when `provider` is a name.
        show_progress: Whether to display progress bars.

    Returns:
        Path to the merged transcription, `output_dir/text/merged.txt`.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If the provider name, page range, or DPI is invalid.
        ProviderError: If the provider is unavailable.
        RuntimeError: If no pages were transcribed.
        PageTranscriptionError: If any page fails. Pages that succeeded stay in
            `output_dir/text/`, and `merged.txt` is not written.
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

    doc, start_page, end_page = prepare_pdf(str(pdf_path), start, end, dpi)
    image_dir, text_dir = setup_output_dirs(output_base)
    try:
        clear_previous_outputs(image_dir, text_dir)
        image_files = pdf_to_images(
            doc,
            image_dir,
            start_page,
            end_page,
            show_progress=show_progress,
            dpi=dpi,
        )
    finally:
        doc.close()
    total_pages = len(image_files)

    if width > 0:
        for image_file in tqdm(
            image_files, desc="Resizing images", disable=not show_progress
        ):
            resize_image(str(image_file), str(image_file), width)

    failures: list[tuple[int, str]] = []
    for image_file in tqdm(
        image_files,
        desc="Transcribing pages",
        total=total_pages,
        disable=not show_progress,
    ):
        page_number = int(image_file.stem.removeprefix("page_"))
        try:
            transcription = provider.transcribe_image(
                str(image_file),
                model=model,
                prompt=prompt,
            )

            text_file = text_dir / f"{image_file.stem}.txt"
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(transcription)
        except (ProviderError, OSError) as e:
            message = str(e)
            failures.append((page_number, message))
            print(f"Error processing page {page_number}: {message}", file=sys.stderr)

        if not keep_images:
            image_file.unlink()

    if failures:
        raise PageTranscriptionError(failures)

    merged_file = merge_text_files(text_dir)
    print(f"Processing complete! Output saved to: {output_base}", file=sys.stderr)
    return merged_file

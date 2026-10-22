import io
import sys
from pathlib import Path

import pymupdf
from PIL import Image
from tqdm import tqdm

from .errors import LlamaScanError, ProviderError
from .providers import TranscriptionProvider, get_provider


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


def setup_output_dirs(output_base: Path) -> tuple[Path, Path]:
    """
    Create and return paths for image and text output directories.

    Args:
        output_base (Path): The base directory for output.
    """
    image_dir = output_base / "images"
    text_dir = output_base / "text"

    image_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    return image_dir, text_dir


def clear_previous_outputs(image_dir: Path, text_dir: Path) -> None:
    """Remove page images and transcription files left by a previous run."""
    for path in image_dir.glob("page_*.png"):
        path.unlink()
    for path in text_dir.glob("page_*.txt"):
        path.unlink()
    merged_file = text_dir / "merged.txt"
    if merged_file.exists():
        merged_file.unlink()


def prepare_pdf(
    pdf_path: str, start: int, end: int, dpi: int
) -> tuple[pymupdf.Document, int, int]:
    """
    Open a PDF and validate the render settings.

    Returns the open document and the normalized start and end pages. The caller
    closes the document.
    """
    if dpi <= 0:
        raise ValueError(f"DPI must be positive, got {dpi}.")

    doc = pymupdf.open(pdf_path)
    try:
        total_pages = len(doc)
        if start < 0 or (start > total_pages and start != 0):
            raise ValueError(
                f"Start page number {start} is out of range. Document has {total_pages} pages."
            )
        if end < 0 or (end > total_pages and end != 0):
            raise ValueError(
                f"End page number {end} is out of range. Document has {total_pages} pages."
            )
    except ValueError:
        doc.close()
        raise

    start = 1 if start == 0 else start
    end = total_pages if end == 0 else end
    return doc, start, end


def pdf_to_images(
    doc: pymupdf.Document,
    output_dir: Path,
    start: int,
    end: int,
    show_progress: bool = True,
    dpi: int = 72,
) -> list[Path]:
    """
    Render PDF pages to images.

    Args:
        doc (pymupdf.Document): Open PDF document.
        output_dir (Path): Directory where the images will be saved.
        start (int): First page to render (1-based).
        end (int): Last page to render (1-based).
        show_progress (bool): Whether to display a progress bar.
        dpi (int): Resolution used when rendering each page.

    Returns:
        Paths of the page images written for this run, in page order.
    """
    total_pages = len(doc)
    written_images: list[Path] = []
    for page_num in tqdm(
        range(start, end + 1),
        desc="Converting pages to images",
        total=end - start + 1,
        disable=not show_progress,
    ):
        page = doc[page_num - 1]  # Convert to 0-based index
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        n_digits = len(str(total_pages))
        output_path = output_dir / f"page_{page_num:0{n_digits}d}.png"
        img.save(str(output_path))
        written_images.append(output_path)

    return written_images


def resize_image(image_path: str, output_path: str, width: int) -> None:
    """
    Resize an image to the specified width while maintaining aspect ratio.

    Args:
        image_path (str): Path to the input image file
        output_path (str): Path where the resized image will be saved
        width (int): Desired width of the image
    """
    if width == 0:
        return
    else:
        img = Image.open(image_path)
        w_percent = width / float(img.size[0])
        h_size = int(float(img.size[1]) * float(w_percent))
        img = img.resize((width, h_size), Image.Resampling.LANCZOS)
        img.save(output_path)


def merge_text_files(text_dir: Path) -> Path:
    """
    Merge all individual text files into a single merged file.

    Args:
        text_dir (Path): Directory containing individual text files.

    Returns:
        Path: Path to the created merged file.
    """
    text_files = sorted(text_dir.glob("page_*.txt"))
    merged_file = text_dir / "merged.txt"
    text_from_files = []

    if not text_files:
        raise RuntimeError("No text files found")

    for text_file in text_files:
        content = text_file.read_text(encoding="utf-8", errors="replace").strip()
        text_from_files.append(content)

    merged_text = "\n\n".join(text_from_files)
    merged_file.write_text(merged_text, encoding="utf-8")

    return merged_file

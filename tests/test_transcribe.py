from pathlib import Path

import pymupdf
from PIL import Image

from llama_scan import PageTranscriptionError, process_pdf
from llama_scan.errors import ProviderError
from llama_scan.providers import TranscriptionProvider


class FakeProvider(TranscriptionProvider):
    name = "fake"
    default_model = "fake-model"

    def __init__(self, fail_pages=()):
        self.fail_pages = set(fail_pages)
        self.prompts = []

    def check(self):
        return None

    def transcribe_image(self, image_path, model, prompt=None):
        self.prompts.append(prompt)
        page = int(Path(image_path).stem.removeprefix("page_"))
        if page in self.fail_pages:
            raise ProviderError(f"boom {page}")
        return f"text {page}"


def write_pdf(path, pages=1):
    doc = pymupdf.open()
    for _ in range(pages):
        doc.new_page(width=612, height=792)
    doc.save(path)
    doc.close()


def seed_previous_output(output_dir):
    text_dir = output_dir / "text"
    image_dir = output_dir / "images"
    text_dir.mkdir(parents=True)
    image_dir.mkdir()
    (text_dir / "page_1.txt").write_text("old page 1")
    (text_dir / "page_9.txt").write_text("old page 9")
    (text_dir / "merged.txt").write_text("old merge")
    (image_dir / "page_01.png").write_bytes(b"old-padded")
    (image_dir / "page_9.png").write_bytes(b"old-extra")


def test_successful_run_merges_pages_in_order(tmp_path):
    pdf_path = tmp_path / "book.pdf"
    write_pdf(pdf_path, pages=2)

    merged = process_pdf(
        pdf_path,
        tmp_path / "out",
        provider=FakeProvider(),
        show_progress=False,
    )

    assert merged.read_text() == "text 1\n\ntext 2"


def test_failed_page_raises_and_skips_merge(tmp_path):
    pdf_path = tmp_path / "book.pdf"
    write_pdf(pdf_path, pages=2)
    output_dir = tmp_path / "out"

    try:
        process_pdf(
            pdf_path,
            output_dir,
            provider=FakeProvider(fail_pages={2}),
            show_progress=False,
        )
    except PageTranscriptionError as exc:
        assert exc.failures == [(2, "boom 2")]
    else:
        raise AssertionError("expected PageTranscriptionError")

    text_dir = output_dir / "text"
    assert (text_dir / "page_1.txt").read_text() == "text 1"
    assert not (text_dir / "page_2.txt").exists()
    assert not (text_dir / "merged.txt").exists()


def test_reused_directory_drops_previous_pages(tmp_path):
    pdf_path = tmp_path / "book.pdf"
    write_pdf(pdf_path, pages=2)
    output_dir = tmp_path / "out"
    seed_previous_output(output_dir)

    merged = process_pdf(
        pdf_path,
        output_dir,
        provider=FakeProvider(),
        keep_images=True,
        show_progress=False,
    )

    assert merged.read_text() == "text 1\n\ntext 2"
    assert not (output_dir / "text" / "page_9.txt").exists()
    names = sorted(path.name for path in (output_dir / "images").glob("page_*.png"))
    assert names == ["page_1.png", "page_2.png"]


def test_early_failure_keeps_previous_output(tmp_path):
    pdf_path = tmp_path / "book.pdf"
    write_pdf(pdf_path, pages=1)
    output_dir = tmp_path / "out"
    seed_previous_output(output_dir)

    try:
        process_pdf(
            pdf_path,
            output_dir,
            provider=FakeProvider(),
            dpi=0,
            show_progress=False,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid dpi")

    assert (output_dir / "text" / "page_1.txt").read_text() == "old page 1"
    assert (output_dir / "text" / "merged.txt").read_text() == "old merge"
    assert (output_dir / "images" / "page_9.png").read_bytes() == b"old-extra"


def test_prompt_is_passed_to_the_provider(tmp_path):
    pdf_path = tmp_path / "book.pdf"
    write_pdf(pdf_path)
    provider = FakeProvider()

    process_pdf(
        pdf_path,
        tmp_path / "out",
        provider=provider,
        prompt="Keep the letterhead.",
        show_progress=False,
    )

    assert provider.prompts == ["Keep the letterhead."]


def test_dpi_changes_rendered_image_size(tmp_path):
    pdf_path = tmp_path / "book.pdf"
    write_pdf(pdf_path)
    output_dir = tmp_path / "out"

    process_pdf(
        pdf_path,
        output_dir,
        provider=FakeProvider(),
        dpi=144,
        keep_images=True,
        show_progress=False,
    )

    image = Image.open(output_dir / "images" / "page_1.png")
    assert image.size == (1224, 1584)

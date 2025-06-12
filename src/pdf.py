import io
import pymupdf
from PIL import Image
from pathlib import Path


def pdf_to_images(pdf_path: str, output_dir: Path) -> None:
    """
    Convert PDF pages to images and save them to the specified output directory.

    Args:
        pdf_path (str): Path to the input PDF file
        output_dir (Path): Directory where the images will be saved
    """
    doc = pymupdf.open(pdf_path)

    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        output_path = output_dir / f"page_{page.number}.png"
        img.save(str(output_path))

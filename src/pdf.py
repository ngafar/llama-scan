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
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((width, h_size), Image.Resampling.LANCZOS)
        img.save(output_path)

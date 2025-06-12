import io
import pymupdf
from PIL import Image
from pathlib import Path


def pdf_to_images(pdf_path: str, output_dir: Path, page: int = 0) -> None:
    """
    Convert PDF pages to images and save them to the specified output directory.

    Args:
        pdf_path (str): Path to the input PDF file
        output_dir (Path): Directory where the images will be saved
        page (int): The page number to convert. If 0, converts all pages.
    """
    doc = pymupdf.open(pdf_path)

    if page == 0:
        # Convert all pages
        for page in doc:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            output_path = output_dir / f"page_{page.number + 1}.png"
            img.save(str(output_path))
    else:
        # Convert single specified page
        if page > len(doc) or page < 1:
            raise ValueError(
                f"Page number {page} is out of range. Document has {len(doc)} pages."
            )

        page = doc[page - 1]  # Convert to 0-based index
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        output_path = output_dir / f"page_{page.number + 1}.png"
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

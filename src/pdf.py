import io
import pymupdf
from PIL import Image


def pdf_to_images(pdf_path):
    doc = pymupdf.open(pdf_path)

    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img.save(f"page_{page.number}.png")

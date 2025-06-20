import sys
from pathlib import Path
from tqdm import tqdm

from .pdf import pdf_to_images, resize_image
from .transcriber import transcribe_image
from .utils import setup_output_dirs, merge_text_files


def process_pdf(
    pdf_path: str,
    output_dir: str,
    model: str = "qwen2.5vl:latest",
    keep_images: bool = False,
    width: int = 500,
    start: int = 0,
    end: int = 0,
    merge_text: bool = False,
) -> None:
    """
    Process a PDF file, converting pages to images and transcribing them.

    Args:
        pdf_path (str): The path to the PDF file.
        output_dir (str): The directory to save the output.
        model (str): The model to use for transcription.
        keep_images (bool): Whether to keep the images after processing.
        width (int): The width of the resized images.
        start (int): The start page number.
        end (int): The end page number.
        merge_text (bool): Whether to merge all text files into a single file.
    """
    pdf_path = Path(pdf_path)
    output_base = Path(output_dir)

    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    # Setup output directories
    image_dir, text_dir = setup_output_dirs(output_base)

    try:
        # Convert PDF to images
        pdf_to_images(str(pdf_path), image_dir, start, end)

        # Process each page
        image_files = sorted(image_dir.glob("page_*.png"))
        total_pages = len(image_files)

        # Resize images to 500px width
        if width > 0:
            for image_file in tqdm(image_files, desc="Resizing images"):
                resize_image(str(image_file), str(image_file), width)
        else:
            pass  # Skip resizing

        for i, image_file in tqdm(
            enumerate(image_files, 1),
            desc="Transcribing pages",
            total=total_pages,
        ):
            # Transcribe the image
            try:
                text = transcribe_image(str(image_file), model=model)

                # Save transcription
                text_file = text_dir / f"{image_file.stem}.txt"
                with open(text_file, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception as e:
                print(f"Error processing page {i}: {str(e)}")

            # Clean up image if not keeping them
            if not keep_images:
                image_file.unlink()

        # Merge text files if requested
        if merge_text:
            merged_file = merge_text_files(text_dir)
            print(f"Merged text file created: {merged_file}")

        print(f"Processing complete! Output saved to: {output_base}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

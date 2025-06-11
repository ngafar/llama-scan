import sys
from pathlib import Path

from src.pdf import pdf_to_images
from src.transcriber import transcribe_image
from src.utils import setup_output_dirs


def process_pdf(
    pdf_path: str,
    output_dir: str,
    model: str = "qwen2.5vl:latest",
    keep_images: bool = False,
) -> None:
    """Process a PDF file, converting pages to images and transcribing them."""
    pdf_path = Path(pdf_path)
    output_base = Path(output_dir)

    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    # Setup output directories
    image_dir, text_dir = setup_output_dirs(output_base)

    try:
        # Convert PDF to images
        print(f"Converting PDF to images...")
        pdf_to_images(str(pdf_path), image_dir)

        # Process each page
        image_files = sorted(image_dir.glob("page_*.png"))
        total_pages = len(image_files)

        print(f"\nProcessing {total_pages} pages...")
        for i, image_file in enumerate(image_files, 1):
            print(f"\nProcessing page {i}/{total_pages}")

            # Transcribe the image
            try:
                text = transcribe_image(str(image_file), model=model)

                # Save transcription
                text_file = text_dir / f"{image_file.stem}.txt"
                with open(text_file, "w") as f:
                    f.write(text)

                print(f"✓ Page {i} transcribed successfully")

            except Exception as e:
                print(f"✗ Error processing page {i}: {str(e)}")

            # Clean up image if not keeping them
            if not keep_images:
                image_file.unlink()

        print(f"\nProcessing complete! Output saved to: {output_base}")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 
import argparse

from .processor import process_pdf


def cli():
    parser = argparse.ArgumentParser(
        description="Convert PDF pages to images and transcribe them using Ollama."
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the input PDF file",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output",
        help="Output directory (default: output)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="qwen2.5vl:latest",
        help="Ollama model to use (default: qwen2.5vl:latest)",
    )
    parser.add_argument(
        "--keep-images",
        "-k",
        action="store_true",
        help="Keep the intermediate image files",
    )
    parser.add_argument(
        "--width",
        "-w",
        type=int,
        default=0,
        help="Width of the resized images. Set to 0 to skip resizing.",
    )
    parser.add_argument(
        "--start",
        "-s",
        type=int,
        default=0,
        help="Start page number (default: 0).",
    )
    parser.add_argument(
        "--end",
        "-e",
        type=int,
        default=0,
        help="End page number (default: 0).",
    )
    parser.add_argument(
        "--merge-text",
        "-mt",
        action="store_true",
        help="Merge all individual text files into a single merged file",
    )

    args = parser.parse_args()

    process_pdf(
        pdf_path=args.pdf_path,
        output_dir=args.output,
        model=args.model,
        keep_images=args.keep_images,
        width=args.width,
        start=args.start,
        end=args.end,
        merge_text=args.merge_text,
    )


if __name__ == "__main__":
    cli()

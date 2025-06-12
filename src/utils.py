from pathlib import Path


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

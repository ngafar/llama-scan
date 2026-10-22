# llama-scan

A tool for converting PDFs to text files using Ollama or OpenRouter.

## Features

- Convert PDFs to text files locally, no token costs.
- Use the latest multimodal models supported by Ollama and OpenRouter.
- Turn images and diagrams into detailed text descriptions.

## Requirements

- Python 3.10+
- Ollama installed and running locally, unless you select another provider.
- An OpenRouter API key in `OPENROUTER_API_KEY` when using `--provider openrouter` .

### Installing Ollama and the Default Model

1. Install [Ollama](https://ollama.com/)
2. Pull the default model:

```bash
ollama run qwen2.5vl:latest
```

## Installation

Install using pip:

```bash
pip install llama-scan
```

or uv:

```bash
uv tool install llama-scan
```

## Usage

Basic usage:

```bash
llama-scan path/to/your/file.pdf
```

### Options

| Option                        | Description                                                     | Default                     |
| ----------------------------- | --------------------------------------------------------------- | --------------------------- |
| `--provider`, `-p`            | Transcription provider, `ollama` or `openrouter`                | `ollama`                    |
| `--output`, `-o`              | Output directory                                                | `output/`                   |
| `--model`, `-m`               | Model to use                                                    | `qwen2.5vl:latest` (Ollama) |
| `--start`, `-s`               | Start page number                                               | 0                         |
| `--end`, `-e`                 | End page number                                                 | 0                         |
| `--custom-instructions`, `-c` | Optional path to a text file containing additional instructions | None                        |
| `--server-url`, `-u`          | Ollama server URL                                               | `http://localhost:11434`    |
| `--width`, `-w`               | Width of the resized images (0 to skip resizing)                | 0                         |
| `--keep-images`, `-k`         | Keep the intermediate image files                               | `False`                     |

### Examples

Process specific pages:

```bash
llama-scan document.pdf --start 1 --end 5
```

Use a different Ollama model:

```bash
llama-scan document.pdf --model qwen2.5vl:3b
```

## Python

Import `process_pdf` to run the same transcription from Python. It writes the page text and `text/merged.txt` under `output_dir`, and returns the path to the merged file. `provider` defaults to `ollama`. `custom_instructions` is the instruction text, not a file path.

```python
from llama_scan import process_pdf

merged = process_pdf("document.pdf", "output")
print(merged.read_text(encoding="utf-8"))
```

```python
merged = process_pdf(
    "document.pdf",
    "output",
    provider="openrouter",
    start=1,
    end=5,
)
```

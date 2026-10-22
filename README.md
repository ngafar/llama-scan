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

Process specific pages:

```bash
llama-scan document.pdf --start 1 --end 5
```

Use a different model (Ollama):

```bash
llama-scan document.pdf --model qwen2.5vl:3b
```

### Options

The following options can be used to customize PDF processing.

**General**

| Option | Description | Default |
|---|---|---|
| `--output`, `-o` | Directory where results are saved | `output/` |
| `--start`, `-s` | First page to process | `0` |
| `--end`, `-e` | Last page to process | `0` |

**Model configuration**

| Option               | Description                                                        | Default                     |
| -------------------- | ------------------------------------------------------------------ | --------------------------- |
| `--provider`, `-p`   | Transcription provider (`ollama` or `openrouter`)                  | `ollama`                    |
| `--model`, `-m`      | Model used for transcription                                       | `qwen2.5vl:latest` (Ollama) |
| `--server-url`, `-u` | Ollama server URL                                                  | `http://localhost:11434`    |
| `--prompt`           | Path to a text file that replaces the default transcription prompt |                             |

**Image processing**

| Option | Description | Default |
|---|---|---|
| `--width`, `-w` | Resize images to the specified width (`0` disables resizing) | `0` |
| `--dpi` | Resolution used when rendering PDF pages | `72` |
| `--keep-images`, `-k` | Keep intermediate image files | `False` |

## Python API

In addition to the command-line interface (CLI), llama-scan can be used directly in Python scripts. This allows you to integrate PDF processing into your own applications and workflows.

```python
from llama_scan import process_pdf

merged = process_pdf("document.pdf", "output")
print(merged.read_text(encoding="utf-8"))
```

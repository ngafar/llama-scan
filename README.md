# llama-scan

A tool for converting PDFs to text files using Ollama.

## Features

- Convert PDFs to text files locally, no token costs.
- Use the latest multimodal models supported by Ollama.
- Turn images and diagrams into detailed text descriptions.

## Requirements

- Python 3.10+
- Ollama installed and running locally, unless you select another provider
- An OpenRouter API key in `OPENROUTER_API_KEY` when using `--provider openrouter`

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

- `--provider`, `-p`: Transcription provider, `ollama` or `openrouter` (default: `ollama`)
- `--output`, `-o`: Output directory (default: "output")
- `--model`, `-m`: Model to use (default: `qwen2.5vl:latest` for Ollama, `qwen/qwen2.5-vl-72b-instruct` for OpenRouter)
- `--start`, `-s`: Start page number (default: 0)
- `--end`, `-e`: End page number (default: 0)
- `--custom-instructions`, `-c`: Optional path to a text file containing additional instructions (default: None)
- `--server-url`, `-u`: Ollama server URL (default: "http://localhost:11434")
- `--width`, `-w`: Width of the resized images (0 to skip resizing; default: 0)
- `--keep-images`, `-k`: Keep the intermediate image files (default: False)
- `--stdout`: Write merged output to stdout (default: False)

### Examples

Process specific pages:
```bash
llama-scan document.pdf --start 1 --end 5
```

Use a different Ollama model:
```bash
llama-scan document.pdf --model qwen2.5vl:3b
```

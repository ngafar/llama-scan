# llama-scan

A tool for converting PDFs to text files using Ollama.

## Features

- Convert PDFs to text files locally, no token costs.
- Use the latest multimodal models supported by Ollama.
- Turn images and diagrams into detailed text descriptions.
- Optional settings to optimize performance.

## Requirements

- Python 3.x
- Ollama installed and running locally

### Installing Ollama and the Default Model

1. Install [Ollama](https://ollama.com/)
2. Pull the default model:
```bash
ollama run qwen2.5vl:latest
```

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python main.py path/to/your/file.pdf
```

### Options

- `--output`, `-o`: Output directory (default: "output")
- `--model`, `-m`: Ollama model to use (default: "qwen2.5vl:latest")
- `--keep-images`, `-k`: Keep the intermediate image files (default: False)
- `--width`, `-w`: Width of the resized images (0 to skip resizing; default: 0)
- `--start`, `-s`: Start page number (default: 0)
- `--end`, `-e`: End page number (default: 0)

### Examples

Process specific pages with custom width:
```bash
python main.py document.pdf --start 1 --end 5 --width 1000
```

Use a different Ollama model:
```bash
python main.py document.pdf --model qwen2.5vl:3b
```

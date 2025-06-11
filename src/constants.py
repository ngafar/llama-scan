OLLAMA_BASE_URL = "http://localhost:11434/api"

TRANSCRIPTION_PROMPT = """Task: Transcribe the page from the provided book image.

- Reproduce the text exactly as it appears, without adding or omitting anything.
- Use Markdown syntax to preserve the original formatting (e.g., headings, bold, italics, lists).
- If the page contains an image, describe it in a sentence and enclose the description in an <image> tag.
- Do not include triple backticks (```) or any other code block markers in your response, unless the page contains code.
"""








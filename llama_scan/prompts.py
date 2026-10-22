BASE_TRANSCRIPTION_PROMPT = """Task: Transcribe the page from the provided book image.

- Reproduce the text exactly as it appears, without adding or omitting anything.
- Use Markdown syntax to preserve the original formatting (e.g., headings, bold, italics, lists).
- Do not include triple backticks (```) or any other code block markers in your response, unless the page contains code.
- Do not include any headers or footers (for example, page numbers).
- If the page contains an image, or a diagram, describe it in detail. Enclose the description in an <image> tag. For example:

<image>
This is an image of a cat.
</image>

"""

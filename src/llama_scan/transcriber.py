import base64
import requests

from .constants import OLLAMA_BASE_URL, TRANSCRIPTION_PROMPT


def transcribe_image(image_path: str, model: str) -> str:
    """
    Transcribe an image using the specified model.

    Args:
        image_path (str): Path to the image file.
        model (str): The model to use for transcription.
    """
    # Read and encode the image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Prepare the request payload
    payload = {
        "model": model,
        "prompt": TRANSCRIPTION_PROMPT,
        "stream": False,
        "images": [image_data],
    }

    # Make the API call
    response = requests.post(f"{OLLAMA_BASE_URL}/generate", json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()["response"]
    else:
        raise Exception(
            f"API call failed with status code {response.status_code}: {response.text}"
        )

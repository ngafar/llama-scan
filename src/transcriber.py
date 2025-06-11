import base64
import requests

DEFAULT_MODEL = "qwen2.5vl:latest"
OLLAMA_BASE_URL = "http://localhost:11434/api"


def transcribe_image(image_path, model=DEFAULT_MODEL):
    # Read and encode the image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Prepare the request payload
    payload = {
        "model": model,
        "prompt": "How much is this check for?",
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

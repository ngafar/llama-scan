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
        "prompt": "The image provided is a page from a book. Please transcribe the text in the image exactly as it is written. Do not add any additional text or formatting. You may use markdown formatting for lists, bold, italics, etc. If there is an image on the page, please describe it. The image description should be placed in an <image> tag. Do not include the ```markdown or ``` tags in your response.",
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

import base64
from mimetypes import guess_type
from plantweb.render import render
import os

# Function to encode a local image into data URL 
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"

def plantuml_to_base64(plantuml_syntax: str, format: str = 'svg') -> str:
    if format not in ['svg', 'png']:
        raise ValueError("Format must be 'svg' or 'png'")
    diagram = render(plantuml_syntax, engine='plantuml', format=format)
    return (diagram[0], base64.b64encode(diagram[0]).decode('utf-8'))

def get_sample_sketches(sketch_name=None):
    if not sketch_name:
        sketches = []
        for file in os.listdir("samples"):
            if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
                sketches.append(file)
        return sketches
    else:
        with open(os.path.join("samples", sketch_name), "rb") as f:
            return f.read()

def get_sample_texts(text=None):
    texts = [
        {"display_text": "JSON Web Tokens", "description": "How does JWT work?"},
        {"display_text": "Docker Architecture", "description": "Explain the architecture of Docker."},
        {"display_text": "Home Automation System", "description": "Design a home automation system."},
        {"display_text": "UPI Payment Flow", "description": "Explain the flow of UPI payments."},
        {"display_text": "Image Generation Process Description", "description": """Image Generation Process Description:
- Prompt Preparation: Create and evaluate a descriptive text prompt.
- Refinement: If the prompt isn’t ready, refine it and re-evaluate.
- API Interaction: If the prompt is ready, invoke the OpenAI API for image generation.
- Image Generation Loop:
  - Up to three attempts to generate an image.
  - Assess image quality after each attempt.
  - If satisfactory, finalize and save the image.
  - If unsatisfactory, increment the attempt counter and retry.
- Termination: End the process when an image is finalized or all attempts are used."""}
    ]
    if text:
        return next((item["description"] for item in texts if item["display_text"] == text), None)
    else:
        return texts

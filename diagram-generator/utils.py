import base64
from mimetypes import guess_type
from typing import Dict, List
from plantweb.render import render
import os

def local_image_to_data_url(image_path: str):
    """
    Converts a local image file to a data URL.
    Args:
        image_path (str): The file path to the local image.
    Returns:
        str: The data URL representing the image.
    Raises:
        FileNotFoundError: If the image file does not exist.
        IOError: If there is an error reading the image file.
    Example:
        >>> data_url = local_image_to_data_url('/path/to/image.png')
        >>> print(data_url)
        'data:image/png;base64,...'
    """
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found

    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

    return f"data:{mime_type};base64,{base64_encoded_data}"

def plantuml_to_base64(plantuml_syntax: str, format: str = 'svg') -> str:
    """
    Converts PlantUML syntax to a base64 encoded string.

    Args:
        plantuml_syntax (str): The PlantUML syntax to be converted.
        format (str, optional): The format of the output diagram. Must be 'svg' or 'png'. Defaults to 'svg'.

    Returns:
        str: A tuple containing the raw diagram data and its base64 encoded string.

    Raises:
        ValueError: If the format is not 'svg' or 'png'.
    """
    if format not in ['svg', 'png']:
        raise ValueError("Format must be 'svg' or 'png'")
    diagram = render(plantuml_syntax, engine='plantuml', format=format)
    return (diagram[0], base64.b64encode(diagram[0]).decode('utf-8'))

def get_sample_sketches(sketch_name: str|None = None) -> List[str] | bytes:
    """
    Retrieve sample sketches from the 'samples' directory.

    If no sketch name is provided, this function returns a list of all sketch filenames
    with extensions .png, .jpg, or .jpeg in the 'samples' directory.

    If a sketch name is provided, this function returns the binary content of the specified sketch file.

    Args:
        sketch_name (str, optional): The name of the sketch file to retrieve. Defaults to None.

    Returns:
        list or bytes: A list of sketch filenames if no sketch name is provided, or the binary content of the specified sketch file.
    """
    if not sketch_name:
        sketches = []
        for file in os.listdir("samples"):
            if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
                sketches.append(file)
        return sketches
    else:
        with open(os.path.join("samples", sketch_name), "rb") as f:
            return f.read()

def get_sample_texts(text: str|None = None) -> List[Dict[str, str]]|str|None:
    """
    Retrieve sample texts or descriptions based on the provided display text.

    This function returns a list of sample texts with their descriptions if no
    specific text is provided. If a specific display text is provided, it returns
    the corresponding description.

    Args:
        text (str, optional): The display text to search for. Defaults to None.

    Returns:
        list or str: A list of dictionaries containing display texts and descriptions
                     if no text is provided. If a specific text is provided, returns
                     the corresponding description as a string, or None if not found.
    """
    texts = [
        {"display_text": "JSON Web Tokens", "description": "How does JWT work?"},
        {"display_text": "Kubernetes Architecture", "description": "Explain the high-level architecture of Kubernetes."},
        {"display_text": "HTTP/3 Protocol", "description": "Explain the overall flow of HTTP/3 protocol."},
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
- Termination: End the process when an image is finalized or all attempts are used."""},
        {"display_text": "Concept for System Design Interview", "description": "Mindmap of the key concepts to study for a system design interview."},
    ]
    if text:
        return next((item["description"] for item in texts if item["display_text"] == text), None)
    else:
        return texts

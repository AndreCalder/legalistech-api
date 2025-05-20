from google.cloud import vision
from google.cloud.vision_v1 import types
import io
import base64
from controllers.util.pdftoimg import pdf_to_images
import os
import tempfile
import json


def image_to_base64(image):
    """Convert a PIL Image to base64-encoded string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # Save the image in a byte buffer
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


# Get the absolute path to the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the full path to the JSON file
json_path = os.path.join(current_dir, "service_key.json")

with open(json_path) as f:
    account_info = json.load(f)


def send_images_to_vision(images):
    """Send an array of base64-encoded images to Google Cloud Vision."""
    client = vision.ImageAnnotatorClient.from_service_account_info(account_info)
    all_texts = []
    for idx, img in enumerate(images):
        # Convert the PIL image to base64
        img_base64 = image_to_base64(img)

        # Create the image request for Vision API
        image = vision.Image(content=img_base64)

        # Perform text detection (or other types like label detection)
        response = client.text_detection(image=image)
        texts = response.text_annotations

        doc_text = " ".join([text.description for text in texts])
        all_texts.append(doc_text)

    document_text = " ".join(all_texts)
    return document_text


output_folder = tempfile.mkdtemp()

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)


def scan_pdf_to_text(pdf_file):
    images = pdf_to_images(pdf_file)
    return send_images_to_vision(images[:-2])

# Change Log
# - Added Google Cloud Vision API integration for OCR processing of PDF files.
# === Andre - Moved file opening to top for better readability and performance.
# - Implemented `scan_pdf_to_text` function to convert PDF files to images and extract text using Vision API.
# - Utilized `ThreadPoolExecutor` for parallel processing of images to improve performance.
# - Added utility functions for image conversion and OCR processing.

from google.cloud import vision
import io
import base64
from controllers.util.pdftoimg import pdf_to_images
import os
import tempfile
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud.vision import Image as VisionImage

current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the full path to the JSON file
json_path = os.path.join(current_dir, "service_key.json")

with open(json_path) as f:
    account_info = json.load(f)

vision_client = vision.ImageAnnotatorClient.from_service_account_info(account_info)


def image_to_base64(image):
    """Convert a PIL Image to base64-encoded string."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # Save the image in a byte buffer
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def _ocr_image(img):
    """
    Helper que convierte una PIL.Image a texto usando Vision API.
    """
    # 1) Convertir la imagen a bytes (evita Base64 extra, usa BytesIO)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    content = buf.getvalue()

    # 2) Construir la petición
    vision_img = VisionImage(content=content)

    # 3) Llamar a OCR
    response = vision_client.text_detection(image=vision_img)
    texts = response.text_annotations or []

    # 4) Devolver el texto concatenado
    return " ".join(text.description for text in texts)


def send_images_to_vision(images, max_workers=10):
    """
    Procesa una lista de PIL.Images en paralelo, haciendo OCR en cada una.
    """
    all_texts = []

    # 1) Creamos el pool de hilos
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        texts = list(executor.map(_ocr_image, images))
    print(" ".join(texts))
    return " ".join(texts)


output_folder = tempfile.mkdtemp()

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)


def scan_pdf_to_text(pdf_file):
    # Convert PDF File to images
    images = pdf_to_images(pdf_file)

    return send_images_to_vision(images)

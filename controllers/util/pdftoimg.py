import fitz  # PyMuPDF
from PIL import Image
import io

def pdf_to_images(pdf_document):
  doc = fitz.open(pdf_document)
  images = []
  # Extract text from each page
  for page_num in range(len(doc)):
      page = doc.load_page(page_num)
      pix = page.get_pixmap()
      image_bytes = pix.tobytes() 
      image = Image.open(io.BytesIO(image_bytes)) 
      
      images.append(image)
  
  doc.close()
  return images
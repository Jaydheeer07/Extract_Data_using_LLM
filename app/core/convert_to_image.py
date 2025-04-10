import logging
import io
import fitz  # PyMuPDF
from PIL import Image
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def process_file_to_images(file_bytes, file_type):
    """Convert uploaded file (PDF or image) to a list of PIL Images"""
    if file_type == "pdf":
        return pdf_to_image(file_bytes)
    else:
        return [image_to_pil(file_bytes)]

def pdf_to_image(pdf_bytes):
    """Convert PDF bytes to a list of PIL Images"""
    images = []
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(pdf_document) == 0:
            raise ValueError("PDF document is empty")
            
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images
    except fitz.FileDataError as e:
        logger.error("Invalid PDF file: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    except Exception as e:
        logger.error("Error converting PDF to image: %s", str(e))
        raise HTTPException(status_code=500, detail="Error processing PDF file")

def image_to_pil(image_bytes):
    """Convert image bytes to PIL Image"""
    try:
        # Handle both BytesIO objects and raw bytes
        if isinstance(image_bytes, io.BytesIO):
            # If it's already a BytesIO object, use it directly
            image_bytes.seek(0)  # Reset position to the start
            return Image.open(image_bytes)
        else:
            # If it's raw bytes, wrap in BytesIO
            return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        logger.error("Error processing image file: %s", str(e))
        raise HTTPException(status_code=400, detail="Invalid image file")
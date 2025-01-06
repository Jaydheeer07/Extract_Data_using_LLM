import logging
import fitz  # PyMuPDF
from PIL import Image
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def pdf_to_image(pdf_bytes):
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
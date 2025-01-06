import logging

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from app.core.convert_to_image import pdf_to_image
from app.core.llm import extract_info, parse_and_validate_llm_output

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Step 1: Read the PDF file
        pdf_bytes = await file.read()
        logger.info("Received PDF file: %s", file.filename)

        # Step 2: Convert PDF to images
        images = pdf_to_image(pdf_bytes)
        logger.info("Converted PDF to %d images", len(images))

        # Step 3: Send the first image to the LLM (assuming single-page invoices)
        if not images:
            raise HTTPException(status_code=400, detail="No images were extracted from the PDF")
            
        extracted_info = extract_info(images[0])
        logger.info("Extracted info: %s", str(extracted_info))

        # Step 4: Parse and validate the LLM output
        parsed_info = parse_and_validate_llm_output(extracted_info)
        logger.info("Parsed info: %s", str(parsed_info))

        # Step 5: Return the JSON response
        if isinstance(parsed_info, dict) and "error" in parsed_info:
            return JSONResponse(content={"error": parsed_info["error"]}, status_code=400)
        return JSONResponse(content=parsed_info.model_dump(), status_code=200)
        
    except HTTPException as e:
        logger.error("HTTP error in upload endpoint: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.error("Unexpected error in upload endpoint: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

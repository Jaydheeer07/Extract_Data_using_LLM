# PDF Data Extraction with LLM

A FastAPI application that extracts structured data from invoice and statement PDFs using OpenAI's GPT-4 Vision API. The application converts PDF documents to images and uses advanced AI to accurately extract key information such as invoice numbers, dates, amounts, and line items.

## Features

- PDF to Image conversion using PyMuPDF
- Support for both invoices and statements
- Structured data extraction with GPT-4 Vision API
- JSON response with validated data structure
- Comprehensive error handling and logging
- Decimal precision for financial amounts
- Support for line items with GST

## Requirements

```txt
fastapi
uvicorn
python-multipart
openai
PyMuPDF
Pillow
pydantic
python-dateutil
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables:
   ```bash
   OPENAI_API_KEY=your_api_key
   OPENAI_ORGANIZATION=your_org_id  # Optional
   ```

## API Endpoints

### POST /upload
Upload a PDF file (invoice or statement) for data extraction.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (PDF file)

**Response:**
```json
{
    "document_type": "invoice" | "statement",
    "invoice_number": string | null,
    "invoice_date": "YYYY-MM-DD" | null,
    "total_amount": number,
    "vendor_name": string,
    "customer_name": string,
    "due_date": "YYYY-MM-DD" | null,
    "tax_amount": number | null,
    "PO_number": string | null,
    "statement_date": "YYYY-MM-DD" | null,
    "reference": string | null,
    "statement_due_date": "YYYY-MM-DD" | null,
    "line_items": [
        {
            "description": string,
            "quantity": number | null,
            "unit_price": number | null,
            "total_price": number,
            "gst": number | null
        }
    ] | null
}
```

## Project Structure

```
app/
├── core/
│   ├── convert_to_image.py  # PDF to image conversion
│   ├── llm.py              # OpenAI API integration
│   └── prompt.py           # LLM prompt template
├── model/
│   └── extracted_model.py  # Pydantic data models
├── routes/
│   └── extract_llm.py      # API routes
├── config.py               # Application settings
├── logging_settings.py     # Logging configuration
└── main.py                # FastAPI application
```

## Error Handling

The application includes comprehensive error handling for:
- Invalid PDF files
- OpenAI API errors
- JSON parsing errors
- Data validation errors

All errors are logged to both console and file (app.log) with appropriate detail levels.

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Logging

Logs are written to:
- Console (stdout)
- app.log file

Log levels:
- DEBUG: Detailed debugging information
- INFO: General operational information
- ERROR: Error events that might still allow the application to continue running

## Notes

- The application requires an active OpenAI API key with access to GPT-4 Vision API
- Ensure sufficient API quota is available
- PDF files should be clear and legible for optimal extraction
- The application supports both invoice and statement document types
- All monetary values are handled with Decimal precision

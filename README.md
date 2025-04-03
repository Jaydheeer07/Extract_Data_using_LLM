# PDF Data Extraction with LLM

A Streamlit application that extracts structured data from invoice and statement PDFs using OpenAI's GPT-4 Vision API. The application converts PDF documents to images and uses advanced AI to accurately extract key information such as invoice numbers, dates, amounts, and line items. Data can be stored in a PostgreSQL database for historical tracking.

## Features

- PDF to Image conversion using PyMuPDF
- Support for both invoices and statements
- Structured data extraction with GPT-4 Vision API
- User-friendly Streamlit interface
- PostgreSQL database integration for data storage
- Document history tracking
- Decimal precision for financial amounts
- Support for line items with GST
- Rating system for extraction quality feedback

## Requirements

```txt
streamlit
fastapi
uvicorn
python-multipart
openai
PyMuPDF
Pillow
pydantic
python-dateutil
psycopg2-binary
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables in a `.env` file:
   ```bash
   OPENAI_API_KEY=your_api_key
   OPENAI_ORGANIZATION=your_org_id  # Optional
   SUPABASE_URL=postgresql://username:password@host:port/database
   ```

## PostgreSQL Setup

To use the database functionality, you need to set up the following tables in your PostgreSQL database:

### 1. Invoices Table
```sql
CREATE TABLE invoices (
  id SERIAL PRIMARY KEY,
  document_type TEXT NOT NULL,
  invoice_number TEXT,
  invoice_date DATE,
  total_amount DECIMAL(10,2) NOT NULL,
  vendor_name TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  due_date DATE,
  tax_amount DECIMAL(10,2),
  PO_number TEXT,
  reference TEXT,
  line_items JSONB,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  filename TEXT
);
```

### 2. Statements Table
```sql
CREATE TABLE statements (
  id SERIAL PRIMARY KEY,
  document_type TEXT NOT NULL,
  statement_date DATE,
  total_amount DECIMAL(10,2) NOT NULL,
  vendor_name TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  reference TEXT,
  statement_due_date DATE,
  PO_number TEXT,
  line_items JSONB,
  uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  filename TEXT
);
```

### 3. Ratings Table
```sql
CREATE TABLE ratings (
  id SERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  document_type TEXT NOT NULL,
  model TEXT NOT NULL,
  rating INTEGER NOT NULL,
  comment TEXT,
  document_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Running the Application

### Streamlit App
```bash
streamlit run streamlit_app.py
```

### FastAPI (Legacy)
```bash
uvicorn app.main:app --reload
```

## Deployment

### Streamlit Cloud Deployment
1. Push your code to a GitHub repository
2. Connect your repository to Streamlit Cloud
3. Set the required environment variables in the Streamlit Cloud dashboard
4. Deploy the application

## API Endpoints (FastAPI Version)

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

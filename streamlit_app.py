import streamlit as st
import logging
import io
import json
from datetime import datetime
import os
from typing import Dict, Any, List

from app.core.convert_to_image import pdf_to_image
from app.core.llm import extract_info, parse_and_validate_llm_output
from app.model.extracted_model import LineItem
from app.core.supabase_client import postgres

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def display_line_items(line_items: List[LineItem]):
    """Display line items in a structured table"""
    if not line_items:
        st.write("No line items found")
        return

    # Prepare data for the table
    data = {
        "Description": [],
        "Quantity": [],
        "Unit Price": [],
        "Total Price": [],
        "GST": []
    }
    
    for item in line_items:
        # Handle both LineItem objects and dictionaries
        if isinstance(item, dict):
            data["Description"].append(item.get("description", ""))
            data["Quantity"].append(item.get("quantity", "") if item.get("quantity") is not None else "")
            data["Unit Price"].append(f"${item.get('unit_price', '')}" if item.get("unit_price") is not None else "")
            data["Total Price"].append(f"${item.get('total_price', '')}")
            data["GST"].append(f"${item.get('gst', '')}" if item.get("gst") is not None else "")
        else:
            data["Description"].append(item.description)
            data["Quantity"].append(item.quantity if item.quantity is not None else "")
            data["Unit Price"].append(f"${item.unit_price}" if item.unit_price is not None else "")
            data["Total Price"].append(f"${item.total_price}")
            data["GST"].append(f"${item.gst}" if item.gst is not None else "")
    
    # Display the table
    st.table(data)

def save_to_database(invoice_data, filename):
    """Save extracted data to PostgreSQL database"""
    if not postgres.is_connected():
        st.error("⚠️ Database connection not configured. Please set POSTGRES_CONNECTION_STRING environment variable with your PostgreSQL connection string.")
        return False
    
    result = postgres.save_invoice(invoice_data, filename)
    
    if result["success"]:
        st.success(f"✅ Successfully saved to {result['table']} table with ID: {result['record_id']}")
        return True
    else:
        st.error(f"❌ Failed to save to database: {result.get('error', 'Unknown error')}")
        return False

def display_history():
    """Display history of processed documents"""
    if not postgres.is_connected():
        st.info("Connect to PostgreSQL database to view document history")
        return
    
    try:
        result = postgres.get_recent_documents(limit=5)
        
        if not result["success"]:
            st.error(f"Failed to fetch history: {result.get('error')}")
            return
            
        if not result["invoices"] and not result["statements"]:
            st.info("No documents found in the database")
            return
            
        st.subheader("📚 Recent Documents")
        
        # Display invoices
        if result["invoices"]:
            st.write("**Recent Invoices**")
            invoice_data = {
                "Invoice #": [],
                "Vendor": [],
                "Date": [],
                "Amount": [],
                "Uploaded": []
            }
            
            for inv in result["invoices"]:
                invoice_data["Invoice #"].append(inv.get("invoice_number", "N/A"))
                invoice_data["Vendor"].append(inv.get("vendor_name", "N/A"))
                invoice_data["Date"].append(inv.get("invoice_date", "N/A"))
                invoice_data["Amount"].append(f"${inv.get('total_amount', 'N/A')}")
                uploaded_at = inv.get("uploaded_at", "N/A")
                # Handle datetime objects from psycopg2
                if hasattr(uploaded_at, 'strftime'):
                    uploaded_at = uploaded_at.strftime("%Y-%m-%d")
                elif isinstance(uploaded_at, str) and "T" in uploaded_at:
                    uploaded_at = uploaded_at.split("T")[0]
                invoice_data["Uploaded"].append(uploaded_at)
            
            st.dataframe(invoice_data, use_container_width=True)
            
            # Allow viewing line items for selected invoice
            if len(result["invoices"]) > 0:
                invoice_options = {f"{inv.get('invoice_number', 'Unknown')} - {inv.get('vendor_name', 'Unknown')}": i 
                                  for i, inv in enumerate(result["invoices"])}
                
                selected_invoice = st.selectbox("Select an invoice to view details:", 
                                               options=list(invoice_options.keys()),
                                               index=None,
                                               key="invoice_selector")
                
                if selected_invoice:
                    inv_index = invoice_options[selected_invoice]
                    invoice = result["invoices"][inv_index]
                    
                    # Display invoice details without card wrapper
                    st.markdown('<div class="section-header no-border"><h3>Invoice Information</h3></div>', unsafe_allow_html=True)
                    
                    # Invoice details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Vendor**")
                        st.markdown(f"<div class='field-value'>{invoice.get('vendor_name', 'N/A')}</div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown("**Date**")
                        st.markdown(f"<div class='field-value'>{invoice.get('invoice_date', 'N/A')}</div>", unsafe_allow_html=True)
                    with col3:
                        st.markdown("**Amount**")
                        st.markdown(f"<div class='field-value'>${invoice.get('total_amount', 'N/A')}</div>", unsafe_allow_html=True)
                    
                    # Display line items if available
                    line_items = invoice.get("line_items", [])
                    if line_items:
                        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                        st.markdown('<div class="section-header no-border"><h3>Line Items</h3></div>', unsafe_allow_html=True)
                        display_line_items(line_items)
        
        # Display statements
        if result["statements"]:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.write("**Recent Statements**")
            statement_data = {
                "Vendor": [],
                "Date": [],
                "Amount": [],
                "Uploaded": []
            }
            
            for stmt in result["statements"]:
                statement_data["Vendor"].append(stmt.get("vendor_name", "N/A"))
                statement_data["Date"].append(stmt.get("statement_date", "N/A"))
                statement_data["Amount"].append(f"${stmt.get('total_amount', 'N/A')}")
                uploaded_at = stmt.get("uploaded_at", "N/A")
                # Handle datetime objects from psycopg2
                if hasattr(uploaded_at, 'strftime'):
                    uploaded_at = uploaded_at.strftime("%Y-%m-%d")
                elif isinstance(uploaded_at, str) and "T" in uploaded_at:
                    uploaded_at = uploaded_at.split("T")[0]
                statement_data["Uploaded"].append(uploaded_at)
            
            st.dataframe(statement_data, use_container_width=True)
            
            # Allow viewing line items for selected statement
            if len(result["statements"]) > 0:
                statement_options = {f"{stmt.get('vendor_name', 'Unknown')} - {stmt.get('statement_date', 'Unknown')}": i 
                                   for i, stmt in enumerate(result["statements"])}
                
                selected_statement = st.selectbox("Select a statement to view details:", 
                                                options=list(statement_options.keys()),
                                                index=None,
                                                key="statement_selector")
                
                if selected_statement:
                    stmt_index = statement_options[selected_statement]
                    statement = result["statements"][stmt_index]
                    
                    # Display statement details without card wrapper
                    st.markdown('<div class="section-header no-border"><h3>Statement Information</h3></div>', unsafe_allow_html=True)
                    
                    # Statement details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Vendor**")
                        st.markdown(f"<div class='field-value'>{statement.get('vendor_name', 'N/A')}</div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown("**Date**")
                        st.markdown(f"<div class='field-value'>{statement.get('statement_date', 'N/A')}</div>", unsafe_allow_html=True)
                    with col3:
                        st.markdown("**Amount**")
                        st.markdown(f"<div class='field-value'>${statement.get('total_amount', 'N/A')}</div>", unsafe_allow_html=True)
                    
                    # Display line items if available
                    line_items = statement.get("line_items", [])
                    if line_items:
                        # Handle JSON string or Python object
                        if isinstance(line_items, str):
                            try:
                                line_items = json.loads(line_items)
                            except:
                                line_items = []
                        
                        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                        st.markdown('<div class="section-header no-border"><h3>Line Items</h3></div>', unsafe_allow_html=True)
                        display_line_items(line_items)
            
    except Exception as e:
        st.error(f"Error displaying history: {str(e)}")

# Load custom CSS
def load_css():
    with open(".streamlit/style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Set page config
st.set_page_config(
    page_title="Invoice & Statement Data Extractor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
try:
    load_css()
except Exception as e:
    logger.warning(f"Could not load custom CSS: {str(e)}")

# Add sidebar with app info
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/invoice--v1.png", width=80)
    st.title("Document Extractor")
    st.markdown("---")
    
    st.markdown("""
    ### About
    This application extracts data from invoice and statement PDFs using AI technology.
    
    ### Features
    - 📄 Extract data from PDF documents
    - 🤖 AI-powered data extraction
    - 💾 Save to database
    - 📊 View document history
    """)
    
    st.markdown("---")
    
    # Database connection status
    st.subheader("Database Status")
    if postgres.is_connected():
        st.success("✅ Connected to database")
    else:
        st.error("❌ Not connected to database")
        st.info("Set POSTGRES_CONNECTION_STRING environment variable to connect")

# Create tabs
tab1, tab2 = st.tabs(["📄 Extract Data", "📚 Document History"])

with tab1:
    # Add title and description
    st.title("📊 Document Data Extractor")
    
    st.markdown("""
    <div class="info-box">
    This app extracts key information from invoice and statement PDFs using AI technology.
    Simply upload a PDF document to get started.
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader("Upload an invoice or statement PDF", type=["pdf"])
    
    with col2:
        st.markdown("""
        ### Supported Documents
        - ✅ Invoices
        - ✅ Statements
        - ✅ Bills
        """)
    
    if uploaded_file is not None:
        try:
            # Show processing message with progress
            with st.status("Processing your document...", expanded=True) as status:
                # Read PDF file
                pdf_bytes = uploaded_file.read()
                logger.info("Received PDF file: %s", uploaded_file.name)
                
                # Convert PDF to image
                status.update(label="Converting PDF to image...", state="running", expanded=True)
                images = pdf_to_image(io.BytesIO(pdf_bytes))
                
                if not images:
                    st.error("❌ Failed to convert PDF to image. Please try another file.")
                else:
                    # Extract information using LLM
                    status.update(label="Extracting data with AI...", state="running", expanded=True)
                    extracted_info = extract_info(images[0])
                    logger.info("Extracted info: %s", str(extracted_info))
                    
                    # Parse and validate LLM output
                    status.update(label="Validating extracted data...", state="running", expanded=True)
                    parsed_data = parse_and_validate_llm_output(extracted_info)
                    
                    # Complete the status
                    status.update(label="✅ Processing complete!", state="complete", expanded=True)
                    
                    # Create a two-column layout for the results with a small gap
                    st.markdown("""<div class="results-container">""", unsafe_allow_html=True)
                    results_col1, results_col2 = st.columns([3, 2], gap="medium")
                    
                    # Left column - Extracted Information
                    with results_col1:
                        # Convert Pydantic model to dict if it's not already a dict
                        if not isinstance(parsed_data, dict):
                            parsed_dict = parsed_data.model_dump()
                        else:
                            parsed_dict = parsed_data
                            
                        # Check for error
                        if "error" in parsed_dict:
                            st.error(f"Error in extraction: {parsed_dict['error']}")
                            st.stop()
                        
                        # Determine document type
                        doc_type = "Invoice" if parsed_dict.get("invoice_number") else "Statement"
                        
                        # Create a card for the main information
                        st.markdown("""
                        <div class="document-card content-card">
                            <div class="section-header no-border">
                                <h3>Extracted Information</h3>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Create columns for key information
                        if doc_type == "Invoice":
                            st.markdown(f"""<h4 class="document-title">Invoice #{parsed_dict.get('invoice_number', 'N/A')}</h4>""", unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown("**Vendor**")
                                st.markdown(f"""<p class="field-value">{parsed_dict.get('vendor_name', 'N/A')}</p>""", unsafe_allow_html=True)
                            with col2:
                                st.markdown("**Date**")
                                st.markdown(f"""<p class="field-value">{parsed_dict.get('invoice_date', 'N/A')}</p>""", unsafe_allow_html=True)
                            with col3:
                                st.markdown("**Amount**")
                                st.markdown(f"""<p class="field-value">${parsed_dict.get('total_amount', 'N/A')}</p>""", unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown("**Due Date**")
                                st.markdown(f"""<p class="field-value">{parsed_dict.get('due_date', 'N/A')}</p>""", unsafe_allow_html=True)
                            with col2:
                                st.markdown("**GST Amount**")
                                st.markdown(f"""<p class="field-value">${parsed_dict.get('tax_amount', 'N/A')}</p>""", unsafe_allow_html=True)
                            with col3:
                                if parsed_dict.get("PO_number"):
                                    st.markdown("**PO Number**")
                                    st.markdown(f"""<p class="field-value">{parsed_dict.get('PO_number', 'N/A')}</p>""", unsafe_allow_html=True)
                        else:  # Statement
                            st.markdown(f"""<h4 class="document-title">Statement: {parsed_dict.get('vendor_name', 'N/A')}</h4>""", unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Statement Date**")
                                st.markdown(f"""<p class="field-value">{parsed_dict.get('statement_date', 'N/A')}</p>""", unsafe_allow_html=True)
                            with col2:
                                st.markdown("**Total Amount**")
                                st.markdown(f"""<p class="field-value">${parsed_dict.get('total_amount', 'N/A')}</p>""", unsafe_allow_html=True)
                        
                        st.markdown("""</div>""", unsafe_allow_html=True)
                        
                        # Display line items
                        if parsed_dict.get("line_items"):
                            st.markdown("""
                            <div class="section-header no-border">
                                <h3>Line Items</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            display_line_items(parsed_dict["line_items"])
                        
                        # Save to Database section
                        st.markdown("""<div class="save-section">""", unsafe_allow_html=True)
                        
                        # Create columns for the save button and status
                        save_col1, save_col2 = st.columns([1, 2])
                        with save_col1:
                            save_clicked = st.button("Save to Database", key="save_button", use_container_width=True)
                        with save_col2:
                            if save_clicked:
                                with st.spinner("Saving to database..."):
                                    save_to_database(parsed_dict, uploaded_file.name)
                            else:
                                st.markdown("Click to save this document to your database for future reference.")
                        
                        st.markdown("""</div>""", unsafe_allow_html=True)
                    
                    # Right column - Document Preview
                    with results_col2:
                        st.markdown("""
                        <div class="document-card preview-card">
                            <div class="section-header no-border">
                                <h3>Document Preview</h3>
                            </div>
                        """, unsafe_allow_html=True)
                        st.image(images[0], use_container_width=True)
                        st.markdown("""</div>""", unsafe_allow_html=True)
                    
                    st.markdown("""</div>""", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Error processing file: %s", str(e))
            st.error(f"An error occurred while processing the file: {str(e)}")

with tab2:
    st.title("📚 Document History")
    st.markdown("""
    <div class="info-box">
    View previously processed documents stored in the database. Select an item to view its details.
    </div>
    """, unsafe_allow_html=True)
    
    # Display history
    display_history()

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
                
                selected_invoice = st.selectbox("Select an invoice to view line items:", 
                                               options=list(invoice_options.keys()),
                                               index=None)
                
                if selected_invoice:
                    inv_index = invoice_options[selected_invoice]
                    invoice = result["invoices"][inv_index]
                    
                    # Display invoice details
                    st.write(f"**Invoice Details:** {invoice.get('invoice_number', 'N/A')}")
                    
                    # Display line items if available
                    line_items = invoice.get("line_items", [])
                    if line_items:
                        # Handle JSON string or Python object
                        if isinstance(line_items, str):
                            try:
                                line_items = json.loads(line_items)
                            except:
                                line_items = []
                        
                        st.write("**Line Items:**")
                        display_line_items(line_items)
                    else:
                        st.write("No line items found for this invoice")
        
        # Display statements
        if result["statements"]:
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
                
                selected_statement = st.selectbox("Select a statement to view line items:", 
                                                options=list(statement_options.keys()),
                                                index=None)
                
                if selected_statement:
                    stmt_index = statement_options[selected_statement]
                    statement = result["statements"][stmt_index]
                    
                    # Display statement details
                    st.write(f"**Statement Details:** {statement.get('vendor_name', 'N/A')} - {statement.get('statement_date', 'N/A')}")
                    
                    # Display line items if available
                    line_items = statement.get("line_items", [])
                    if line_items:
                        # Handle JSON string or Python object
                        if isinstance(line_items, str):
                            try:
                                line_items = json.loads(line_items)
                            except:
                                line_items = []
                        
                        st.write("**Line Items:**")
                        display_line_items(line_items)
                    else:
                        st.write("No line items found for this statement")
            
    except Exception as e:
        st.error(f"Error displaying history: {str(e)}")

# Set page config
st.set_page_config(
    page_title="Invoice Data Extractor",
    page_icon="📄",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTable td, .stTable th {
        padding: 0.5rem;
    }
    .invoice-field {
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.2rem 0;
    }
    .stButton button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Create tabs for different sections
tab1, tab2 = st.tabs(["📝 Extract Data", "📚 History"])

with tab1:
    # Add title and description
    st.title("📄 Invoice Data Extractor")
    st.markdown("""
    This app extracts key information from invoice and statement PDFs using AI. 
    Simply upload your PDF invoice/statement and get structured data in return.
    """)

    # Check database connection
    db_status = "✅ Connected to database" if postgres.is_connected() else "⚠️ Not connected to database"
    st.sidebar.write(f"**Database Status:** {db_status}")

    if not postgres.is_connected():
        st.sidebar.info("To enable database storage, set POSTGRES_CONNECTION_STRING environment variable with your PostgreSQL connection string.")

    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF invoice/statement", type=['pdf'])

    # Store parsed info in session state to access it later
    if 'parsed_info' not in st.session_state:
        st.session_state.parsed_info = None
    if 'filename' not in st.session_state:
        st.session_state.filename = None

    if uploaded_file is not None:
        try:
            # Show processing message
            with st.spinner('Processing your invoice/statement...'):
                # Read PDF file
                pdf_bytes = uploaded_file.read()
                logger.info("Received PDF file: %s", uploaded_file.name)
                
                # Store filename in session state
                st.session_state.filename = uploaded_file.name

                # Convert PDF to images
                images = pdf_to_image(pdf_bytes)
                logger.info("Converted PDF to %d images", len(images))

                if not images:
                    st.error("No images were extracted from the PDF. Please check if the PDF is valid.")
                else:
                    # Extract information using LLM
                    extracted_info = extract_info(images[0])
                    logger.info("Extracted info: %s", str(extracted_info))

                    # Parse and validate the LLM output
                    parsed_info = parse_and_validate_llm_output(extracted_info)
                    logger.info("Parsed info: %s", str(parsed_info))
                    
                    # Store parsed info in session state
                    st.session_state.parsed_info = parsed_info

                    # Display the extracted information
                    if not parsed_info:
                        st.error("Failed to extract valid information from the invoice/statement.")
                    else:
                        doc_type = parsed_info.document_type.capitalize()
                        st.success(f"✅ Successfully extracted {doc_type} data!")
                        
                        # Create two columns with adjusted ratio
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            # Display the first image
                            st.subheader("Document Preview")
                            st.image(images[0], use_container_width=True)
                        
                        with col2:
                            # Display extracted information
                            st.subheader("Extracted Information")
                            
                            if parsed_info.document_type == "invoice":
                                # Display invoice information
                                st.markdown(f"**Invoice Number:** {parsed_info.invoice_number or 'N/A'}")
                                st.markdown(f"**Invoice Date:** {parsed_info.invoice_date or 'N/A'}")
                                st.markdown(f"**Due Date:** {parsed_info.due_date or 'N/A'}")
                                st.markdown(f"**Total Amount:** ${parsed_info.total_amount}")
                                st.markdown(f"**Vendor:** {parsed_info.vendor_name or 'N/A'}")
                                st.markdown(f"**Customer:** {parsed_info.customer_name or 'N/A'}")
                                
                                if parsed_info.tax_amount:
                                    st.markdown(f"**Tax Amount:** ${parsed_info.tax_amount}")
                                
                                if parsed_info.PO_number:
                                    st.markdown(f"**PO Number:** {parsed_info.PO_number}")
                                
                                if parsed_info.reference:
                                    st.markdown(f"**Reference:** {parsed_info.reference}")
                            else:
                                # Display statement information
                                st.markdown(f"**Statement Date:** {parsed_info.statement_date or 'N/A'}")
                                st.markdown(f"**Total Amount:** ${parsed_info.total_amount}")
                                st.markdown(f"**Vendor:** {parsed_info.vendor_name or 'N/A'}")
                                st.markdown(f"**Customer:** {parsed_info.customer_name or 'N/A'}")
                                
                                if parsed_info.reference:
                                    st.markdown(f"**Reference:** {parsed_info.reference}")
                            
                            # Line items section
                            if parsed_info.line_items:
                                st.subheader("Line Items")
                                display_line_items(parsed_info.line_items)
                            
                            # Save to database button
                            if postgres.is_connected():
                                if st.button("💾 Save to Database"):
                                    save_to_database(parsed_info, st.session_state.filename)
                            else:
                                st.info("Database connection not available. Connect to save data.")
                            
                            # Download JSON button
                            json_data = parsed_info.model_dump_json(indent=2)
                            st.download_button(
                                label="📥 Download JSON",
                                data=json_data,
                                file_name=f"{uploaded_file.name.split('.')[0]}_extracted.json",
                                mime="application/json"
                            )
        except Exception as e:
            logger.error("Error processing file: %s", str(e))
            st.error(f"An error occurred while processing the file: {str(e)}")

with tab2:
    st.title("📚 Document History")
    st.markdown("View previously processed documents stored in the database.")
    
    # Display history
    display_history()
    
    # Refresh button
    if st.button("🔄 Refresh History"):
        st.experimental_rerun()

# Add footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit and AI")

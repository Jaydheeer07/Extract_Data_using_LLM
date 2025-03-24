import streamlit as st
import logging
import io
import json
from typing import Dict, Any, List

from app.core.convert_to_image import pdf_to_image
from app.core.llm import extract_info, parse_and_validate_llm_output
from app.model.extracted_model import LineItem

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
        data["Description"].append(item.description)
        data["Quantity"].append(item.quantity if item.quantity is not None else "")
        data["Unit Price"].append(f"${item.unit_price}" if item.unit_price is not None else "")
        data["Total Price"].append(f"${item.total_price}")
        data["GST"].append(f"${item.gst}" if item.gst is not None else "")
    
    # Display the table
    st.table(data)

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
    </style>
""", unsafe_allow_html=True)

# Add title and description
st.title("📄 Invoice Data Extractor")
st.markdown("""
This app extracts key information from invoice and statement PDFs using AI. 
Simply upload your PDF invoice/statement and get structured data in return.
""")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF invoice/statement", type=['pdf'])

if uploaded_file is not None:
    try:
        # Show processing message
        with st.spinner('Processing your invoice/statement...'):
            # Read PDF file
            pdf_bytes = uploaded_file.read()
            logger.info("Received PDF file: %s", uploaded_file.name)

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

                # Display results
                if isinstance(parsed_info, dict) and "error" in parsed_info:
                    st.error(f"Error: {parsed_info['error']}")
                else:
                    st.success("Successfully extracted invoice data!")
                    
                    # Create two columns with adjusted ratio
                    col1, col2 = st.columns([3, 2])
                    
                    # Display the extracted information in an organized way
                    with col1:
                        st.subheader("📋 Invoice Details")
                        info_dict = parsed_info.model_dump()
                        
                        # Create three columns for better layout of basic info
                        c1, c2, c3 = st.columns(3)
                        
                        with c1:
                            st.markdown("**Invoice Number**")
                            st.markdown(f"<div class='invoice-field'>{info_dict.get('invoice_number', 'N/A')}</div>", unsafe_allow_html=True)
                            
                            st.markdown("**Invoice Date**")
                            st.markdown(f"<div class='invoice-field'>{info_dict.get('invoice_date', 'N/A')}</div>", unsafe_allow_html=True)
                        
                        with c2:
                            st.markdown("**Vendor Name**")
                            st.markdown(f"<div class='invoice-field'>{info_dict.get('vendor_name', 'N/A')}</div>", unsafe_allow_html=True)
                            
                            st.markdown("**Customer Name**")
                            st.markdown(f"<div class='invoice-field'>{info_dict.get('customer_name', 'N/A')}</div>", unsafe_allow_html=True)
                        
                        with c3:
                            st.markdown("**Total Amount**")
                            st.markdown(f"<div class='invoice-field'>${info_dict.get('total_amount', 'N/A')}</div>", unsafe_allow_html=True)
                            
                            st.markdown("**Tax Amount**")
                            st.markdown(f"<div class='invoice-field'>${info_dict.get('tax_amount', 'N/A') if info_dict.get('tax_amount') else 'N/A'}</div>", unsafe_allow_html=True)
                        
                        # Display line items in a table
                        st.subheader("📝 Line Items")
                        display_line_items(parsed_info.line_items if parsed_info.line_items else [])
                        
                        # Display additional fields
                        st.subheader("📌 Additional Information")
                        additional_fields = {
                            "PO Number": info_dict.get('PO_number', 'N/A'),
                            "Statement Date": info_dict.get('statement_date', 'N/A'),
                            "Due Date": info_dict.get('due_date', 'N/A'),
                            "Reference": info_dict.get('reference', 'N/A')
                        }
                        
                        # Create two columns for additional fields
                        ac1, ac2 = st.columns(2)
                        for i, (key, value) in enumerate(additional_fields.items()):
                            with ac1 if i % 2 == 0 else ac2:
                                st.markdown(f"**{key}**")
                                st.markdown(f"<div class='invoice-field'>{value}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.subheader("🔍 Preview")
                        # Use use_container_width instead of use_column_width
                        st.image(images[0], caption="Invoice Preview", use_container_width=True)

    except Exception as e:
        logger.error("Error processing file: %s", str(e))
        st.error(f"An error occurred while processing the file: {str(e)}")

# Add footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit and AI")

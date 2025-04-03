import io
import logging

import streamlit as st

from app.core.convert_to_image import pdf_to_image
from app.core.llm import extract_info, parse_and_validate_llm_output
from app.streamlit_func.display_line_items import display_line_items
from app.streamlit_func.save_to_database import save_to_database
from app.streamlit_func.rating_component import display_rating_component

# Configure logging
logger = logging.getLogger(__name__)


def display_extract_data_tab():
    """Display the Extract Data tab content"""
    # Add title and description
    st.title("📊 Document Data Extractor")

    st.markdown(
        """
    <div class="info-box">
    This app extracts key information from invoice and statement PDFs using AI technology.
    Simply upload a PDF document to get started.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Create columns for better layout
    col1, col2 = st.columns([2, 1])

    with col1:
        # File uploader for PDF documents
        uploaded_file = st.file_uploader(
            "Upload an invoice or statement PDF",
            type="pdf",
            help="Upload a PDF file to extract data",
            key="pdf_uploader"
        )
        
        # Check if we need to reprocess a file due to model change
        reprocess_file = False
        if "reprocess_file" in st.session_state and st.session_state["reprocess_file"]:
            reprocess_file = True
            st.session_state["reprocess_file"] = False  # Reset the flag
            logger.info("Reprocessing last file with new model")
            
            # Show a message about reprocessing if we have a filename
            if "last_uploaded_filename" in st.session_state:
                filename = st.session_state["last_uploaded_filename"]
                st.info(f"Reprocessing {filename} with model: {st.session_state.get('selected_model', 'Unknown')}")

    with col2:
        st.markdown("""
        ### Supported Documents
        - ✅ Invoices
        - ✅ Statements
        - ✅ Bills
        """)

    # Handle reprocessing case - if model changed and we have stored file bytes
    reprocess_file = False
    pdf_bytes = None
    filename = None
    
    if "reprocess_file" in st.session_state and st.session_state["reprocess_file"]:
        if "last_uploaded_filename" in st.session_state and "last_uploaded_file_bytes" in st.session_state:
            reprocess_file = True
            pdf_bytes = st.session_state["last_uploaded_file_bytes"]
            filename = st.session_state["last_uploaded_filename"]
            logger.info(f"Reprocessing file {filename} with new model")
        st.session_state["reprocess_file"] = False  # Reset the flag
    
    # Process either uploaded file or reprocessed file
    if uploaded_file is not None or reprocess_file:
        try:
            # Show processing message with progress
            with st.status("Processing your document...", expanded=True) as status:
                # Get file bytes - either from uploaded file or from session state
                if uploaded_file is not None:
                    # New file upload case
                    pdf_bytes = uploaded_file.read()
                    filename = uploaded_file.name
                    logger.info(f"Received PDF file: {filename}")
                    
                    # Store for potential reprocessing with different models
                    st.session_state["last_uploaded_filename"] = filename
                    st.session_state["last_uploaded_file_bytes"] = pdf_bytes
                else:
                    # Reprocessing case - already have bytes from above
                    logger.info(f"Reprocessing file: {filename}")

                # Convert PDF to image
                status.update(
                    label="Converting PDF to image...", state="running", expanded=True
                )
                images = pdf_to_image(io.BytesIO(pdf_bytes))

                if not images:
                    st.error(
                        "❌ Failed to convert PDF to image. Please try another file."
                    )
                else:
                    # Get current model
                    current_model = st.session_state.get("selected_model", "Unknown")
                    
                    # Create a model-specific key for caching
                    file_model_key = f"extracted_{filename}_{current_model}"
                    
                    # Check if we have results for this file with the current model
                    if file_model_key not in st.session_state:
                        # Extract information using LLM
                        status.update(
                            label=f"Extracting data with {current_model}...",
                            state="running",
                            expanded=True,
                        )
                        extracted_info = extract_info(images[0])
                        logger.info("Extracted info: %s", str(extracted_info))

                        # Parse and validate LLM output
                        status.update(
                            label="Validating extracted data...",
                            state="running",
                            expanded=True,
                        )
                        parsed_data = parse_and_validate_llm_output(extracted_info)
                        
                        # Store in session state with model-specific key
                        st.session_state[file_model_key] = parsed_data
                        
                        # Store the file information in session state for reuse
                        st.session_state["last_uploaded_filename"] = uploaded_file.name
                        st.session_state["last_uploaded_file_bytes"] = pdf_bytes
                    else:
                        # Use cached results from session state for this model
                        parsed_data = st.session_state[file_model_key]
                        logger.info(f"Using cached extraction results for {uploaded_file.name} with model {current_model}")

                    # Complete the status
                    status.update(
                        label="✅ Processing complete!", state="complete", expanded=True
                    )

                    # Create a two-column layout for the results with a small gap
                    st.markdown(
                        """<div class="results-container">""", unsafe_allow_html=True
                    )
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
                            return

                        # Determine document type
                        doc_type = (
                            "Invoice"
                            if parsed_dict.get("invoice_number")
                            else "Statement"
                        )

                        # Create a card for the main information
                        st.markdown(
                            """
                         <div class="document-card content-card">
                             <div class="section-header no-border">
                                 <h3>Extracted Information</h3>
                             </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Create columns for key information
                        if doc_type == "Invoice":
                            st.markdown(
                                f"""<h4 class="document-title">Invoice #{parsed_dict.get("invoice_number", "N/A")}</h4>""",
                                unsafe_allow_html=True,
                            )

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown("**Vendor**")
                                st.markdown(
                                    f"""<p class="field-value">{parsed_dict.get("vendor_name", "N/A")}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col2:
                                st.markdown("**Date**")
                                st.markdown(
                                    f"""<p class="field-value">{parsed_dict.get("invoice_date", "N/A")}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col3:
                                st.markdown("**Amount**")
                                total_amount = parsed_dict.get("total_amount")
                                total_display = f"${total_amount}" if total_amount not in [None, "N/A"] else "N/A"
                                st.markdown(
                                    f"""<p class="field-value">{total_display}</p>""",
                                    unsafe_allow_html=True,
                                )

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown("**Due Date**")
                                st.markdown(
                                    f"""<p class="field-value">{parsed_dict.get("due_date", "N/A")}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col2:
                                st.markdown("**GST Amount**")
                                tax_amount = parsed_dict.get("tax_amount")
                                tax_display = f"${tax_amount}" if tax_amount not in [None, "N/A"] else "N/A"
                                st.markdown(
                                    f"""<p class="field-value">{tax_display}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col3:
                                if parsed_dict.get("PO_number"):
                                    st.markdown("**PO Number**")
                                    st.markdown(
                                        f"""<p class="field-value">{parsed_dict.get("PO_number", "N/A")}</p>""",
                                        unsafe_allow_html=True,
                                    )
                        else:  # Statement
                            st.markdown(
                                f"""<h4 class="document-title">Statement: {parsed_dict.get("vendor_name", "N/A")}</h4>""",
                                unsafe_allow_html=True,
                            )

                            col1, col2, col3, col4, col5, col6 = st.columns(6)
                            with col1:
                                st.markdown("**Statement Date**")
                                st.markdown(
                                    f"""<p class="field-value">{parsed_dict.get("statement_date", "N/A")}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col2:
                                st.markdown("**Due Date**")
                                st.markdown(
                                    f"""<p class="field-value">{parsed_dict.get("due_date", "N/A")}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col3:
                                st.markdown("**Customer Name**")
                                st.markdown(
                                    f"""<p class="field-value">{parsed_dict.get("customer_name", "N/A")}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col4:
                                st.markdown("**Reference**")
                                st.markdown(
                                    f"""<p class="field-value">{parsed_dict.get("reference", "N/A")}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col5:
                                st.markdown("**GST/Tax**")
                                tax_amount = parsed_dict.get("tax_amount")
                                tax_display = f"${tax_amount}" if tax_amount not in [None, "N/A"] else "N/A"
                                st.markdown(
                                    f"""<p class="field-value">{tax_display}</p>""",
                                    unsafe_allow_html=True,
                                )
                            with col6:
                                st.markdown("**Total Amount**")
                                total_amount = parsed_dict.get("total_amount")
                                total_display = f"${total_amount}" if total_amount not in [None, "N/A"] else "N/A"
                                st.markdown(
                                    f"""<p class="field-value">{total_display}</p>""",
                                    unsafe_allow_html=True,
                                )

                        st.markdown("""</div>""", unsafe_allow_html=True)

                        # Display line items
                        if parsed_dict.get("line_items"):
                            st.markdown(
                                """
                             <div class="section-header no-border">
                                 <h3>Line Items</h3>
                             </div>
                            """,
                                unsafe_allow_html=True,
                            )
                            display_line_items(parsed_dict["line_items"])

                        # Rating component section - show after successful extraction
                        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
                        display_rating_component(
                            filename=uploaded_file.name,
                            document_type=parsed_dict.get("document_type", "invoice")
                        )
                        
                        # Save to Database section
                        st.markdown(
                            """<div class="save-section">""", unsafe_allow_html=True
                        )

                        # Create columns for the save button and status
                        save_col1, save_col2 = st.columns([1, 2])
                        with save_col1:
                            save_clicked = st.button(
                                "Save to Database",
                                key="save_button",
                                use_container_width=True,
                            )
                        with save_col2:
                            if save_clicked:
                                with st.spinner("Saving to database..."):
                                    save_result = save_to_database(parsed_dict, uploaded_file.name)
                                    if save_result:
                                        st.success("Document saved successfully!")
                            else:
                                st.markdown(
                                    "Click to save this document to your database for future reference."
                                )

                        st.markdown("""</div>""", unsafe_allow_html=True)

                    # Right column - Document Preview
                    with results_col2:
                        st.markdown(
                            """
                         <div class="document-card preview-card">
                             <div class="section-header no-border">
                                 <h3>Document Preview</h3>
                             </div>
                        """,
                            unsafe_allow_html=True,
                        )
                        st.image(images[0], use_container_width=True)
                        st.markdown("""</div>""", unsafe_allow_html=True)

                    st.markdown("""</div>""", unsafe_allow_html=True)

        except Exception as e:
            logger.error("Error processing file: %s", str(e))
            st.error(f"An error occurred while processing the file: {str(e)}")

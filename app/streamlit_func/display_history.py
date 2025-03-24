import json

import streamlit as st

from app.core.supabase_client import postgres
from app.streamlit_func.display_line_items import display_line_items


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
                "Uploaded": [],
            }

            for inv in result["invoices"]:
                invoice_data["Invoice #"].append(inv.get("invoice_number", "N/A"))
                invoice_data["Vendor"].append(inv.get("vendor_name", "N/A"))
                invoice_data["Date"].append(inv.get("invoice_date", "N/A"))
                invoice_data["Amount"].append(f"${inv.get('total_amount', 'N/A')}")
                uploaded_at = inv.get("uploaded_at", "N/A")
                # Handle datetime objects from psycopg2
                if hasattr(uploaded_at, "strftime"):
                    uploaded_at = uploaded_at.strftime("%Y-%m-%d")
                elif isinstance(uploaded_at, str) and "T" in uploaded_at:
                    uploaded_at = uploaded_at.split("T")[0]
                invoice_data["Uploaded"].append(uploaded_at)

            st.dataframe(invoice_data, use_container_width=True)

            # Allow viewing line items for selected invoice
            if len(result["invoices"]) > 0:
                invoice_options = {
                    f"{inv.get('invoice_number', 'Unknown')} - {inv.get('vendor_name', 'Unknown')}": i
                    for i, inv in enumerate(result["invoices"])
                }

                selected_invoice = st.selectbox(
                    "Select an invoice to view details:",
                    options=list(invoice_options.keys()),
                    index=None,
                    key="invoice_selector",
                )

                if selected_invoice:
                    inv_index = invoice_options[selected_invoice]
                    invoice = result["invoices"][inv_index]

                    # Display invoice details without card wrapper
                    st.markdown(
                        '<div class="section-header no-border"><h3>Invoice Information</h3></div>',
                        unsafe_allow_html=True,
                    )

                    # Invoice details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Vendor**")
                        st.markdown(
                            f"<div class='field-value'>{invoice.get('vendor_name', 'N/A')}</div>",
                            unsafe_allow_html=True,
                        )
                    with col2:
                        st.markdown("**Date**")
                        st.markdown(
                            f"<div class='field-value'>{invoice.get('invoice_date', 'N/A')}</div>",
                            unsafe_allow_html=True,
                        )
                    with col3:
                        st.markdown("**Amount**")
                        st.markdown(
                            f"<div class='field-value'>${invoice.get('total_amount', 'N/A')}</div>",
                            unsafe_allow_html=True,
                        )

                    # Display line items if available
                    line_items = invoice.get("line_items", [])
                    if line_items:
                        st.markdown(
                            '<div class="section-divider"></div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            '<div class="section-header no-border"><h3>Line Items</h3></div>',
                            unsafe_allow_html=True,
                        )
                        display_line_items(line_items)

        # Display statements
        if result["statements"]:
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.write("**Recent Statements**")
            statement_data = {"Vendor": [], "Date": [], "Amount": [], "Uploaded": []}

            for stmt in result["statements"]:
                statement_data["Vendor"].append(stmt.get("vendor_name", "N/A"))
                statement_data["Date"].append(stmt.get("statement_date", "N/A"))
                statement_data["Amount"].append(f"${stmt.get('total_amount', 'N/A')}")
                uploaded_at = stmt.get("uploaded_at", "N/A")
                # Handle datetime objects from psycopg2
                if hasattr(uploaded_at, "strftime"):
                    uploaded_at = uploaded_at.strftime("%Y-%m-%d")
                elif isinstance(uploaded_at, str) and "T" in uploaded_at:
                    uploaded_at = uploaded_at.split("T")[0]
                statement_data["Uploaded"].append(uploaded_at)

            st.dataframe(statement_data, use_container_width=True)

            # Allow viewing line items for selected statement
            if len(result["statements"]) > 0:
                statement_options = {
                    f"{stmt.get('vendor_name', 'Unknown')} - {stmt.get('statement_date', 'Unknown')}": i
                    for i, stmt in enumerate(result["statements"])
                }

                selected_statement = st.selectbox(
                    "Select a statement to view details:",
                    options=list(statement_options.keys()),
                    index=None,
                    key="statement_selector",
                )

                if selected_statement:
                    stmt_index = statement_options[selected_statement]
                    statement = result["statements"][stmt_index]

                    # Display statement details without card wrapper
                    st.markdown(
                        '<div class="section-header no-border"><h3>Statement Information</h3></div>',
                        unsafe_allow_html=True,
                    )

                    # Statement details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Vendor**")
                        st.markdown(
                            f"<div class='field-value'>{statement.get('vendor_name', 'N/A')}</div>",
                            unsafe_allow_html=True,
                        )
                    with col2:
                        st.markdown("**Date**")
                        st.markdown(
                            f"<div class='field-value'>{statement.get('statement_date', 'N/A')}</div>",
                            unsafe_allow_html=True,
                        )
                    with col3:
                        st.markdown("**Amount**")
                        st.markdown(
                            f"<div class='field-value'>${statement.get('total_amount', 'N/A')}</div>",
                            unsafe_allow_html=True,
                        )

                    # Display line items if available
                    line_items = statement.get("line_items", [])
                    if line_items:
                        # Handle JSON string or Python object
                        if isinstance(line_items, str):
                            try:
                                line_items = json.loads(line_items)
                            except json.JSONDecodeError:
                                line_items = []

                        st.markdown(
                            '<div class="section-divider"></div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            '<div class="section-header no-border"><h3>Line Items</h3></div>',
                            unsafe_allow_html=True,
                        )
                        display_line_items(line_items)

    except Exception as e:
        st.error(f"Error displaying history: {str(e)}")

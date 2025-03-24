import logging
from typing import List

import streamlit as st

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
        "GST": [],
    }

    for item in line_items:
        # Handle both LineItem objects and dictionaries
        if isinstance(item, dict):
            data["Description"].append(item.get("description", ""))
            data["Quantity"].append(
                item.get("quantity", "") if item.get("quantity") is not None else ""
            )
            data["Unit Price"].append(
                f"${item.get('unit_price', '')}"
                if item.get("unit_price") is not None
                else ""
            )
            data["Total Price"].append(f"${item.get('total_price', '')}")
            data["GST"].append(
                f"${item.get('gst', '')}" if item.get("gst") is not None else ""
            )
        else:
            data["Description"].append(item.description)
            data["Quantity"].append(item.quantity if item.quantity is not None else "")
            data["Unit Price"].append(
                f"${item.unit_price}" if item.unit_price is not None else ""
            )
            data["Total Price"].append(f"${item.total_price}")
            data["GST"].append(f"${item.gst}" if item.gst is not None else "")

    # Display the table
    st.table(data)

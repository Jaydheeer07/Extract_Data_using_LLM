import streamlit as st

from app.core.supabase_client import postgres


def save_to_database(invoice_data, filename):
    """Save extracted data to PostgreSQL database"""
    if not postgres.is_connected():
        st.error(
            "⚠️ Database connection not configured. Please set POSTGRES_CONNECTION_STRING environment variable with your PostgreSQL connection string."
        )
        return False

    result = postgres.save_invoice(invoice_data, filename)

    if result["success"]:
        st.success(
            f"✅ Successfully saved to {result['table']} table with ID: {result['record_id']}"
        )
        return True
    else:
        st.error(
            f"❌ Failed to save to database: {result.get('error', 'Unknown error')}"
        )
        return False

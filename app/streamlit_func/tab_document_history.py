import streamlit as st

from app.streamlit_func.display_history import display_history


def display_document_history_tab():
    """Display the Document History tab content"""
    st.title("📚 Document History")
    st.markdown(
        """
    <div class="info-box">
    View previously processed documents stored in the database. Select an item to view its details.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Display history
    display_history()

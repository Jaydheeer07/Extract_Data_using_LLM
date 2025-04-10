import logging

import streamlit as st

from app.core.supabase_client import postgres
from app.core.convert_to_image import process_file_to_images
from app.streamlit_func import display_document_history_tab, display_extract_data_tab, display_model_selection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load custom CSS
def load_css():
    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Set page config
st.set_page_config(
    page_title="Invoice & Statement Data Extractor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
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
    
    # Add model selection UI using the modular function
    display_model_selection()
    
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

# Display content for each tab
with tab1:
    display_extract_data_tab()

with tab2:
    display_document_history_tab()

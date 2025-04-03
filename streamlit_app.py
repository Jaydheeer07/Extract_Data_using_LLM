import logging

import streamlit as st

from app.core.supabase_client import postgres
from app.streamlit_func import display_document_history_tab, display_extract_data_tab

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
    
    # Model selection section
    st.subheader("AI Model Selection")
    
    # Create a dictionary of model options
    model_options = {
        "Google Gemma 3 (27B)": "google/gemma-3-27b-it",
        "Mistral Small (24B)": "mistralai/mistral-small-3.1-24b-instruct",
        "Qwen (32B)": "qwen/qwq-32b"
    }
    
    # Create a selectbox for model selection with custom styling
    st.markdown("""
    <style>
    div[data-testid="stSelectbox"] > div > div > div {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 2px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    selected_model_name = st.selectbox(
        "Select AI Model",
        options=list(model_options.keys()),
        index=0,  # Default to the first option (Gemma)
        help="Choose which AI model to use for data extraction"
    )
    
    # Get the actual model ID from the selected name
    selected_model = model_options[selected_model_name]
    
    # Store the selected model in session state so it can be accessed elsewhere
    if "selected_model" not in st.session_state or st.session_state.selected_model != selected_model:
        st.session_state.selected_model = selected_model
        # Log the model change
        logger.info(f"Model changed to: {selected_model}")
    
    # Display model info
    model_info = {
        "google/gemma-3-27b-it": "Google's Gemma 3 model optimized for instruction following with 27B parameters.",
        "mistralai/mistral-small-3.1-24b-instruct": "Mistral AI's 24B parameter model with strong reasoning capabilities.",
        "qwen/qwq-32b": "Qwen's 32B parameter model with excellent comprehension abilities."
    }
    
    st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-top: 10px;'><small>{model_info[selected_model]}</small></div>", unsafe_allow_html=True)
    
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

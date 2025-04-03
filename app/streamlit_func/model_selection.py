import logging
import streamlit as st

logger = logging.getLogger(__name__)

def display_model_selection():
    """
    Display the model selection UI in the sidebar.
    Returns the selected model ID.
    """
    # Add the model selection header with icon
    st.markdown(
        """
        <div class="model-selection-header">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2c1.5 0 3 .6 4 1.5 1.5 1.5 1.5 4.5 0 6h-8c-1.5-1.5-1.5-4.5 0-6C9 2.6 10.5 2 12 2z"></path>
                <path d="M12 22c-1.5 0-3-.6-4-1.5-1.5-1.5-1.5-4.5 0-6h8c1.5 1.5 1.5 4.5 0 6-1 .9-2.5 1.5-4 1.5z"></path>
                <path d="M15 9.5a3.5 3.5 0 1 0 0 5 3.5 3.5 0 1 0 0-5z"></path>
                <path d="M9 9.5a3.5 3.5 0 1 0 0 5 3.5 3.5 0 1 0 0-5z"></path>
            </svg>
            AI Model Selection
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Create a dictionary of model options with additional metadata
    model_options = {
        "Mistral Small (24B)": {
            "id": "mistralai/mistral-small-3.1-24b-instruct",
            "description": "Mistral AI's 24B parameter model with strong reasoning capabilities.",
            "badge": "RECOMMENDED",
            "icon": "🧠"
        },
        "Google Gemma 3 (27B)": {
            "id": "google/gemma-3-27b-it",
            "description": "Google's Gemma 3 model optimized for instruction following with 27B parameters.",
            "badge": "FAST",
            "icon": "⚡"
        },
        "Qwen 2.5 VL (32B)": {
            "id": "qwen/qwen2.5-vl-32b-instruct:free",
            "description": "Qwen's 32B vision-language model with excellent text and image comprehension abilities.",
            "badge": "OPTIMAL",
            "icon": "👁️"
        }
    }
    
    # Create the selectbox for model selection
    selected_model_name = st.selectbox(
        "Select AI Model",
        options=list(model_options.keys()),
        index=0,  # Default to the first option (Mistral)
        help="Choose which AI model to use for data extraction"
    )
    
    # Get the model details from the selected name
    selected_model_details = model_options[selected_model_name]
    selected_model = selected_model_details["id"]
    
    # Store the selected model in session state so it can be accessed elsewhere
    if "selected_model" not in st.session_state or st.session_state.selected_model != selected_model:
        st.session_state.selected_model = selected_model
        # Log the model change
        logger.info(f"Model changed to: {selected_model}")
    
    # Display enhanced model info card
    st.markdown(
        f"""
        <div class="model-info-card">
            <span class="model-badge">{selected_model_details['badge']}</span>
            <span class="model-badge" style="background-color: #8B5CF6;">{selected_model_details['icon']} {selected_model_name.split(' ')[0]}</span>
            <div class="model-info-text">{selected_model_details['description']}</div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    return selected_model

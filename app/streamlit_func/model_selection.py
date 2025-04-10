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
        },
        "GPT-4o Mini": {
            "id": "openai/gpt-4o-mini",
            "description": "OpenAI's smaller version of GPT-4o with excellent reasoning and instruction following.",
            "badge": "BALANCED",
            "icon": "🤖"
        },
        "Llama 4 Maverick": {
            "id": "meta-llama/llama-4-maverick",
            "description": "Meta's newest Llama 4 Maverick model with strong performance on complex tasks.",
            "badge": "POWERFUL",
            "icon": "🦙"
        },
        "Gemini 2.0 Flash": {
            "id": "google/gemini-2.0-flash-001",
            "description": "Google's Gemini 2.0 Flash model optimized for speed and efficiency.",
            "badge": "SPEEDY",
            "icon": "🌟"
        },
        "Amazon Nova Lite": {
            "id": "amazon/nova-lite-v1",
            "description": "Amazon's Nova Lite model with excellent document understanding capabilities.",
            "badge": "NEW",
            "icon": "📊"
        }
    }
    
    # Create the selectbox for model selection
    selected_model_name = st.selectbox(
        "Select AI Model",
        options=list(model_options.keys()),
        index=2,  # Default to Qwen 2.5 VL (32B) which is the third option (index 2)
        help="Choose which AI model to use for data extraction"
    )
    
    # Get the model details from the selected name
    selected_model_details = model_options[selected_model_name]
    selected_model = selected_model_details["id"]
    
    # Store the selected model in session state so it can be accessed elsewhere
    model_changed = False
    if "selected_model" not in st.session_state or st.session_state.selected_model != selected_model:
        # Record that the model has changed
        model_changed = True
        st.session_state.selected_model = selected_model
        # Log the model change
        logger.info(f"Model changed to: {selected_model}")
        
        # If we have a previously uploaded file, set a flag to re-process it
        if "last_uploaded_filename" in st.session_state and "last_uploaded_file_bytes" in st.session_state:
            st.session_state["reprocess_file"] = True
            logger.info(f"Model changed - will reprocess last uploaded file with new model: {selected_model}")
            
            # Clear any existing rating and comment data
            filename = st.session_state["last_uploaded_filename"]
            # Reset rating to 0 (no rating)
            for key in list(st.session_state.keys()):
                # Clear rating and comment fields for this file
                if key.startswith("rating_") or key.startswith("comment_"):
                    del st.session_state[key]
    
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

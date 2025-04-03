import streamlit as st
from app.core.supabase_client import postgres
import logging

logger = logging.getLogger(__name__)

def display_rating_component(filename, document_type, model=None, show_in_history=False, document_id=None):
    """
    Display a rating component for users to rate the extraction quality
    
    Args:
        filename: The name of the document file
        document_type: Either 'invoice' or 'statement'
        model: The AI model used for extraction
        show_in_history: Whether this is shown in the history tab
        document_id: The database ID of the document (used in history view)
    """
    # Create a unique key suffix based on context
    key_suffix = f"history_{document_id}" if show_in_history else "extract"
    
    # Get the current model if not provided
    if not model:
        model = st.session_state.get("selected_model", "Unknown")
    
    st.markdown(
        """
        <div class="rating-section">
            <h4>Rate Extraction Quality</h4>
            <p class="rating-description">How accurate was the data extraction?</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Create a simple radio button star rating
    st.write("Rating")
    
    # Initialize rating in session state if not already present
    if f"rating_{key_suffix}" not in st.session_state:
        st.session_state[f"rating_{key_suffix}"] = 0
    
    # Create a radio button group for star ratings
    rating_options = {
        "☆☆☆☆☆": 0,
        "★☆☆☆☆": 1,
        "★★☆☆☆": 2,
        "★★★☆☆": 3,
        "★★★★☆": 4,
        "★★★★★": 5
    }
    
    # Convert current rating to display option
    current_rating = st.session_state[f"rating_{key_suffix}"]
    current_display = list(rating_options.keys())[list(rating_options.values()).index(current_rating)]
    
    # Create the radio buttons with a proper label that we'll hide with CSS
    selected_display = st.radio(
        "Star Rating",  # Provide a proper label for accessibility
        options=list(rating_options.keys()),
        index=list(rating_options.values()).index(current_rating),
        key=f"rating_radio_{key_suffix}",
        horizontal=True,
        label_visibility="collapsed"  # Hide the label visually but keep it for accessibility
    )
    
    # Update the rating in session state
    rating = rating_options[selected_display]
    st.session_state[f"rating_{key_suffix}"] = rating
    
    # Display the current rating as text
    if rating > 0:
        st.markdown(f"<p>You selected: {rating} {'star' if rating == 1 else 'stars'}</p>", unsafe_allow_html=True)
    
    # Add a comment field
    comment = st.text_area(
        "Comments (optional)",
        placeholder="Add any additional feedback about the extraction quality. Make sure to include any errors or missing data.",
        key=f"comment_{key_suffix}"
    )
    
    # Submit button
    submit_clicked = st.button(
        "Submit Rating", 
        key=f"submit_rating_{key_suffix}",
        use_container_width=True
    )
    
    # Handle submission
    if submit_clicked:
        with st.spinner("Saving your feedback..."):
            # Only submit if a rating has been selected
            if rating > 0:
                result = postgres.save_rating(
                    filename=filename,
                    document_type=document_type,
                    model=model,
                    rating=rating,
                    comment=comment,
                    document_id=document_id
                )
            else:
                result = {"success": False, "error": "Please select a rating before submitting."}
            
            if result["success"]:
                st.success("Thank you for your feedback!")
                
                # Clear the form after submission
                if f"rating_{key_suffix}" in st.session_state:
                    del st.session_state[f"rating_{key_suffix}"]
                if f"comment_{key_suffix}" in st.session_state:
                    del st.session_state[f"comment_{key_suffix}"]
            else:
                st.error(f"Failed to save rating: {result.get('error', 'Unknown error')}")

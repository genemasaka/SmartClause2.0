import streamlit as st


def confirm_generation_started():
    """
    Call this function from document_editor.py when document generation has been
    confirmed to have started (e.g., when the first chunk of content is received
    or when the generation API call succeeds).
    
    This will close the new matter modal if it's waiting for generation confirmation.
    """
    if st.session_state.get("wait_for_generation_start", False):
        # Generation has started, close the modal
        st.session_state.wait_for_generation_start = False
        st.session_state.show_new_matter = False
        st.session_state.modal_mode = "new_matter"
        st.session_state.existing_matter_id = None
        # Don't rerun here - let the editor continue naturally


def is_waiting_for_generation():
    """
    Check if we're currently waiting for generation to start.
    Returns True if the modal should remain open until generation is confirmed.
    """
    return st.session_state.get("wait_for_generation_start", False)

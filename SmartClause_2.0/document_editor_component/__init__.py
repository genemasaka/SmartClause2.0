import streamlit as st
import streamlit.components.v1 as components
import os

_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "st_doc_editor",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_doc_editor", path=build_dir)

def st_doc_editor(
    content: str, 
    key: str = None,
    versionId: str = None,
    comments: list = None, 
    height: int = 800, 
    debounce: int = 1500,
    clauses: list = None
):
    """
    Create a new instance of the st_doc_editor component.

    Parameters
    ----------
    content: str
        The initial HTML content to load into the editor.
    key: str or None
        An optional key that uniquely identifies this component.
    height: int
        The height of the editor component in pixels.
    debounce: int
        The debounce time in milliseconds for sending updates from JS to Python.
        Default is 1500ms (1.5 seconds).
    clauses: list or None
        List of clause dictionaries to make available for insertion in the editor.
        Each clause should have: id, title, category, content, tags, usage_count, is_pinned, is_system.
    
    Returns
    -------
    str
        The current HTML content of the editor.
    """
    if clauses is None:
        clauses = []
    
    component_value = _component_func(
        initialContent=content,
        debounce=debounce,
        clauses=clauses,
        key=key,
        versionId=versionId,
        comments=comments,
        default=content,
        height=height,
    )
    return component_value

if not _RELEASE and __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.subheader("Streamlit Document Editor Component Test")
    
    if "content" not in st.session_state:
        st.session_state.content = "<p>This is the <strong>initial content</strong> from Streamlit.</p><p>Start typing or paste content here.</p>"

    st.info("Type or paste into the editor below. The content will update here after 1.5s of inactivity.")

    test_clauses = [
        {
            "id": "test_1",
            "title": "Test Clause 1",
            "category": "Boilerplate",
            "content": "<p><strong>Test Clause.</strong> This is a test clause for development.</p>",
            "tags": ["test", "development"],
            "usage_count": 0,
            "is_pinned": False,
            "is_system": False
        }
    ]

    new_content = st_doc_editor(
        st.session_state.content,
        key="editor_test",
        height=600,
        clauses=test_clauses
    )
    
    if new_content != st.session_state.content:
        st.session_state.content = new_content
        st.toast("Content synced from component!")
    
    st.markdown("---")
    st.subheader("Current Content (from Python):")
    st.text(new_content)
"""
AI Chat Component Integration
Provides a Streamlit component wrapper for the AI chat interface.
"""

import streamlit.components.v1 as components
import os
from typing import Dict, Any, List, Optional
import uuid

# Create component declaration
_component_func = components.declare_component(
    "ai_chat",
    path=os.path.join(os.path.dirname(__file__), "document_editor_component", "frontend", "build")
)


def st_ai_chat(
    document_content: str,
    document_metadata: Dict[str, Any],
    matter_metadata: Dict[str, Any],
    version_id: str,
    session_id: Optional[str] = None,
    messages: List[Dict[str, Any]] = None,
    is_streaming: bool = False,
    height: int = 700,
    key: Optional[str] = None
):
    """
    Render the AI Chat component.
    
    Args:
        document_content: Current document HTML content
        document_metadata: Document metadata (type, subtype, title)
        matter_metadata: Matter metadata (name, client, jurisdiction)
        version_id: Current document version ID
        session_id: Chat session ID (auto-generated if not provided)
        messages: List of chat messages
        is_streaming: Whether AI is currently streaming a response
        height: Component height in pixels
        key: Unique key for the component
        
    Returns:
        Component value (chat action from user)
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    if messages is None:
        messages = []
    
    component_value = _component_func(
        documentContent=document_content,
        documentMetadata=document_metadata,
        matterMetadata=matter_metadata,
        versionId=version_id,
        sessionId=session_id,
        messages=messages,
        isStreaming=is_streaming,
        height=height,
        default=None,
        key=key
    )
    
    return component_value


# For development/testing
if __name__ == "__main__":
    import streamlit as st
    
    st.set_page_config(page_title="AI Chat Test", layout="wide")
    
    st.title("AI Chat Component Test")
    
    # Test data
    test_doc_content = "<h1>Test Document</h1><p>This is a test document.</p>"
    test_doc_metadata = {
        "type": "Agreement",
        "subtype": "Service Agreement",
        "title": "Test Service Agreement"
    }
    test_matter_metadata = {
        "name": "Test Matter",
        "client_name": "Test Client",
        "jurisdiction": "Kenya"
    }
    
    # Render component test
    action = st_ai_chat(
        document_content=test_doc_content,
        document_metadata=test_doc_metadata,
        matter_metadata=test_matter_metadata,
        version_id="test-version-123",
        key="test_chat"
    )
    
    if action:
        st.write("Chat Action:", action)

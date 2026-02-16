import streamlit.components.v1 as components
import os
from typing import List, Dict, Any

# Set to True for production builds (after running npm run build)
_RELEASE = True 

parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "frontend/build")

if not _RELEASE:
    # Development mode - make sure React dev server is running on port 3003
    _component_func = components.declare_component(
        "st_document_outline",
        url="http://localhost:3003",
    )
else:
    # Production mode - use built files
    if not os.path.exists(build_dir):
        raise FileNotFoundError(
            f"Build directory not found at {build_dir}. "
            f"Please run 'npm run build' in the frontend directory."
        )
    _component_func = components.declare_component(
        "st_document_outline", 
        path=build_dir
    )


def st_document_outline(headings: List[Dict[str, Any]], key: str = None, height: int = 800) -> str or None:
    """
    Renders an interactive document outline/table of contents.

    Parameters
    ----------
    headings: List[Dict[str, Any]]
        A list of heading objects (containing 'level', 'text', 'id').
    key: str or None
        An optional key that uniquely identifies this component.
    height: int
        The fixed height of the component in pixels.

    Returns
    -------
    str or None
        The 'id' of the heading the user clicked.
    """
    component_value = _component_func(
        headings=headings,
        height=height,
        key=key,
        default=None,
    )
    return component_value
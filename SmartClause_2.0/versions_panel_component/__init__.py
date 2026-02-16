import streamlit.components.v1 as components
import os
from typing import List, Dict, Any

_RELEASE = True 

parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "frontend/build")

if not _RELEASE:
    _component_func = components.declare_component(
        "st_versions_panel",
        url="http://localhost:3002", # Port from package.json
    )
else:
    _component_func = components.declare_component("st_versions_panel", path=build_dir)


def st_versions_panel(versions: List[Dict[str, Any]], current_version_id: str, key: str = None, height: int = 500):
    """
    Renders the Versions Panel component.

    Parameters
    ----------
    versions: List[Dict[str, Any]]
        A list of version dictionaries. Python datetimes should be
        converted to ISO strings (e.g., `dt.isoformat()`).
    current_version_id: str
        The ID of the currently active version.
    key: str or None
        An optional key that uniquely identifies this component.
    height: int
        The fixed height of the component in pixels.

    Returns
    -------
    str
        The ID of the version selected (clicked) by the user.
    """
    
    # Process versions to ensure timestamps are strings
    processed_versions = []
    for v in versions:
        v_copy = v.copy()
        if 'timestamp' in v_copy and hasattr(v_copy['timestamp'], 'isoformat'):
             v_copy['timestamp'] = v_copy['timestamp'].isoformat()
        elif 'created_at' in v_copy and hasattr(v_copy['created_at'], 'isoformat'):
             # Handle common variation
             v_copy['timestamp'] = v_copy['created_at'].isoformat()
        
        processed_versions.append(v_copy)

    component_value = _component_func(
        versions=processed_versions,
        currentVersionId=current_version_id,
        height=height,
        key=key,
        default=current_version_id, 
    )
    return component_value
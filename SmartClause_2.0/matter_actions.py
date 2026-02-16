import streamlit as st
from database import DatabaseManager


def render_matter_actions_menu(matter_id: str, matter_name: str):
    """
    Render the actions dropdown menu for a matter card.
    This creates a modal-like interface for matter actions.
    """
    
    # Create a unique key for this matter's menu
    menu_key = f"matter_menu_{matter_id}"
    
    # Check if this menu is open
    if st.session_state.get(menu_key, False):
        # Show the action menu modal
        with st.container():
            st.markdown(f"""
<div id="{menu_key}" style="
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
" onclick="if(event.target.id==='{menu_key}') {{ window.parent.postMessage({{type: 'streamlit:setComponentValue', value: {{close: '{menu_key}'}}}}, '*'); }}">
    <div style="
        background: #1A1D24;
        border: 1px solid #252930;
        border-radius: 12px;
        padding: 16px;
        min-width: 300px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    ">
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #252930;
        ">
            <h3 style="margin: 0; font-size: 16px; color: #FFFFFF;">{matter_name}</h3>
            <button onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: {{close: '{menu_key}'}}}}, '*');" style="
                background: transparent;
                border: none;
                color: #9BA1B0;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
            ">×</button>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📌 Pin", key=f"pin_{matter_id}", use_container_width=True):
                    handle_pin_matter(matter_id)
                    st.session_state[menu_key] = False
                    st.rerun()
            
            with col2:
                if st.button("📦 Archive", key=f"archive_{matter_id}", use_container_width=True):
                    handle_archive_matter(matter_id)
                    st.session_state[menu_key] = False
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Delete", key=f"delete_{matter_id}", use_container_width=True):
                    st.session_state[f"confirm_delete_{matter_id}"] = True
                    st.session_state[menu_key] = False
                    st.rerun()
            
            # Close button
            if st.button("Cancel", key=f"cancel_{matter_id}", use_container_width=True, type="secondary"):
                st.session_state[menu_key] = False
                st.rerun()
    
    # Handle delete confirmation
    if st.session_state.get(f"confirm_delete_{matter_id}", False):
        with st.container():
            st.warning(f"⚠️ Are you sure you want to delete '{matter_name}'?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Yes, Delete", key=f"confirm_yes_{matter_id}", use_container_width=True, type="primary"):
                    handle_delete_matter(matter_id)
                    st.session_state[f"confirm_delete_{matter_id}"] = False
                    st.success(f"Deleted '{matter_name}'")
                    st.rerun()
            
            with col2:
                if st.button("Cancel", key=f"confirm_no_{matter_id}", use_container_width=True):
                    st.session_state[f"confirm_delete_{matter_id}"] = False
                    st.rerun()


def handle_pin_matter(matter_id: str) -> bool:
    """Toggle pin status for a matter."""
    try:
        db = DatabaseManager()
        db.set_user(st.session_state["user_id"])
        
        # Get current matter
        matter = db.get_matter(matter_id)
        if not matter:
            st.error("Matter not found")
            return False
        
        # Toggle pin status
        current_pinned = matter.get("is_pinned", False)
        new_pinned = not current_pinned
        
        # Update in database
        result = db.update_matter(matter_id, {"is_pinned": new_pinned})
        
        if result:
            action = "Pinned" if new_pinned else "Unpinned"
            st.success(f"{'📌' if new_pinned else '📍'} {action} '{matter['name']}'")
            return True
        else:
            st.error("Failed to update matter")
            return False
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False


def handle_archive_matter(matter_id: str) -> bool:
    """Archive a matter."""
    try:
        db = DatabaseManager()
        db.set_user(st.session_state["user_id"])
        
        # Get current matter
        matter = db.get_matter(matter_id)
        if not matter:
            st.error("Matter not found")
            return False
        
        # Update status to archived
        result = db.update_matter(matter_id, {"status": "archived"})
        
        if result:
            st.success(f"📦 Archived '{matter['name']}'")
            return True
        else:
            st.error("Failed to archive matter")
            return False
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False


def handle_delete_matter(matter_id: str) -> bool:
    """Soft delete a matter."""
    try:
        db = DatabaseManager()
        db.set_user(st.session_state["user_id"])
        
        # Get matter name before deletion
        matter = db.get_matter(matter_id)
        if not matter:
            st.error("Matter not found")
            return False
        
        # Soft delete
        success = db.delete_matter(matter_id, hard_delete=False)
        
        if success:
            return True
        else:
            st.error("Failed to delete matter")
            return False
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False
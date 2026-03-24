import streamlit as st
from datetime import datetime
from database import DatabaseManager
from typing import Dict, Any
import logging
from error_helpers import show_error
from organization_manager import get_user_role_from_org


def get_time_ago(dt: datetime) -> str:
    """Helper to show relative time."""
    if not dt:
        return "Unknown"
    
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    except Exception:
        return "Unknown"


def format_date(dt) -> str:
    """Format datetime for display."""
    if not dt:
        return "Not set"
    
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        return "Unknown"


def get_session_param() -> str:
    """Get session parameter for URLs to maintain authentication."""
    try:
        session_cookie = st.session_state.get("session_cookie", "")
        if session_cookie:
            return f"&session={session_cookie}"
        return ""
    except Exception:
        return ""


def render_edit_matter_modal(matter: Dict[str, Any], db: DatabaseManager):
    """Render the edit matter modal with full functionality using dialog."""
    
    # CRITICAL: Only show if specifically the edit matter flag is True
    # and the new_matter flag is NOT True (to avoid conflicts)
    if not st.session_state.get("show_edit_matter", False):
        return
    
    if st.session_state.get("show_new_matter", False):
        # If new matter modal is also trying to show, prioritize new matter
        return
    
    if not matter:
        st.error("❌ Matter data not available")
        st.session_state["show_edit_matter"] = False
        return
    
    # CRITICAL: Check if the matter_id has changed (user navigated away)
    current_matter_id = st.query_params.get("matter_id")
    if current_matter_id != matter.get("id"):
        # Matter changed, close the modal
        st.session_state["show_edit_matter"] = False
        return
    
    # Use Streamlit's native dialog for better compatibility
    @st.dialog("Edit Matter", width="large")
    def edit_matter_dialog():
        # Form inputs
        name = st.text_input(
            "Matter Name *",
            value=matter.get("name", ""),
            key="edit_matter_name",
            placeholder="Enter matter name"
        )
        
        client_name = st.text_input(
            "Client Name *",
            value=matter.get("client_name", ""),
            key="edit_client_name",
            placeholder="Enter client name"
        )
        
        counterparty = st.text_input(
            "Counterparty",
            value=matter.get("counterparty", "") or "",
            key="edit_counterparty",
            placeholder="Enter counterparty (optional)"
        )
        
        internal_reference = st.text_input(
            "Internal Reference",
            value=matter.get("internal_reference", "") or "",
            key="edit_internal_ref",
            placeholder="Enter internal reference (optional)"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            matter_types = [
                "Corporate", "Real Estate", "Employment", "Litigation", 
                "Intellectual Property", "Family Law", "Probate & Estate", 
                "Commercial", "Banking & Finance", "Tax", "Immigration", 
                "Criminal", "Insurance", "Environmental", "General"
            ]
            current_type = matter.get("matter_type", "General")
            
            # Ensure current_type is in the list even if it's custom
            if current_type and current_type not in matter_types:
                matter_types.append(current_type)
                
            type_index = matter_types.index(current_type) if current_type in matter_types else 0
            
            matter_type = st.selectbox(
                "Matter Type *",
                options=matter_types,
                index=type_index,
                key="edit_matter_type"
            )
        
        with col2:
            jurisdictions = [
                "Kenya", "Uganda", "Tanzania", "Rwanda", "United Kingdom", 
                "United States", "South Africa", "Nigeria", "United Arab Emirates", 
                "Global", "Other"
            ]
            current_jurisdiction = matter.get("jurisdiction", "Kenya")
            
            # Ensure current_jurisdiction is in the list
            if current_jurisdiction and current_jurisdiction not in jurisdictions:
                jurisdictions.append(current_jurisdiction)
                
            jurisdiction_index = jurisdictions.index(current_jurisdiction) if current_jurisdiction in jurisdictions else 0
            
            jurisdiction = st.selectbox(
                "Jurisdiction *",
                options=jurisdictions,
                index=jurisdiction_index,
                key="edit_jurisdiction"
            )
        
        statuses = ["active", "review", "completed", "archived", "on_hold", "pending"]
        current_status = matter.get("status", "active")
        
        # Ensure current_status is in the list
        if current_status and current_status not in statuses:
            statuses.append(current_status)
            
        status_index = statuses.index(current_status) if current_status in statuses else 0
        
        status = st.selectbox(
            "Status *",
            options=statuses,
            index=status_index,
            key="edit_status"
        )
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Cancel", use_container_width=True, key="edit_cancel"):
                st.session_state["show_edit_matter"] = False
                st.rerun()
        
        with col2:
            if st.button("Save Changes", type="primary", use_container_width=True, key="edit_save"):
                if not name or not name.strip():
                    st.error("❌ Matter name is required")
                    return
                
                if not client_name or not client_name.strip():
                    st.error("❌ Client name is required")
                    return
                
                try:
                    updates = {
                        "name": name.strip(),
                        "client_name": client_name.strip(),
                        "counterparty": counterparty.strip() if counterparty else None,
                        "internal_reference": internal_reference.strip() if internal_reference else None,
                        "matter_type": matter_type,
                        "jurisdiction": jurisdiction,
                        "status": status
                    }
                    
                    updated_matter = db.update_matter(matter["id"], updates)
                    
                    if updated_matter:
                        st.success("✅ Matter updated successfully!")
                        st.session_state["show_edit_matter"] = False
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Failed to update matter. Please try again.")
                
                except Exception as e:
                    show_error(e, "matter")
    
    # Show dialog
    edit_matter_dialog()


def render_matter_details():
    """Render the matter details page."""
    
    # CRITICAL: Track the current page view to detect navigation
    st.query_params.get("view", "matters")
    current_matter_id = st.query_params.get("matter_id")
    last_view = st.session_state.get("last_viewed_page", None)
    last_matter_id = st.session_state.get("last_matter_id", None)
    
    # Handle URL actions (triggered by HTML buttons)
    action = st.query_params.get("action")
    if action:
        # Pre-set navigation state to prevent flags from being cleared by the navigation check below
        st.session_state["last_viewed_page"] = "matter_details"
        st.session_state["last_matter_id"] = current_matter_id
        
        if action == "edit_matter":
            st.session_state["show_new_matter"] = False
            st.session_state["show_search_modal"] = False
            st.session_state["modal_mode"] = None
            st.session_state["existing_matter_id"] = None
            st.session_state["show_manage_access"] = False
            st.session_state["show_edit_matter"] = True
            st.query_params["action"] = None
            st.rerun()
        elif action == "new_document":
            st.session_state["show_edit_matter"] = False
            st.session_state["show_manage_access"] = False
            st.session_state["show_new_matter"] = True
            st.session_state["show_search_modal"] = False
            st.session_state["modal_mode"] = "new_document"
            st.session_state["existing_matter_id"] = current_matter_id
            st.query_params["action"] = None
            st.rerun()
        elif action == "manage_access":
            st.session_state["show_edit_matter"] = False
            st.session_state["show_new_matter"] = False
            st.session_state["show_search_modal"] = False
            st.session_state["modal_mode"] = None
            st.session_state["show_manage_access"] = True
            st.query_params["action"] = None
            st.rerun()
    
    # If user navigated to this page from a different view OR different matter, clear modal flags
    if (last_view != "matter_details" or last_matter_id != current_matter_id):
        st.session_state["show_new_matter"] = False
        st.session_state["modal_mode"] = None
        st.session_state["show_edit_matter"] = False
        st.session_state["show_manage_access"] = False
        st.session_state["existing_matter_id"] = None
    
    # Update the last viewed page and matter
    st.session_state["last_viewed_page"] = "matter_details"
    st.session_state["last_matter_id"] = current_matter_id
    
    # Initialize edit matter state
    if "show_edit_matter" not in st.session_state:
        st.session_state["show_edit_matter"] = False
    
    # Check authentication first
    if "user_id" not in st.session_state or not st.session_state.get("user_id"):
        try:
            if "matter_id" in st.query_params:
                st.session_state["return_to_matter"] = st.query_params.get("matter_id")
        except:
            pass
        
        st.error("⚠️ Session expired. Please log in again.")
        st.markdown(
            '<a href="?view=login" class="sc-btn sc-btn-primary" style="display:inline-block; margin-top:16px;">🔐 Log In</a>',
            unsafe_allow_html=True
        )
        return
    
    try:
        matter_id = st.query_params.get("matter_id")
        if not matter_id:
            st.error("No matter ID provided")
            session_param = get_session_param()
            st.markdown(
                f'<a href="?view=matters{session_param}" class="sc-btn sc-btn-primary" style="display:inline-block; margin-top:16px;">← Back to Matters</a>',
                unsafe_allow_html=True
            )
            return
    except Exception:
        st.error("Invalid matter ID")
        return
    
    # Initialize database
    db = DatabaseManager()
    db.set_user(st.session_state["user_id"])
    
    # Fetch matter data
    matter = db.get_matter(matter_id)
    
    if not matter:
        st.error("Matter not found")
        session_param = get_session_param()
        st.markdown(
            f'<a href="?view=matters{session_param}" class="sc-btn sc-btn-primary" style="display:inline-block; margin-top:16px;">← Back to Matters</a>',
            unsafe_allow_html=True
        )
        return
    
    # Store matter in session state for modal access
    st.session_state["current_matter"] = matter
    
    org = db.get_user_organization(st.session_state["user_id"])
    user_role = get_user_role_from_org(org, st.session_state["user_id"]) if org else "member"
    
    is_owner_admin = user_role in ["owner", "admin"]
    is_creator = matter.get("user_id") == st.session_state["user_id"]
    
    # OPTIMIZATION: Don't load full content for the list view
    # Fetch documents with metadata in one go (already optimized in db.get_documents)
    # Check if we have cached documents for this matter to avoid re-fetching on small UI changes
    cache_key = f"docs_{matter_id}"
    if cache_key not in st.session_state or st.session_state.get("_refresh_docs"):
        all_documents = db.get_documents(matter_id, include_content=False)
        
        # OPTIMIZATION: Bulk fetch all versions for these documents in one query
        # to avoid N+1 queries during rendering.
        doc_ids = [d['id'] for d in all_documents]
        all_vers = db.bulk_get_versions(doc_ids)
        
        # Group versions by document_id
        vers_by_doc = {}
        for v in all_vers:
            did = v['document_id']
            if did not in vers_by_doc:
                vers_by_doc[did] = []
            vers_by_doc[did].append(v)
            
        # Enrich documents with version metadata
        for d in all_documents:
            did = d['id']
            d_vers = vers_by_doc.get(did, [])
            d['all_versions'] = d_vers
            # Bulk query is ordered by version_number desc, so index 0 is latest
            d['version_metadata'] = d_vers[0] if d_vers else {}
            
        # Get user names for the last editors
        editor_uids = list(set([d.get("last_edited_by") or (d.get("version_metadata") or {}).get("created_by") for d in all_documents]))
        editor_uids = [u for u in editor_uids if u]
        editors_meta = getattr(db, 'get_users_metadata', lambda x: {})(editor_uids) if editor_uids else {}
        
        for d in all_documents:
            uid = d.get("last_edited_by") or (d.get("version_metadata") or {}).get("created_by")
            if uid and uid in editors_meta:
                meta = editors_meta[uid]
                name = meta.get("full_name") or meta.get("email")
                if name and "@" in name:
                    name = name.split("@")[0]
                d["last_editor_name"] = name
            else:
                d["last_editor_name"] = None
                
        st.session_state[cache_key] = all_documents
        st.session_state["_refresh_docs"] = False
    else:
        all_documents = st.session_state[cache_key]
        
    documents = [d for d in all_documents if d.get("document_type") != "uploaded_file"]
    uploaded_files = [d for d in all_documents if d.get("document_type") == "uploaded_file"]
    
    status_class = "active" if matter["status"] == "active" else "review"
    session_param = get_session_param()
    
    # Header section with functional buttons
    st.markdown(f"""
<div class="sc-main-header">
  <div class="sc-header-left">
    <div class="sc-page-title">{matter["name"]}</div>
    <div class="sc-page-subtitle">
      <span class="sc-status-chip sc-status-{status_class}" style="margin-right: 8px;">{matter["status"]}</span>
      {matter["client_name"]}
    </div>
  </div>
  <div class="sc-header-right">
    <a class="sc-btn sc-btn-secondary" href="?view=matters{session_param}" target="_self">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M19 12H5M5 12l7 7M5 12l7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>Back to Matters</span>
    </a>
  </div>
</div>
""", unsafe_allow_html=True)
    
    # Action Links serving as buttons - styled exactly like "Back to Matters"
    # Note: Using current URL + action
    current_url_base = f"?view=matter_details&matter_id={matter_id}{session_param}"
    
    manage_access_btn = ""
    if is_owner_admin or is_creator:
        manage_access_btn = f"""
  <a href="{current_url_base}&action=manage_access" target="_self" class="sc-btn sc-btn-secondary" style="min-width: 140px; text-decoration: none;">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="9" cy="7" r="4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span>Manage Access</span>
  </a>"""

    st.markdown(f"""
<div style="display: flex; gap: 12px; margin-bottom: 24px;">
  <a href="{current_url_base}&action=edit_matter" target="_self" class="sc-btn sc-btn-secondary" style="min-width: 140px; text-decoration: none;">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M18.5 2.5a2.121 2 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span>Edit Matter</span>
  </a>{manage_access_btn}
  <a href="{current_url_base}&action=new_document" target="_self" class="sc-btn sc-btn-primary" style="min-width: 140px; text-decoration: none;">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <polyline points="14 2 14 8 20 8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="12" y1="18" x2="12" y2="12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="9" y1="15" x2="15" y2="15" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span>New Document</span>
  </a>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<div style="padding: 0; margin-top: 24px;">', unsafe_allow_html=True)
    
    st.markdown("""
<div style="margin-bottom: 24px;">
  <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="color: #4B9EFF;">
      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <polyline points="13 2 13 9 20 9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg>
    <h2 style="font-size: 18px; font-weight: 600; color: #FFFFFF; margin: 0;">Matter Information</h2>
  </div>
</div>
""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
<div class="panel" style="height: 100%;">
  <div style="margin-bottom: 20px;">
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #9BA1B0; margin-bottom: 6px;">Client Name</div>
    <div style="font-size: 15px; color: #FFFFFF; font-weight: 500;">{matter.get("client_name", "Not specified")}</div>
  </div>
  
  <div style="margin-bottom: 20px;">
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #9BA1B0; margin-bottom: 6px;">Counterparty</div>
    <div style="font-size: 15px; color: #FFFFFF; font-weight: 500;">{matter.get("counterparty") or "Not specified"}</div>
  </div>
  
  <div style="margin-bottom: 20px;">
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #9BA1B0; margin-bottom: 6px;">Internal Reference</div>
    <div style="font-size: 15px; color: #FFFFFF; font-weight: 500;">{matter.get("internal_reference") or "Not specified"}</div>
  </div>
  
  <div>
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #9BA1B0; margin-bottom: 6px;">Matter Type</div>
    <div style="font-size: 15px; color: #FFFFFF; font-weight: 500;">{matter.get("matter_type") or "General"}</div>
  </div>
</div>
""", unsafe_allow_html=True)
    
    with col2:
        created_time = format_date(matter.get("created_at"))
        updated_time = format_date(matter.get("updated_at"))
        updated_ago = get_time_ago(matter.get("updated_at")) if matter.get("updated_at") else "Unknown"
        
        st.markdown(f"""
<div class="panel" style="height: 100%;">
  <div style="margin-bottom: 20px;">
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #9BA1B0; margin-bottom: 6px;">Jurisdiction</div>
    <div style="font-size: 15px; color: #FFFFFF; font-weight: 500;">{matter.get("jurisdiction", "Not specified")}</div>
  </div>
  
  <div style="margin-bottom: 20px;">
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #9BA1B0; margin-bottom: 6px;">Status</div>
    <div>
      <span class="sc-status-chip sc-status-{status_class}">{matter["status"]}</span>
    </div>
  </div>
  
  <div style="margin-bottom: 20px;">
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #9BA1B0; margin-bottom: 6px;">Created</div>
    <div style="font-size: 15px; color: #FFFFFF; font-weight: 500;">{created_time}</div>
  </div>
  
  <div>
    <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #9BA1B0; margin-bottom: 6px;">Last Updated</div>
    <div style="font-size: 15px; color: #FFFFFF; font-weight: 500;">{updated_time}</div>
    <div style="font-size: 13px; color: #9BA1B0; margin-top: 4px;">({updated_ago})</div>
  </div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
    
    # ==================== CASE MANAGER SECTION ====================
    st.markdown("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="color: #4B9EFF;">
    <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
    <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>
    <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>
    <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>
  </svg>
  <h2 style="font-size: 18px; font-weight: 600; color: #FFFFFF; margin: 0;">Case Manager</h2>
</div>
""", unsafe_allow_html=True)
    
    # Import and render case manager component
    try:
        from components.case_manager import render_case_manager
        render_case_manager(matter_id, matter["name"], db)
    except Exception as e:
        logging.error(f"Error loading case manager: {e}", exc_info=True)
        st.error("⚠️ Case manager is temporarily unavailable.")
        st.info("💡 Please try refreshing the page.")
    
    st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
    
    # Documents section
    st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
  <div style="display: flex; align-items: center; gap: 8px;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="color: #4B9EFF;">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
      <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2"/>
      <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
      <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/>
      <polyline points="10 9 9 9 8 9" stroke="currentColor" stroke-width="2"/>
    </svg>
    <h2 style="font-size: 18px; font-weight: 600; color: #FFFFFF; margin: 0;">Documents ({len(documents)})</h2>
  </div>
</div>
""", unsafe_allow_html=True)
    
    if documents:
        for doc in documents:
            doc_status = doc.get("status", "draft")
            status_colors = {
                "generating": "#F59E0B",
                "draft": "#4B9EFF",
                "review": "#F59E0B",
                "final": "#4ADE80"
            }
            status_color = status_colors.get(doc_status, "#9BA1B0")
            
            created_ago = get_time_ago(doc.get("created_at"))
            doc_id = doc['id']
            
            # CRITICAL FIX: Store doc_id in a unique session state key immediately
            # This ensures each button has its own stable reference
            button_state_key = f"doc_button_data_{doc_id}"
            if button_state_key not in st.session_state:
                st.session_state[button_state_key] = doc_id
            
            # Use pre-fetched metadata from the optimized join
            version_metadata = doc.get("version_metadata", {})
            word_count = version_metadata.get('word_count', 0) if version_metadata else 0
            
            # version_count comes from the 'all_versions' join
            ver_info = doc.get("all_versions", [])
            version_count = len(ver_info) if ver_info and isinstance(ver_info, list) else 1
            
            st.markdown(f"""
<a href="?view=editor&document_id={doc_id}&matter_id={matter_id}{session_param}" target="_self" style="text-decoration: none; display: block; color: inherit; margin-bottom: 12px;">
  <div style="display: flex; align-items: center; justify-content: space-between; background: #1A1D24; border: 1px solid #252930; border-radius: 12px; padding: 16px 20px; transition: all 0.15s ease;">
    <div style="display: flex; align-items: center; gap: 16px; flex: 1;">
      <div style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; background: rgba(255, 255, 255, 0.05); flex-shrink: 0;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke-width="2"/>
          <polyline points="14 2 14 8 20 8" stroke-width="2"/>
        </svg>
      </div>
      <div style="display: flex; flex-direction: column; gap: 4px; min-width: 0;">
        <div style="font-size: 16px; font-weight: 600; color: #FFFFFF;">{doc.get("title", "Untitled Document")}</div>
        <div style="font-size: 13px; color: #6B7280; display: flex; align-items: center; gap: 6px;">
          <span>{doc.get("document_type", "Document")}</span>
          {f'<span style="opacity: 0.5;">•</span><span>{doc.get("document_subtype")}</span>' if doc.get("document_subtype") else ""}
          <span style="opacity: 0.5;">•</span>
          <span>{version_count} version{"s" if version_count != 1 else ""}</span>
          <span style="opacity: 0.5;">•</span>
          <span>Edited {created_ago}{f" by {doc['last_editor_name']}" if doc.get('last_editor_name') else ""}</span>
        </div>
      </div>
    </div>
    <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0;">
      <span style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; background: rgba(75, 158, 255, 0.12); color: {status_color};">
        <span style="width: 6px; height: 6px; border-radius: 50%; background: {status_color};"></span>
        {doc_status}
      </span>
    </div>
  </div>
</a>
""", unsafe_allow_html=True)
            
            # Removed button and callback logic as the card itself is now the link
    else:
        st.markdown(f"""
<div style="background: rgba(255, 255, 255, 0.03); border: 1px solid #252930; border-radius: 12px; padding: 32px; text-align: center;">
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" style="color: #6B7280; margin: 0 auto 16px;">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
    <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2"/>
  </svg>
  <div style="font-size: 16px; color: #9BA1B0; margin-bottom: 8px;">No documents yet</div>
  <div style="font-size: 14px; color: #6B7280; margin-bottom: 20px;">Create your first document for this matter</div>
</div>
""", unsafe_allow_html=True)
        
        if st.button("Create First Document", key="create_first_doc", use_container_width=True, type="primary"):
            # CRITICAL: Clear edit matter flag
            st.session_state["show_edit_matter"] = False
            # Set new document flags
            st.session_state["show_new_matter"] = True
            st.session_state["show_search_modal"] = False  # Clear conflict
            st.session_state["modal_mode"] = "new_document"
            st.session_state["existing_matter_id"] = matter_id
            st.rerun()
    
    st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
    
    # ==================== ATTACHED FILES SECTION ====================
    st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
  <div style="display: flex; align-items: center; gap: 8px;">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="color: #4B9EFF;">
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <h2 style="font-size: 18px; font-weight: 600; color: #FFFFFF; margin: 0;">Attached Files ({len(uploaded_files)})</h2>
  </div>
</div>
""", unsafe_allow_html=True)

    with st.container():
        # CSS to style the file uploader to match document cards (#1A1D24) and button (#4B9EFF)
        st.markdown("""
        <style>
            [data-testid="stFileUploaderDropzone"] {
                background-color: #1A1D24 !important;
                border: 1px dashed #252930 !important;
                border-radius: 12px !important;
            }
            [data-testid="stFileUploader"] label,
            [data-testid="stFileUploaderDropzone"],
            [data-testid="stFileUploaderDropzone"] div,
            [data-testid="stFileUploaderDropzone"] small {
                color: #FFFFFF !important;
            }
            [data-testid="stFileUploaderDropzone"] button {
                background-color: #4B9EFF !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
            }
            [data-testid="stFileUploaderDropzone"] button:hover {
                background-color: #3A8AE0 !important;
                color: white !important;
            }
        </style>
        """, unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload a new file (ID, KRA PIN, doc, etc.)", type=["png", "jpg", "jpeg", "pdf"], key="matter_file_uploader")
        if uploaded_file is not None:
            if st.button("Save Uploaded File", type="primary"):
                import base64
                file_bytes = uploaded_file.getvalue()
                base64_data = base64.b64encode(file_bytes).decode('utf-8')
                mime_type = uploaded_file.type
                
                with st.spinner("Uploading..."):
                    result = db.upload_matter_file(matter_id, uploaded_file.name, mime_type, base64_data)
                    if result:
                        st.session_state["_refresh_docs"] = True
                        st.success("File uploaded successfully!")
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to upload file.")

    if uploaded_files:
        @st.dialog("View Attached File")
        def view_attached_file_dialog(fdoc, db):
            st.markdown("""
                <style>
                /* Target the delete button in the 2nd column of the horizontal block inside the dialog */
                div[data-testid="stDialog"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) button {
                    background-color: #EF4444 !important;
                    border-color: #EF4444 !important;
                    color: white !important;
                }
                div[data-testid="stDialog"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) button p {
                    color: white !important;
                }
                div[data-testid="stDialog"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) button:hover {
                    background-color: #DC2626 !important;
                    border-color: #DC2626 !important;
                    color: white !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            with st.spinner("Loading file..."):
                latest_version = db.get_latest_version(fdoc["id"])
                
            if latest_version and latest_version.get("content"):
                import base64
                file_data = base64.b64decode(latest_version["content"])
                mime_type = latest_version.get("content_plain", "application/octet-stream")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.download_button(
                        label="Download File",
                        data=file_data,
                        file_name=fdoc.get("title", "download"),
                        mime=mime_type,
                        key=f"dl_dialog_{fdoc['id']}",
                        use_container_width=True
                    )
                with col_btn2:
                    if st.button(
                        "Delete File", 
                        key=f"del_dialog_{fdoc['id']}", 
                        use_container_width=True,
                        help="Permanently delete this uploaded file"
                    ):
                        with st.spinner("Deleting..."):
                            if hasattr(db, "delete_document"):
                                db.delete_document(fdoc["id"])
                            st.success("File deleted! Refreshing...")
                            import time
                            time.sleep(0.5)
                            import streamlit.components.v1 as components
                            components.html("<script>window.parent.location.reload();</script>", height=0, width=0)
                            st.stop()
                
                if mime_type.startswith("image/"):
                    st.image(file_data, use_container_width=True)
            else:
                st.error("File content not found.")

        for fdoc in uploaded_files:
            fdoc_id = fdoc['id']
            created_ago = get_time_ago(fdoc.get("created_at"))
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255, 255, 255, 0.03); border: 1px solid #252930; border-radius: 8px; margin-bottom: 8px;">
                  <div style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 6px; background: rgba(255, 255, 255, 0.05); flex-shrink: 0;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" stroke-width="2"/>
                    </svg>
                  </div>
                  <div>
                    <div style="font-size: 14px; font-weight: 500; color: #FFFFFF;">{fdoc.get("title", "Untitled")}</div>
                    <div style="font-size: 12px; color: #6B7280;">Uploaded {created_ago}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown('<div style="margin-top: 14px;"></div>', unsafe_allow_html=True)
                if st.button("View", key=f"view_doc_{fdoc_id}", use_container_width=True):
                    view_attached_file_dialog(fdoc, db)

    st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
    
    st.markdown("""
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="color: #4B9EFF;">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
  <h2 style="font-size: 18px; font-weight: 600; color: #FFFFFF; margin: 0;">Recent Activity</h2>
</div>
""", unsafe_allow_html=True)
    
    activity = db.get_activity_log(limit=10, entity_type="matter")
    matter_activity = [a for a in activity if a.get("entity_id") == matter_id]
    
    if matter_activity:
        for activity_item in matter_activity[:5]:
            activity_time = get_time_ago(activity_item.get("created_at"))
            activity_desc = activity_item.get("description", "Activity")
            
            st.markdown(f"""
<div style="display: flex; align-items: start; gap: 12px; padding: 12px; background: rgba(255, 255, 255, 0.03); border: 1px solid #252930; border-radius: 8px; margin-bottom: 8px;">
  <div style="width: 8px; height: 8px; border-radius: 50%; background: #4B9EFF; margin-top: 6px; flex-shrink: 0;"></div>
  <div style="flex: 1;">
    <div style="font-size: 14px; color: #FFFFFF;">{activity_desc}</div>
    <div style="font-size: 12px; color: #9BA1B0; margin-top: 4px;">{activity_time}</div>
  </div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div style="background: rgba(255, 255, 255, 0.03); border: 1px solid #252930; border-radius: 8px; padding: 20px; text-align: center;">
  <div style="font-size: 14px; color: #6B7280;">No recent activity</div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # CRITICAL: Only render edit modal if explicitly requested AND not showing new matter modal
    should_show_edit_modal = (
        st.session_state.get("show_edit_matter", False) and
        not st.session_state.get("show_new_matter", False) and
        not st.session_state.get("show_manage_access", False)
    )
    
    if should_show_edit_modal:
        render_edit_matter_modal(matter, db)
        
    if st.session_state.get("show_manage_access", False) and (is_owner_admin or is_creator):
        @st.dialog("Manage Matter Access", width="large")
        def manage_access_dialog():
            st.markdown("### Team Permissions")
            st.markdown("Configure which team members can view and interact with this matter and its documents.")
            
            # Fetch organization members
            if org:
                # Fetch accesses first
                accesses = db.get_matter_access(matter_id)
                access_map = {a.get("user_id"): a for a in accesses}
                
                members = db.client.table("organization_members").select("*").eq("organization_id", org["id"]).eq("status", "active").execute().data
                
                if members:
                    uids = [m.get("user_id") for m in members if m.get("user_id")]
                    users_meta = getattr(db, 'get_users_metadata', lambda x: {})(uids) if uids else {}
                    
                    for member in members:
                        uid = member.get("user_id")
                        member_role = member.get("role")
                        user_info = users_meta.get(uid, {})
                        
                        name = user_info.get("full_name") or user_info.get("name") or user_info.get("email") or "Unknown Member"
                        email_display = user_info.get("email", "")
                        
                        col_info, col_status, col_btn = st.columns([4, 2, 2])
                        with col_info:
                            st.write(f"**{name}**")
                            st.caption(f"{email_display}")
                        
                        # Owners and Admins inherently have access
                        if member_role in ['owner', 'admin'] or uid == matter.get("user_id"):
                            with col_status:
                                st.write("Full Access")
                            with col_btn:
                                st.button("Locked (Role based)", key=f"ma_lk_{uid}", disabled=True)
                        else:
                            has_access = uid in access_map
                            with col_status:
                                st.write("Explicit Access" if has_access else "No Access")
                            with col_btn:
                                if has_access:
                                    if st.button("Revoke Access", key=f"ma_rev_{uid}"):
                                        db.revoke_matter_access(matter_id, uid)
                                        st.success(f"Revoked access for {name}")
                                        import time; time.sleep(0.5)
                                        st.rerun()
                                else:
                                    if st.button("Grant Access", key=f"ma_gnt_{uid}"):
                                        db.grant_matter_access(matter_id, uid, "edit")
                                        st.success(f"Granted access to {name}")
                                        import time; time.sleep(0.5)
                                        st.rerun()
                                        
            if st.button("Close", key="ma_close", type="primary"):
                st.session_state["show_manage_access"] = False
                st.rerun()
                
        manage_access_dialog()
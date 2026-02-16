import streamlit as st
import time
from clause_library import render_clause_library 
from export import render_exports
from settings import render_settings
from new_matter_modal import render_new_matter_modal
from document_editor import render_document_editor
from database import DatabaseManager
from auth import check_authentication, logout
from matter_actions import handle_pin_matter, handle_archive_matter, handle_delete_matter
from search import render_search_modal
from pricing_page import render_pricing_page
from subscription_manager import SubscriptionManager
from components.organization_dashboard import render_organization_dashboard
# ============================================================================
# PAGE CONFIG - MUST BE FIRST
# ============================================================================
st.set_page_config(
    page_title="SmartClause – Legal Drafting Assistant",
    page_icon="assets/smartclause_badge.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# LOAD CSS BEFORE AUTHENTICATION CHECK
# ============================================================================
def local_css(path: str = "styles.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

local_css()

# ============================================================================
# CRITICAL: PRESERVE QUERY PARAMS BEFORE AUTH CHECK
# ============================================================================
def preserve_navigation_state():
    """Preserve critical navigation state before authentication check."""
    try:
        # Store query params in session state if they exist
        if "view" in st.query_params:
            view = st.query_params.get("view")
            st.session_state["preserved_view"] = view
            # Also store in a cookie-like persistent way
            if "session_navigation" not in st.session_state:
                st.session_state["session_navigation"] = {}
            st.session_state["session_navigation"]["view"] = view
        
        if "document_id" in st.query_params:
            doc_id = st.query_params.get("document_id")
            st.session_state["preserved_document_id"] = doc_id
            st.session_state["current_document_id"] = doc_id
            if "session_navigation" not in st.session_state:
                st.session_state["session_navigation"] = {}
            st.session_state["session_navigation"]["document_id"] = doc_id
        
        if "matter_id" in st.query_params:
            matter_id = st.query_params.get("matter_id")
            st.session_state["preserved_matter_id"] = matter_id
            if "session_navigation" not in st.session_state:
                st.session_state["session_navigation"] = {}
            st.session_state["session_navigation"]["matter_id"] = matter_id
        
        # CRITICAL: Preserve generation state if in editor
        if "view" in st.query_params and st.query_params.get("view") == "editor":
            # Mark that we're in editor mode to prevent false "no data" errors
            st.session_state["editor_mode_active"] = True
            
    except Exception as e:
        # Silently fail to avoid breaking the app
        pass

preserve_navigation_state()

# ============================================================================
# AUTHENTICATION CHECK - WILL STOP HERE IF NOT LOGGED IN
# This now uses Supabase session recovery automatically
# ============================================================================
check_authentication()

# ============================================================================
# RESTORE SESSION STATE IMMEDIATELY AFTER AUTH
# ============================================================================
# If we had navigation state before auth, restore it now
if "session_navigation" in st.session_state:
    nav = st.session_state["session_navigation"]
    
    if "view" in nav and "view" not in st.query_params:
        try:
            st.query_params["view"] = nav["view"]
        except:
            pass
    
    if "document_id" in nav and "document_id" not in st.query_params:
        try:
            st.query_params["document_id"] = nav["document_id"]
            st.session_state["current_document_id"] = nav["document_id"]
            st.session_state["preserved_document_id"] = nav["document_id"]
        except:
            pass
    
    if "matter_id" in nav and "matter_id" not in st.query_params:
        try:
            st.query_params["matter_id"] = nav["matter_id"]
        except:
            pass



# ============================================================================
# IF WE REACH HERE, USER IS AUTHENTICATED
# ============================================================================

# Initialize UI state AFTER authentication
if "show_new_matter" not in st.session_state:
    st.session_state["show_new_matter"] = False
# Initialize edit matter state
if "show_edit_matter" not in st.session_state:
    st.session_state["show_edit_matter"] = False

# Initialize filter state
if "filter_status" not in st.session_state:
    st.session_state["filter_status"] = "all"
if "filter_matter_type" not in st.session_state:
    st.session_state["filter_matter_type"] = "all"
if "filter_jurisdiction" not in st.session_state:
    st.session_state["filter_jurisdiction"] = "all"

# Initialize Database
@st.cache_resource
def get_database():
    # Cache cleared for performance optimization updates
    return DatabaseManager()

db = get_database()

# Set user_id from authenticated session
if st.session_state.get("user_id"):
    db.set_user(st.session_state["user_id"])

# Initialize Subscription Manager
@st.cache_resource
def get_subscription_manager():
    return SubscriptionManager(get_database())

subscription_mgr = get_subscription_manager()

# ============================================================================
# ROUTING & QUERY PARAMS
# ============================================================================
def check_new_matter_trigger():
    """Check if New Matter or New Document button was clicked via query params."""
    try:
        # Check for new_matter trigger (creates new matter)
        if "new_matter" in st.query_params:
            st.session_state["show_new_matter"] = True
            st.session_state["show_search_modal"] = False  # Clear conflict
            st.session_state["show_edit_matter"] = False   # Clear conflict
            st.session_state["modal_mode"] = "new_matter"
            st.session_state["existing_matter_id"] = None
            # Clear the query param to prevent re-triggering
            del st.query_params["new_matter"]
        
        # Check for new_document trigger (adds doc to existing matter)
        elif "new_document" in st.query_params:
            matter_id = st.query_params.get("matter_id")
            if matter_id:
                st.session_state["show_new_matter"] = True
                st.session_state["show_search_modal"] = False  # Clear conflict
                st.session_state["show_edit_matter"] = False   # Clear conflict
                st.session_state["modal_mode"] = "new_document"
                st.session_state["existing_matter_id"] = matter_id
                del st.query_params["new_document"]
    except:
        pass

check_new_matter_trigger()

def get_view() -> str:
    """Query-param router with fallback to session state."""
    try:
        view = st.query_params.get("view", "matters")
        # Store current view in session state
        st.session_state["current_view"] = view
        return view if isinstance(view, str) else "matters"
    except Exception:
        # Fallback to session state if query params fail
        return st.session_state.get("current_view", "matters")

view = get_view()

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:


    # Sidebar Logo
    try:
        import base64
        import os
        logo_path = "assets/sidebar_logo.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin-bottom: 20px; margin-top: 10px;">
                    <img src="data:image/png;base64,{data}" style="width: 70%; height: auto; border: none; background: transparent;">
                </div>
                """,
                unsafe_allow_html=True
            )
    except Exception:
        pass

    # User info
    user_email = st.session_state.get("user_email", "Unknown User")
    st.markdown(f"""
<div style="padding: 8px 12px; background: rgba(75, 158, 255, 0.1); border-radius: 6px; margin: 12px 16px;">
    <div style="color: #9BA1B0; font-size: 11px;">Logged in as:</div>
    <div style="color: #FFFFFF; font-size: 13px; font-weight: 500;">{user_email}</div>
</div>
""", unsafe_allow_html=True)

    # Subscription Status
    user_id = st.session_state.get("user_id")
    if user_id:
        status = subscription_mgr.get_user_status(user_id)
        tier = status.get("tier", "single_credit")
        credits = status.get("credits", 0)
        is_active = status.get("is_active", False)
        
        tier_names = {
            "single_credit": "Single Credit",
            "pay_as_you_go": "Pay-As-You-Go",
            "standard": "Standard"
        }
        tier_display = tier_names.get(tier, tier)
        
        # Color based on tier
        tier_colors = {
            "single_credit": "#4ADE80",
            "pay_as_you_go": "#F59E0B",
            "standard": "#4B9EFF"
        }
        tier_color = tier_colors.get(tier, "#9BA1B0")
        
        # Credit display
        if tier in ["single_credit", "pay_as_you_go"]:
            credit_text = f"{credits} credit{'s' if credits != 1 else ''} remaining"
            credit_color = "#4ADE80" if credits > 0 else "#FF6B6B"
        else:
            credit_text = "Unlimited"
            credit_color = "#4ADE80"
        
        st.markdown(f"""
<div style="padding: 8px 12px; background: #1A1D24; border: 1px solid #252930; border-radius: 6px; margin: 12px 16px;">
    <div style="color: {tier_color}; font-size: 13px; font-weight: 600; margin-bottom: 2px;">{tier_display}</div>
    <div style="color: {credit_color}; font-size: 11px;">{credit_text}</div>
</div>
""", unsafe_allow_html=True)

    # New Matter Button
    if st.button("New Matter", key="sidebar_new_matter", use_container_width=True, type="primary"):
        st.session_state["show_new_matter"] = True
        st.session_state["show_search_modal"] = False  # Clear conflict
        st.session_state["show_edit_matter"] = False   # Clear conflict
        st.session_state["modal_mode"] = "new_matter"
        st.session_state["existing_matter_id"] = None
        st.rerun()

    # Interactive Search Box
    st.markdown('<div style="margin-bottom: 16px;"></div>', unsafe_allow_html=True)
    
    # Initialize search modal state
    if "show_search_modal" not in st.session_state:
        st.session_state["show_search_modal"] = False
    
    # Search button that opens modal
    if st.button(
        f"Search {'clauses' if view=='clause_library' else 'matters'}",
        key="search_trigger_btn",
        use_container_width=True,
        type="secondary"
    ):
        st.session_state["show_search_modal"] = True
        st.session_state["show_new_matter"] = False    # Clear conflict
        st.session_state["show_edit_matter"] = False   # Clear conflict
        st.rerun()
    
    st.markdown('<div style="margin-bottom: 16px;"></div>', unsafe_allow_html=True)

    # Get session param helper
    def get_session_param():
        """Get session parameter for URLs."""
        session_cookie = st.session_state.get("session_cookie", "")
        if session_cookie:
            return f"&session={session_cookie}"
        return ""

    session_param = get_session_param()
    
    # Navigation
    def nav_item(label, icon_svg, href_view, is_active):
        active_cls = " sc-nav-active" if is_active else ""
        return f"""
<a class="sc-nav-item{active_cls}" href="?view={href_view}{session_param}" target="_self">
  <svg class="sc-nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">{icon_svg}</svg>
  <span>{label}</span>
</a>"""

    matters_icon = """<rect x="4" y="3" width="16" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M8 7h8M8 11h8M8 15h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>"""
    library_icon = """<path d="M6 20V7a2 2 0 0 1 2-2h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                      <rect x="6" y="7" width="12" height="13" rx="2" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M10 10h6M10 13h6M10 16h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>"""
    pricing_icon = """<circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/>
                      <path d="M12 6v12M9 9h3.5a2 2 0 0 1 0 4H9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>"""
    org_icon = """<path d="M3 21h18M5 21V7l8-4 8 4v14M8 10a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>"""

    st.markdown(f"""
<nav class="sc-nav">
  {nav_item("Matters", matters_icon, "matters", view == "matters" or view == "matter_details")}
  {nav_item("Clause Library", library_icon, "clause_library", view == "clause_library")}
  {nav_item("Organization", org_icon, "organization", view == "organization")}
  {nav_item("Pricing", pricing_icon, "pricing", view == "pricing")}
</nav>
""", unsafe_allow_html=True)
    
    # Logout button - Use form to prevent rerun issues
    if st.button("Logout", use_container_width=True, key="logout_btn"):
        logout()

# ============================================================================
# MATTERS PAGE
# ============================================================================
def render_matters():
    # Get session param for links
    def get_session_param():
        """Get session parameter for URLs."""
        session_cookie = st.session_state.get("session_cookie", "")
        if session_cookie:
            return f"&session={session_cookie}"
        return ""
    
    session_param = get_session_param()
    
    # Create header with filter button on the right
    col_title, col_filter = st.columns([4, 1])

    with col_title:
        st.markdown("""
    <div class="sc-header-left" style="padding-top: 8px;">
        <div class="sc-page-title">Matters</div>
        <div class="sc-page-subtitle">Manage your legal matters and documents</div>
    </div>
    """, unsafe_allow_html=True)

    with col_filter:
        st.markdown('<div style="margin-top: 16px; float: right;">', unsafe_allow_html=True)
        
        # Use popover for filter UI with custom class
        with st.popover("Filter", use_container_width=True):
            st.markdown("**Filter Matters**")
            
            # Get all matters to extract unique values (limit to 100 to get a good sample)
            all_matters = db.get_matters(limit=100)
            
            # Extract unique matter types and jurisdictions
            matter_types = sorted(list(set([m.get("matter_type", "General") for m in all_matters])))
            jurisdictions = sorted(list(set([m["jurisdiction"] for m in all_matters])))
            
            # Status filter
            status_filter = st.selectbox(
                "Status",
                options=["all", "active", "review"],
                index=["all", "active", "review"].index(st.session_state["filter_status"]),
                key="status_select"
            )
            
            # Matter type filter
            matter_type_options = ["all"] + matter_types
            current_type_index = 0
            if st.session_state["filter_matter_type"] in matter_type_options:
                current_type_index = matter_type_options.index(st.session_state["filter_matter_type"])
            
            matter_type_filter = st.selectbox(
                "Matter Type",
                options=matter_type_options,
                index=current_type_index,
                key="matter_type_select"
            )
            
            # Jurisdiction filter
            jurisdiction_options = ["all"] + jurisdictions
            current_jurisdiction_index = 0
            if st.session_state["filter_jurisdiction"] in jurisdiction_options:
                current_jurisdiction_index = jurisdiction_options.index(st.session_state["filter_jurisdiction"])
            
            jurisdiction_filter = st.selectbox(
                "Jurisdiction",
                options=jurisdiction_options,
                index=current_jurisdiction_index,
                key="jurisdiction_select"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Apply", use_container_width=True, type="primary"):
                    st.session_state["filter_status"] = status_filter
                    st.session_state["filter_matter_type"] = matter_type_filter
                    st.session_state["filter_jurisdiction"] = jurisdiction_filter
                    st.rerun()
            
            with col2:
                if st.button("Clear", use_container_width=True):
                    st.session_state["filter_status"] = "all"
                    st.session_state["filter_matter_type"] = "all"
                    st.session_state["filter_jurisdiction"] = "all"
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<hr style="border-color: var(--border); margin: 24px 0 16px 0;">', unsafe_allow_html=True)
    
    # Get matters and apply filters
    # CRITICAL FIX: Pass status to DB query if not 'all', and increase limit
    status_filter = None
    if st.session_state["filter_status"] != "all":
        status_filter = st.session_state["filter_status"]
        
    # Increase limit to show more matters (default was 50)
    matters = db.get_matters(status=status_filter, limit=100)
    
    # Apply filters (Matter Type and Jurisdiction still need memory filtering)
    filtered_matters = matters
    
    # Status filter is handled by DB query now, so we don't need memory filtering for it
    
    # Filter by matter type
    if st.session_state["filter_matter_type"] != "all":
        filtered_matters = [m for m in filtered_matters if m.get("matter_type", "General") == st.session_state["filter_matter_type"]]
    
    # Filter by jurisdiction
    if st.session_state["filter_jurisdiction"] != "all":
        filtered_matters = [m for m in filtered_matters if m["jurisdiction"] == st.session_state["filter_jurisdiction"]]
    
    # Show active filters
    active_filters = []
    if st.session_state["filter_status"] != "all":
        active_filters.append(f"Status: {st.session_state['filter_status']}")
    if st.session_state["filter_matter_type"] != "all":
        active_filters.append(f"Type: {st.session_state['filter_matter_type']}")
    if st.session_state["filter_jurisdiction"] != "all":
        active_filters.append(f"Jurisdiction: {st.session_state['filter_jurisdiction']}")
    
    if active_filters:
        st.markdown(f"""
<div style="padding: 12px; background: rgba(75, 158, 255, 0.1); border-radius: 6px; margin: 0 32px 16px 32px; color: #9BA1B0; font-size: 13px;">
    <strong>Active Filters:</strong> {" • ".join(active_filters)} ({len(filtered_matters)} matter{"s" if len(filtered_matters) != 1 else ""} found)
</div>
""", unsafe_allow_html=True)
    
    if not filtered_matters:
        if active_filters:
            st.info("No matters match the current filters. Try adjusting your filter criteria.")
        else:
            st.info("No matters yet. Click 'New Matter' to get started!")
        return
    
    
    # BATCH OPTIMIZATION: Fetch document counts for all displayed matters in one go
    matter_ids = [m["id"] for m in filtered_matters]
    doc_counts = db.get_document_counts_for_matters(matter_ids)
    
    for m in filtered_matters:
        status_class = "active" if m["status"] == "active" else "review"
        
        # Use batch fetched count
        draft_count = doc_counts.get(m["id"], 0)
        
        from datetime import datetime
        updated = datetime.fromisoformat(m["updated_at"])
        time_ago = get_time_ago(updated)   

        # Use Streamlit columns to position the menu button
        col_card, col_menu = st.columns([20, 1])
        
        with col_card:
            st.markdown(f"""
    <a href="?view=matter_details&matter_id={m["id"]}{session_param}" target="_self" style="text-decoration: none; display: block; margin: 0 32px 12px 0;">
    <div class="sc-matter-card" style="margin: 0;">
        <div class="sc-card-left">
        <div class="sc-card-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <rect x="4" y="3" width="16" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 7h8M8 11h8M8 15h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
        </div>
        <div class="sc-card-content">
            <div class="sc-card-title">{m["name"]}</div>
            <div class="sc-card-client">{m["client_name"]}</div>
            <div class="sc-card-meta">
            <span>{m.get("matter_type", "General")}</span>
            <span class="sc-meta-dot">•</span>
            <span>{m["jurisdiction"]}</span>
            <span class="sc-meta-dot">•</span>
            <span>{draft_count} draft{"s" if draft_count != 1 else ""}</span>
            </div>
        </div>
        </div>
        <div class="sc-card-right">
        <span class="sc-status-chip sc-status-{status_class}">{m["status"]}</span>
        <span class="sc-card-time">{time_ago}</span>
        </div>
    </div>
    </a>
    """, unsafe_allow_html=True)
        
        with col_menu:
            st.markdown('<div style="position: absolute; top: 50%; transform: translateY(-50%); z-index: 20; right: 32px;">', unsafe_allow_html=True)
            
            with st.popover("⋮"):
                if st.button("Pin", key=f"pin_{m['id']}", use_container_width=True):
                    handle_pin_matter(m['id'])
                    st.rerun()
                
                if st.button("Archive", key=f"archive_{m['id']}", use_container_width=True):
                    handle_archive_matter(m['id'])
                    st.rerun()
                
                if st.button("Delete", key=f"delete_{m['id']}", use_container_width=True):
                    st.session_state[f"confirm_delete_{m['id']}"] = True
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle delete confirmation
        if st.session_state.get(f"confirm_delete_{m['id']}", False):
            st.warning(f"Are you sure you want to delete '{m['name']}'?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Yes, Delete", key=f"confirm_yes_{m['id']}", use_container_width=True, type="primary"):
                    success = handle_delete_matter(m['id'])
                    st.session_state[f"confirm_delete_{m['id']}"] = False
                    if success:
                        st.success(f"Deleted '{m['name']}'")
                    st.rerun()
            
            with col2:
                if st.button("Cancel", key=f"confirm_no_{m['id']}", use_container_width=True):
                    st.session_state[f"confirm_delete_{m['id']}"] = False
                    st.rerun()

def get_time_ago(dt):
    """Helper to show relative time."""
    from datetime import datetime
    now = datetime.now(dt.tzinfo)
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

# ============================================================================
# ROUTING
# ============================================================================
if view == "matters":
    render_matters()
elif view == "clause_library":
    render_clause_library()
elif view == "pricing":
    render_pricing_page()
elif view == "organization":
    render_organization_dashboard()
elif view == "exports":
    render_exports()
elif view == "settings":
    render_settings()
elif view == "editor":                     
    render_document_editor()
elif view == "matter_details":
    from matter_details import render_matter_details
    render_matter_details()
else:
    render_matters()


# ============================================================================
# SEARCH MODAL - Render if search is triggered
# ============================================================================
render_search_modal(db, view)

# ============================================================================
# MODAL - ALWAYS RENDER AT THE END
# ============================================================================
render_new_matter_modal()
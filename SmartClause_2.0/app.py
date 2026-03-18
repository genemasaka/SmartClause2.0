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
from legal_pages import render_privacy_policy, render_terms_of_use
from analytics import Analytics
# ============================================================================
# PAGE CONFIG - MUST BE FIRST
# ============================================================================
st.set_page_config(
    page_title="SmartClause",
    page_icon="assets/smartclause_badge.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# FAVICON OVERRIDE - Prevent Streamlit logo flash on reload
# ============================================================================
import base64 as _b64, os as _os
_favicon_path = "assets/smartclause_badge.png"
if _os.path.exists(_favicon_path):
    with open(_favicon_path, "rb") as _f:
        _favicon_b64 = _b64.b64encode(_f.read()).decode()
    st.markdown(f"""
    <script>
    (function() {{
        var iconUrl = "data:image/png;base64,{_favicon_b64}";
        // Immediately set favicon
        var link = document.querySelector("link[rel*='icon']");
        if (link) {{
            link.href = iconUrl;
        }} else {{
            link = document.createElement('link');
            link.rel = 'shortcut icon';
            link.href = iconUrl;
            document.head.appendChild(link);
        }}
        // Watch for Streamlit overwriting the favicon and re-apply
        var observer = new MutationObserver(function(mutations) {{
            mutations.forEach(function(m) {{
                if (m.type === 'childList') {{
                    var icons = document.querySelectorAll("link[rel*='icon']");
                    icons.forEach(function(el) {{
                        if (el.href !== iconUrl) el.href = iconUrl;
                    }});
                }}
            }});
        }});
        observer.observe(document.head, {{ childList: true, subtree: true }});
    }})();
    </script>
    """, unsafe_allow_html=True)

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
# PUBLIC PAGES - Accessible without authentication (legal pages)
# ============================================================================
_public_view = st.query_params.get("view", "")
if _public_view in ("privacy", "terms"):
    if not st.session_state.get("authenticated"):
        local_css()  # Ensure styles are loaded
        if _public_view == "privacy":
            render_privacy_policy()
        else:
            render_terms_of_use()
        st.stop()

# ============================================================================
# AUTHENTICATION CHECK - WILL STOP HERE IF NOT LOGGED IN
# This now uses Supabase session recovery automatically
# ============================================================================
check_authentication()

# ============================================================================
# PROACTIVE SESSION PERSISTENCE
# ============================================================================
# If authenticated but "session" is missing from URL, push it.
# This prevents logout if the user refreshes or lands on a URL without the param.
if st.session_state.get("authenticated") and "session" not in st.query_params:
    session_cookie = st.session_state.get("session_cookie")
    if session_cookie:
        from auth import update_query_params
        update_query_params(st.query_params.to_dict())

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
    user_id = st.session_state["user_id"]
    db.set_user(user_id)
    
    # IDENTIFY: Link session to user once
    if not st.session_state.get("_analytics_identified"):
        Analytics().identify(
            user_id=user_id,
            email=st.session_state.get("email"),
            name=st.session_state.get("full_name")
        )
        st.session_state["_analytics_identified"] = True

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

# Track page visit
Analytics().track_page_visit(view)

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    # Handle logout action triggered from the footer HTML button
    if st.query_params.get("action") == "logout":
        logout()

    # Robust sidebar styling with absolute positioned footer
    st.markdown("""
    <style>
    /* Force sidebar to use relative positioning for absolute footer */
    [data-testid="stSidebar"] {
        position: relative;
    }
    
    /* Ensure sidebar content is scrollable with space for footer */
    section[data-testid="stSidebar"] > div {
        padding-bottom: 80px !important; /* Space for fixed footer */
    }
    
    /* Sidebar footer - absolutely positioned at bottom */
    .sidebar-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 250px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        background: #1E1E1E;
        z-index: 999;
        box-sizing: border-box;
    }
    
    /* Adjust for expanded sidebar */
    [data-testid="stSidebar"][aria-expanded="true"] .sidebar-footer {
        width: 250px;
    }
    
    .sidebar-footer-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .sidebar-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #4B9EFF, #2D7DD2);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 14px;
        flex-shrink: 0;
    }
    
    .sidebar-user-info {
        flex: 1;
        min-width: 0;
    }
    
    .sidebar-user-email {
        color: #FFFFFF;
        font-size: 13px;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Modern navigation with pill-shaped active state */
    .modern-nav {
        padding: 8px 12px;
    }
    
    .modern-nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0 12px;
        min-height: 38px;
        margin: 4px 0;
        border-radius: 8px;
        color: #FFFFFF !important;
        text-decoration: none !important;
        font-size: 14px;
        font-weight: 400;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .modern-nav-item:hover {
        background: rgba(255, 255, 255, 0.07);
        color: #FFFFFF !important;
        text-decoration: none !important;
    }
    
    .modern-nav-item.active {
        background: #252930;
        color: #FFFFFF !important;
        font-weight: 500;
        text-decoration: none !important;
    }
    
    .modern-nav-item span {
        color: #FFFFFF !important;
    }
    
    .modern-nav-item svg {
        flex-shrink: 0;
        opacity: 0.9;
    }
    
    .tier-tag {
        display: inline-block;
        margin-left: auto;
        padding: 2px 8px;
        background: rgba(74, 222, 128, 0.15);
        color: #4ADE80;
        font-size: 10px;
        font-weight: 600;
        border-radius: 4px;
        text-transform: uppercase;
    }
    
    /* Slimmer buttons */
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] .stButton > button {
        min-height: 32px !important;
        padding: 6px 12px !important;
        font-size: 13px !important;
    }
    </style>
    """, unsafe_allow_html=True)


    
    # Logo
    try:
        import base64
        import os
        logo_path = "assets/sidebar_logo.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin: 12px 0;">
                    <img src="data:image/png;base64,{data}" style="width: 80%; height: auto; border: none; background: transparent;">
                </div>
                """,
                unsafe_allow_html=True
            )
    except Exception:
        pass

    # New Matter Button
    if st.button("New Matter", key="sidebar_new_matter", use_container_width=True, type="primary"):
        st.session_state["show_new_matter"] = True
        st.session_state["show_search_modal"] = False
        st.session_state["show_edit_matter"] = False
        st.session_state["modal_mode"] = "new_matter"
        st.session_state["existing_matter_id"] = None
        st.rerun()


    # Search Button (Modal-based)
    st.markdown('<div style="margin: 0 16px 16px 16px;">', unsafe_allow_html=True)
    
    # Initialize search modal state
    if "show_search_modal" not in st.session_state:
        st.session_state["show_search_modal"] = False
    
    # Get current view for search context
    view = get_view()
    
    # Search button that opens modal
    if st.button(
        f"Search {'clauses' if view=='clause_library' else 'matters'}",
        key="search_trigger_btn",
        use_container_width=True,
        type="secondary"
    ):
        st.session_state["show_search_modal"] = True
        st.session_state["show_new_matter"] = False
        st.session_state["show_edit_matter"] = False
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Get session param helper
    def get_session_param():
        """Get session parameter for URLs."""
        session_cookie = st.session_state.get("session_cookie", "")
        if session_cookie:
            return f"&session={session_cookie}"
        return ""

    session_param = get_session_param()
    
    # Get subscription info for tier tag
    user_id = st.session_state.get("user_id")
    tier_display = ""
    if user_id:
        status = subscription_mgr.get_user_status(user_id)
        tier = status.get("tier", "trial")
        documents_remaining = status.get("documents_remaining")
        
        # Determine tier display
        if tier == "enterprise":
            tier_display = '<span class="tier-tag">Unlimited</span>'
        elif tier == "team":
            tier_display = '<span class="tier-tag">Team</span>'
        elif tier == "individual":
            tier_display = f'<span class="tier-tag">{documents_remaining or 0} docs</span>'
        elif tier == "trial":
            tier_display = '<span class="tier-tag" style="background: rgba(245, 158, 11, 0.15); color: #F59E0B;">Trial</span>'
    
    # Modern Navigation with icons
    st.markdown(f"""
    <div class="modern-nav">
        <a class="modern-nav-item {'active' if view in ['matters', 'matter_details'] else ''}" href="?view=matters{session_param}" target="_self">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="color:#fff">
                <path d="M2.50047 13H8.50047M15.5005 13H21.5005M12.0005 7V21M12.0005 7C13.3812 7 14.5005 5.88071 14.5005 4.5M12.0005 7C10.6198 7 9.50047 5.88071 9.50047 4.5M4.00047 21L20.0005 21M4.00047 4.50001L9.50047 4.5M9.50047 4.5C9.50047 3.11929 10.6198 2 12.0005 2C13.3812 2 14.5005 3.11929 14.5005 4.5M14.5005 4.5L20.0005 4.5M8.88091 14.3364C8.48022 15.8706 7.11858 17 5.50047 17C3.88237 17 2.52073 15.8706 2.12004 14.3364C2.0873 14.211 2.07093 14.1483 2.06935 13.8979C2.06838 13.7443 2.12544 13.3904 2.17459 13.2449C2.25478 13.0076 2.34158 12.8737 2.51519 12.6059L5.50047 8L8.48576 12.6059C8.65937 12.8737 8.74617 13.0076 8.82636 13.2449C8.87551 13.3904 8.93257 13.7443 8.9316 13.8979C8.93002 14.1483 8.91365 14.211 8.88091 14.3364ZM21.8809 14.3364C21.4802 15.8706 20.1186 17 18.5005 17C16.8824 17 15.5207 15.8706 15.12 14.3364C15.0873 14.211 15.0709 14.1483 15.0693 13.8979C15.0684 13.7443 15.1254 13.3904 15.1746 13.2449C15.2548 13.0076 15.3416 12.8737 15.5152 12.6059L18.5005 8L21.4858 12.6059C21.6594 12.8737 21.7462 13.0076 21.8264 13.2449C21.8755 13.3904 21.9326 13.7443 21.9316 13.8979C21.93 14.1483 21.9137 14.211 21.8809 14.3364Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Matters</span>
        </a>
        <a class="modern-nav-item {'active' if view == 'clause_library' else ''}" href="?view=clause_library{session_param}" target="_self">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="color:#fff">
                <path d="M2 12.0001L11.6422 16.8212C11.7734 16.8868 11.839 16.9196 11.9078 16.9325C11.9687 16.9439 12.0313 16.9439 12.0922 16.9325C12.161 16.9196 12.2266 16.8868 12.3578 16.8212L22 12.0001M2 17.0001L11.6422 21.8212C11.7734 21.8868 11.839 21.9196 11.9078 21.9325C11.9687 21.9439 12.0313 21.9439 12.0922 21.9325C12.161 21.9196 12.2266 21.8868 12.3578 21.8212L22 17.0001M2 7.00006L11.6422 2.17895C11.7734 2.11336 11.839 2.08056 11.9078 2.06766C11.9687 2.05622 12.0313 2.05622 12.0922 2.06766C12.161 2.08056 12.2266 2.11336 12.3578 2.17895L22 7.00006L12.3578 11.8212C12.2266 11.8868 12.161 11.9196 12.0922 11.9325C12.0313 11.9439 11.9687 11.9439 11.9078 11.9325C11.839 11.9196 11.7734 11.8868 11.6422 11.8212L2 7.00006Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Clause Library</span>
        </a>
        <a class="modern-nav-item {'active' if view == 'organization' else ''}" href="?view=organization{session_param}" target="_self">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="color:#fff">
                <path d="M7.5 11H4.6C4.03995 11 3.75992 11 3.54601 11.109C3.35785 11.2049 3.20487 11.3578 3.10899 11.546C3 11.7599 3 12.0399 3 12.6V21M16.5 11H19.4C19.9601 11 20.2401 11 20.454 11.109C20.6422 11.2049 20.7951 11.3578 20.891 11.546C21 11.7599 21 12.0399 21 12.6V21M16.5 21V6.2C16.5 5.0799 16.5 4.51984 16.282 4.09202C16.0903 3.71569 15.7843 3.40973 15.408 3.21799C14.9802 3 14.4201 3 13.3 3H10.7C9.57989 3 9.01984 3 8.59202 3.21799C8.21569 3.40973 7.90973 3.71569 7.71799 4.09202C7.5 4.51984 7.5 5.0799 7.5 6.2V21M22 21H2M11 7H13M11 11H13M11 15H13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Organization</span>
            {tier_display}
        </a>
        <a class="modern-nav-item {'active' if view == 'pricing' else ''}" href="?view=pricing{session_param}" target="_self">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="color:#fff">
                <path d="M22 8.5H2M2 12.5H5.54668C6.08687 12.5 6.35696 12.5 6.61813 12.5466C6.84995 12.5879 7.0761 12.6563 7.29191 12.7506C7.53504 12.8567 7.75977 13.0065 8.20924 13.3062L8.79076 13.6938C9.24023 13.9935 9.46496 14.1433 9.70809 14.2494C9.9239 14.3437 10.15 14.4121 10.3819 14.4534C10.643 14.5 10.9131 14.5 11.4533 14.5H12.5467C13.0869 14.5 13.357 14.5 13.6181 14.4534C13.85 14.4121 14.0761 14.3437 14.2919 14.2494C14.535 14.1433 14.7598 13.9935 15.2092 13.6938L15.7908 13.3062C16.2402 13.0065 16.465 12.8567 16.7081 12.7506C16.9239 12.6563 17.15 12.5879 17.3819 12.5466C17.643 12.5 17.9131 12.5 18.4533 12.5H22M2 7.2L2 16.8C2 17.9201 2 18.4802 2.21799 18.908C2.40973 19.2843 2.71569 19.5903 3.09202 19.782C3.51984 20 4.07989 20 5.2 20L18.8 20C19.9201 20 20.4802 20 20.908 19.782C21.2843 19.5903 21.5903 19.2843 21.782 18.908C22 18.4802 22 17.9201 22 16.8V7.2C22 6.0799 22 5.51984 21.782 5.09202C21.5903 4.7157 21.2843 4.40974 20.908 4.21799C20.4802 4 19.9201 4 18.8 4L5.2 4C4.0799 4 3.51984 4 3.09202 4.21799C2.7157 4.40973 2.40973 4.71569 2.21799 5.09202C2 5.51984 2 6.07989 2 7.2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Pricing</span>
        </a>
    </div>
    """, unsafe_allow_html=True)
    

    # Pinned Footer (no help icon, outside scrollable content)
    user_email = st.session_state.get("user_email", "User")
    user_initials = "".join([word[0].upper() for word in user_email.split("@")[0].split(".")[:2]])
    
    st.markdown(f"""
    <!-- Logout button: fixed just above the avatar footer -->
    <div style="
        position: fixed;
        bottom: 65px;
        left: 0;
        width: 250px;
        padding: 0 16px 8px 16px;
        box-sizing: border-box;
        z-index: 999;
    ">
        <a href="?action=logout{session_param}" target="_self" style="
            display: block;
            text-align: center;
            padding: 8px 0;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: #9CA3AF;
            font-size: 13px;
            font-weight: 500;
            text-decoration: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            transition: background 0.2s, color 0.2s;
        " onmouseover="this.style.background='rgba(255,255,255,0.12)';this.style.color='#FFFFFF';"
           onmouseout="this.style.background='rgba(255,255,255,0.06)';this.style.color='#9CA3AF';"
        >Logout</a>
    </div>

    <!-- Avatar footer: pinned at the very bottom -->
    <div class="sidebar-footer" style="padding: 10px 16px;">
        <div class="sidebar-footer-content">
            <div class="sidebar-avatar">{user_initials}</div>
            <div class="sidebar-user-info">
                <div class="sidebar-user-email">{user_email}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)




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
            
            # --- Expanded Filter Categories ---
            STATUS_OPTIONS = ["all", "active", "review", "completed", "archived", "on_hold", "pending"]
            
            # Pre-defined Matter Types (Legal Practice Areas)
            PREDEFINED_TYPES = [
                "Corporate", "Real Estate", "Employment", "Litigation", 
                "Intellectual Property", "Family Law", "Probate & Estate", 
                "Commercial", "Banking & Finance", "Tax", "Immigration", 
                "Criminal", "Insurance", "Environmental", "General"
            ]
            
            # Pre-defined Jurisdictions
            PREDEFINED_JURISDICTIONS = [
                "Kenya", "Uganda", "Tanzania", "Rwanda", "United Kingdom", 
                "United States", "South Africa", "Nigeria", "United Arab Emirates", 
                "Global", "Other"
            ]
            # ----------------------------------

            # Get all matters to extract unique values (limit to 100 to get a good sample)
            all_matters = db.get_matters(limit=100)
            
            # Extract unique matter types and jurisdictions from DB
            db_matter_types = [m.get("matter_type", "General") for m in all_matters]
            db_jurisdictions = [m["jurisdiction"] for m in all_matters]
            
            # Merge and deduplicate
            matter_types = sorted(list(set(PREDEFINED_TYPES + db_matter_types)))
            jurisdictions = sorted(list(set(PREDEFINED_JURISDICTIONS + db_jurisdictions)))
            
            # Status filter
            current_status = st.session_state.get("filter_status", "all")
            status_index = STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0
            
            status_filter = st.selectbox(
                "Status",
                options=STATUS_OPTIONS,
                index=status_index,
                key="status_select"
            )
            
            # Matter type filter
            matter_type_options = ["all"] + matter_types
            current_type = st.session_state.get("filter_matter_type", "all")
            type_index = matter_type_options.index(current_type) if current_type in matter_type_options else 0
            
            matter_type_filter = st.selectbox(
                "Matter Type",
                options=matter_type_options,
                index=type_index,
                key="matter_type_select"
            )
            
            # Jurisdiction filter
            jurisdiction_options = ["all"] + jurisdictions
            current_jurisdiction = st.session_state.get("filter_jurisdiction", "all")
            juris_index = jurisdiction_options.index(current_jurisdiction) if current_jurisdiction in jurisdiction_options else 0
            
            jurisdiction_filter = st.selectbox(
                "Jurisdiction",
                options=jurisdiction_options,
                index=juris_index,
                key="jurisdiction_select"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Apply", use_container_width=True, type="primary"):
                    st.session_state["filter_status"] = status_filter
                    st.session_state["filter_matter_type"] = matter_type_filter
                    st.session_state["filter_jurisdiction"] = jurisdiction_filter
                    update_query_params(st.query_params.to_dict())
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
            <span class="sc-meta-dot">&bull;</span>
            <span>{m["jurisdiction"]}</span>
            <span class="sc-meta-dot">&bull;</span>
            <span>{draft_count} draft{'s' if draft_count != 1 else ''}</span>
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
    """Helper to show relative time"""
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
elif view == "privacy":
    render_privacy_policy()
elif view == "terms":
    render_terms_of_use()
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
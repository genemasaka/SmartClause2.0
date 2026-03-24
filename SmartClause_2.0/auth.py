# auth.py - TRULY PERSISTENT SESSION (COOKIE-BASED)
import streamlit as st
from error_helpers import show_error
from supabase import create_client
import os
import logging
from dotenv import load_dotenv

import hashlib
import hmac
from analytics import Analytics
from email_service import EmailService

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Analytics
def get_analytics():
    return Analytics()

# Secret key for session cookies (change this to a random secret in production)
SESSION_SECRET = os.getenv("SESSION_SECRET", "your-secret-key-change-in-production")


def get_supabase_client():
    """Get Supabase client with robust URL validation."""
    # Fetch and strip whitespace (fixes common copy-paste errors)
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL is missing from .env file")
        
    if not supabase_key:
        raise ValueError("SUPABASE_ANON_KEY is missing from .env file")
    
    # Auto-correct missing protocol
    if not supabase_url.startswith("https://") and not supabase_url.startswith("http://"):
        supabase_url = f"https://{supabase_url}"
        
    # Validation to prevent cryptic DNS errors
    if "your-project" in supabase_url or "supabase.co" not in supabase_url:
        # Check if it's a valid custom domain or standard supabase URL
        if "." not in supabase_url:
             raise ValueError(f"Invalid SUPABASE_URL: '{supabase_url}'. It looks like a placeholder.")

    return create_client(supabase_url, supabase_key)


def get_supabase_admin_client():
    """Get Supabase client with SERVICE_ROLE key for admin tasks."""
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    
    if not supabase_url or not supabase_service_key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY is missing from .env file")
        
    return create_client(supabase_url, supabase_service_key)


def create_session_cookie(user_id: str, email: str, access_token: str, refresh_token: str):
    """Create a secure session cookie."""
    import json
    import base64
    
    session_data = {
        "user_id": user_id,
        "email": email,
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    
    # Convert to JSON and encode
    json_str = json.dumps(session_data)
    encoded = base64.b64encode(json_str.encode()).decode()
    
    # Create signature
    signature = hmac.new(
        SESSION_SECRET.encode(),
        encoded.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{encoded}.{signature}"


def verify_session_cookie(cookie_value: str) -> dict:
    """Verify and decode session cookie."""
    import json
    import base64
    
    try:
        # Split cookie into data and signature
        parts = cookie_value.split('.')
        if len(parts) != 2:
            return None
        
        encoded, signature = parts
        
        # Verify signature
        expected_signature = hmac.new(
            SESSION_SECRET.encode(),
            encoded.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        # Decode data
        json_str = base64.b64decode(encoded.encode()).decode()
        session_data = json.loads(json_str)
        
        return session_data
    except Exception:
        return None


def get_session_cookie():
    """Get session cookie from query params or browser storage."""
    # Try to get from query params first (for navigation)
    if "session" in st.query_params:
        return st.query_params["session"]
    
    # Try to get from session state (for same-page reruns)
    if "session_cookie" in st.session_state:
        return st.session_state["session_cookie"]
    
    return None


def save_session(user_id: str, email: str, access_token: str, refresh_token: str):
    """Save session persistently."""
    # Save to session state for immediate use
    st.session_state["authenticated"] = True
    st.session_state["user_id"] = user_id
    st.session_state["user_email"] = email
    st.session_state["access_token"] = access_token
    st.session_state["refresh_token"] = refresh_token
    
    # Create session cookie
    cookie = create_session_cookie(user_id, email, access_token, refresh_token)
    st.session_state["session_cookie"] = cookie
    
    # Add session to query params for persistence across navigation
    st.query_params["session"] = cookie
    
    # Preserving invite_token if it exists
    if "invite_token" in st.query_params:
        st.query_params["invite_token"] = st.query_params["invite_token"]
    elif "preserved_invite_token" in st.session_state:
        st.query_params["invite_token"] = st.session_state["preserved_invite_token"]


def restore_session_from_cookie() -> bool:
    """Restore session from cookie if it exists."""
    cookie = get_session_cookie()
    
    if not cookie:
        return False
    
    # Verify and decode cookie
    session_data = verify_session_cookie(cookie)
    
    if not session_data:
        return False
    
    try:
        # Verify session with Supabase
        supabase = get_supabase_client()
        response = supabase.auth.set_session(
            session_data["access_token"],
            session_data["refresh_token"]
        )
        
        if response and response.user:
            # Session is valid - restore to session state
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = session_data["user_id"]
            st.session_state["user_email"] = session_data["email"]
            st.session_state["access_token"] = session_data["access_token"]
            st.session_state["refresh_token"] = session_data["refresh_token"]
            st.session_state["session_cookie"] = cookie
            
            # Update tokens if refreshed
            if response.session:
                st.session_state["access_token"] = response.session.access_token
                st.session_state["refresh_token"] = response.session.refresh_token
                
                # Update cookie with new tokens
                new_cookie = create_session_cookie(
                    session_data["user_id"],
                    session_data["email"],
                    response.session.access_token,
                    response.session.refresh_token
                )
                st.session_state["session_cookie"] = new_cookie
                st.query_params["session"] = new_cookie
            
            return True
        
        return False
    
    except Exception as e:
        print(f"Session restore error: {e}")
        return False


def clear_session():
    """Clear all session data."""
    keys_to_clear = [
        "authenticated", 
        "user_id", 
        "user_email",
        "access_token",
        "refresh_token",
        "session_cookie",
        "show_new_matter",
        "new_matter_payload",
        "current_matter_id",
        "current_document_id",
        "editor_content",
        "generation_complete"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear all query params to prevent action triggers (like action=logout) from persisting
    for key in list(st.query_params.keys()):
        try:
            del st.query_params[key]
        except Exception:
            pass


def login_page():
    """Render login page with modern split-screen design."""
    # CRITICAL: Early exit if already authenticated - don't render anything
    if st.session_state.get("authenticated"):
        return
    
    # Initialize view state
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"

    # ── Recovery token handler (pure Python, no JS bridge needed) ────────────
    # The reset email contains ?sc_token=<token_hash>&sc_type=recovery
    # We verify the token_hash directly against Supabase's /auth/v1/verify endpoint
    # to get a real access_token + refresh_token, then store them for the reset form.
    sc_type  = st.query_params.get("sc_type", "")
    sc_token = st.query_params.get("sc_token", "")

    if sc_type == "recovery" and sc_token:
        if "reset_access_token" not in st.session_state:
            try:
                import httpx
                supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
                supabase_anon_key = (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
                verify_resp = httpx.post(
                    f"{supabase_url}/auth/v1/verify",
                    headers={
                        "apikey": supabase_anon_key,
                        "Content-Type": "application/json"
                    },
                    json={"token_hash": sc_token, "type": "recovery"},
                    timeout=10
                )
                verify_data = verify_resp.json()
                access_token  = verify_data.get("access_token")
                refresh_token = verify_data.get("refresh_token")
                if access_token:
                    st.session_state["reset_access_token"]  = access_token
                    st.session_state["reset_refresh_token"] = refresh_token or ""
                else:
                    error_msg = verify_data.get("error_description") or verify_data.get("msg") or "Invalid or expired reset link."
                    st.session_state["reset_token_error"] = error_msg
            except Exception as e:
                logger.error(f"Token verify error: {e}", exc_info=True)
                st.session_state["reset_token_error"] = "Could not verify reset link. Please request a new one."
        st.session_state["auth_view"] = "reset_password"

    elif sc_type == "signup" and sc_token:
        try:
            import httpx
            supabase_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
            supabase_anon_key = (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
            httpx.post(
                f"{supabase_url}/auth/v1/verify",
                headers={"apikey": supabase_anon_key, "Content-Type": "application/json"},
                json={"token_hash": sc_token, "type": "email"},
                timeout=10
            )
            st.success("✅ Email confirmed! You can now sign in.")
        except Exception:
            pass
        st.session_state["auth_view"] = "login"

    
    # Add custom CSS for the modern split-screen layout
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@700;800&display=swap');

        /* ── HIDE CHROME ───────────────────────────────────────────── */
        #MainMenu, header, footer { visibility: hidden; }
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] { display: none !important; }

        /* ── SIDEBAR: completely removed on auth page ───────────────── */
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important; min-width: 0 !important; max-width: 0 !important;
            margin: 0 !important; padding: 0 !important;
        }
        [data-testid="collapsedControl"] { display: none !important; }

        /* ── RESET LAYOUT ───────────────────────────────────────────── */
        body, .stApp, .appview-container,
        [data-testid="stAppViewContainer"] {
            margin: 0 !important; padding: 0 !important;
            width: 100vw !important; max-width: 100vw !important;
            background: transparent !important;
            overflow-x: hidden !important;
        }
        section.main, section[data-testid="stMain"],
        div.appview-container > section.main {
            margin-left: 0 !important;
            width: 100vw !important; max-width: 100vw !important;
        }
        .main {
            background: transparent !important;
            padding: 0 !important; margin: 0 !important;
        }
        .block-container {
            padding: 0 !important; margin: 0 !important;
            max-width: 100% !important; width: 100% !important;
        }

        /* ── SPLIT BACKGROUNDS ──────────────────────────────────────── */
        .auth-bg-left {
            position: fixed; top: 0; left: 0;
            width: 62vw; height: 100vh; z-index: 0;
            background: #1a6fd4 !important; /* Professional solid blue */
        }
        /* Subtle grid overlay for texture */
        .auth-bg-left::before {
            content: '';
            position: absolute; inset: 0;
            background-image:
                linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px);
            background-size: 48px 48px;
        }
        /* Soft orb accents */
        .auth-bg-left::after {
            content: '';
            position: absolute;
            width: 520px; height: 520px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.18) 0%, transparent 70%);
            bottom: -120px; left: -80px;
        }
        .auth-bg-right {
            position: fixed; top: 0; right: 0;
            width: 38vw; height: 100vh; z-index: 0;
            background: #000000;
        }

        /* ── COLUMN LAYOUT ──────────────────────────────────────────── */
        [data-testid="column"] {
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            height: 100vh !important;
            z-index: 1;
        }
        /* Left: brand panel — fills its flex share, scrollable if content overflows */
        [data-testid="column"]:nth-of-type(1) {
            align-items: flex-start !important;
            justify-content: flex-start !important;
            flex: 16 !important;
            overflow: hidden !important;
        }
        /* Propagate height through left column Streamlit wrappers */
        html body [data-testid="column"]:nth-of-type(1) > div,
        html body [data-testid="column"]:nth-of-type(1) [data-testid="stVerticalBlockBorderWrapper"],
        html body [data-testid="column"]:nth-of-type(1) [data-testid="stVerticalBlock"] {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
        }
        /* Right Column (Form Column) styling */
        [data-testid="column"]:nth-of-type(2) {
            padding-right: 0 !important;
            padding-left: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: stretch !important;
            justify-content: center !important;
            background: #000 !important;
        }

        /* FORM WRAPPER — viewport-relative padding to visually center form */
        .auth-form-wrapper {
            width: 100% !important;
            padding-top: calc(50vh - 210px) !important;
            display: flex !important;
            justify-content: center !important;
        }

        /* ── 60% WIDTH INNER FORM CONTAINER ────────────────────────────
           This div wraps all form content and constrains it to 60% of
           the right column. All Streamlit elements inside inherit this
           width via width:100% on their own containers.               */
        .auth-form-inner {
            width: 60% !important;
            min-width: 260px !important;
            max-width: 400px !important;
            flex-shrink: 0;
        }

        /* ── PROPAGATE HEIGHT THROUGH STREAMLIT'S INTERNAL WRAPPERS ─────
           The right column has height:100vh and justify-content:center,
           but Streamlit's stVerticalBlockBorderWrapper and stVerticalBlock
           are height:auto by default, so centering has no effect.
           Force height:100% + flex all the way down the chain.          */
        html body [data-testid="column"]:nth-of-type(2) > div,
        html body [data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlockBorderWrapper"],
        html body [data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlock"] {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
        }

        /* Force all form elements inside .auth-form-inner to fill their container */
        .auth-form-inner .stTextInput,
        .auth-form-inner .stButton,
        .auth-form-inner div[data-testid="stForm"],
        .auth-form-inner div[data-testid="stFormSubmitButton"],
        .auth-form-inner div[data-testid="stButton"],
        .auth-form-inner .auth-title,
        .auth-form-inner .auth-subtitle,
        .auth-form-inner .auth-toggle,
        .auth-form-inner .auth-privacy-notice {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        /* Inputs inside the 60% container fill full width */
        .auth-form-inner .stTextInput > div,
        .auth-form-inner .stTextInput input {
            width: 100% !important;
            box-sizing: border-box !important;
        }

        /* Buttons inside the 60% container fill full width */
        .auth-form-inner div[data-testid="stFormSubmitButton"] > button,
        .auth-form-inner div[data-testid="stButton"] > button {
            width: 100% !important;
            box-sizing: border-box !important;
        }

        /* Completely strip Streamlit's form container to match button widths */
        div[data-testid="stForm"], 
        div[data-testid="stForm"] > div,
        [data-testid="stForm"] [data-testid="stVerticalBlock"] {
            padding: 0 !important;
            margin: 0 !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        /* ── BRAND PANEL ────────────────────────────────────────────── */
        .auth-brand-panel {
            padding: 48px 64px 40px 64px;
            max-width: 58vw !important;
            animation: fadeSlideUp 0.7s ease both;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            height: 100%;
            box-sizing: border-box;
            overflow-y: auto;
            overflow-x: hidden;
            scrollbar-width: none; /* Firefox */
        }
        .auth-brand-panel::-webkit-scrollbar { display: none; } /* Chrome/Safari */
        .auth-brand-logo {
            margin-bottom: 40px;
        }
        .auth-brand-logo img {
            width: 180px; height: auto; display: block;
            filter: drop-shadow(0 2px 16px rgba(0,0,0,0.18));
        }
        .auth-brand-logo-fallback {
            font-size: 22px; font-weight: 800;
            color: #fff; margin-bottom: 20px; letter-spacing: -0.02em;
        }
        .auth-brand-headline {
            font-family: 'Hanken Grotesk', sans-serif !important;
            font-size: clamp(48px, 6vw, 84px);
            font-weight: 800; line-height: 0.95;
            color: #ffffff;
            letter-spacing: -0.02em;
            margin-bottom: 16px;
            max-width: 800px;
            text-shadow: 0 2px 20px rgba(0,0,0,0.12);
        }
        .auth-brand-headline em {
            font-style: normal;
            background: linear-gradient(90deg, #ffffff 0%, rgba(255,255,255,0.75) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .auth-brand-sub {
            font-size: 16px; line-height: 1.6;
            color: rgba(255,255,255,0.85);
            margin-bottom: 20px;
            max-width: 650px;
        }
        /* Feature items */
        .auth-features {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 0;
        }
        .auth-feature-item {
            display: flex;
            align-items: center;
            gap: 12px;
            color: rgba(255,255,255,0.88);
            font-size: 14px;
            font-weight: 500;
        }
        .auth-feature-icon {
            width: 24px; height: 24px;
            display: flex; align-items: center; justify-content: center;
            flex-shrink: 0;
            color: rgba(255,255,255,0.95);
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        /* Dual Testimonials Grid — adjacent layout within column */
        .auth-testimonials-grid {
            margin-top: 20px;
            margin-bottom: 40px;
            display: flex;
            gap: 14px;
            flex-direction: row;
            flex-wrap: wrap;
            width: 100%;
            justify-content: flex-start;
            align-items: stretch;
        }
        /* Testimonial card */
        .auth-testimonial {
            flex: 1; /* Equal width cards */
            min-width: 280px; /* Prevent too much squishing */
            max-width: 48%; /* Keep within half column width roughly */
            padding: 24px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 16px;
            backdrop-filter: blur(12px);
            transition: transform 0.3s ease;
            
        }
        .auth-testimonial:hover {
            transform: translateY(-4px);
            background: rgba(255,255,255,0.14);
        }
        .auth-testimonial-quote {
            font-size: 14px; line-height: 1.6;
            color: rgba(255,255,255,0.9);
            font-style: italic; margin-bottom: 12px;
        }
        .auth-testimonial-author {
            display: flex; align-items: center; gap: 10px;
        }
        .auth-testimonial-avatar {
            width: 30px; height: 30px; border-radius: 50%;
            background: rgba(255,255,255,0.25);
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 700; color: white;
        }
        .auth-testimonial-name {
            font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.95);
        }
        .auth-testimonial-role {
            font-size: 12px; color: rgba(255,255,255,0.6);
        }

        /* ── AUTH FORM (RIGHT PANEL) ────────────────────────────────── */
        .auth-logo {
            width: 52px; height: 52px; border-radius: 12px;
            background: linear-gradient(135deg, #4B9EFF 0%, #3B7DD1 100%);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 22px; font-weight: 700;
            margin-bottom: 28px;
            box-shadow: 0 4px 16px rgba(75,158,255,0.35);
        }
        .auth-title {
            font-size: 28px; font-weight: 700;
            color: #FFFFFF !important; margin-bottom: 6px; letter-spacing: -0.01em;
        }
        .auth-subtitle {
            font-size: 14px; color: #6B7280 !important;
            margin-bottom: 28px; line-height: 1.55;
        }

        /* Inputs */
        .stTextInput label { color: #9CA3AF !important; font-size: 13px !important; font-weight: 500 !important; }
        .stTextInput input {
            background-color: #111317 !important;
            color: #FFFFFF !important;
            border: 1px solid #252930 !important;
            border-radius: 8px !important;
            font-size: 14px !important;
        }
        .stTextInput input:focus { border-color: #4B9EFF !important; }
        .stTextInput > div > div:focus-within {
            border-color: #4B9EFF !important;
            box-shadow: 0 0 0 3px rgba(75,158,255,0.12) !important;
        }

        /* Buttons */
        div[data-testid="stFormSubmitButton"],
        div[data-testid="stButton"] {
            display: flex !important;
            justify-content: center !important;
        }
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stButton"] > button {
            background: #4B9EFF !important;
            border: none !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 7px 20px !important;
            font-size: 13px !important; font-weight: 600 !important;
            width: 100% !important;
            min-height: unset !important;
            line-height: 1.4 !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stButton"] > button:hover {
            background: #5BABFF !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(75,158,255,0.28) !important;
        }

        /* Forgot password — match Sign In button width/style */
        .forgot-password-btn {
            width: 100% !important;
        }
        .forgot-password-btn > button {
            background: #4B9EFF !important;
            border: none !important;
            color: #fff !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            padding: 7px 20px !important;
            box-shadow: none !important;
            width: 100% !important;
            min-height: unset !important;
            line-height: 1.4 !important;
            border-radius: 8px !important;
            text-decoration: none !important;
            transition: all 0.2s ease !important;
        }
        .forgot-password-btn > button:hover {
            background: #5BABFF !important;
            box-shadow: 0 4px 12px rgba(75,158,255,0.28) !important;
            transform: translateY(-1px) !important;
            text-decoration: none !important;
        }

        /* Toggle / switch-view text */
        .auth-toggle {
            font-size: 13px; color: #4B5563 !important;
            text-align: center; margin-top: 4px;
        }

        /* Privacy notice */
        .auth-privacy-notice {
            text-align: center; font-size: 11px;
            color: #374151; margin-top: 20px; line-height: 1.6;
        }
        .auth-privacy-notice a { color: #4B9EFF; text-decoration: none; }
        .auth-privacy-notice a:hover { text-decoration: underline; }

        /* ── DEAD-ZONE FIX ──────────────────────────────────────────────
           Streamlit wraps columns in stHorizontalBlock → stMainBlockContainer
           → stMain, each carrying hidden padding. Zero every layer, then
           pin the row to the raw viewport edge with position:fixed.        */

        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100vw !important;
            width: 100vw !important;
        }

        [data-testid="stHorizontalBlock"] {
            position: fixed !important;
            top: 0 !important; left: 0 !important;
            width: 100vw !important; height: 100vh !important;
            padding: 0 !important; margin: 0 !important; gap: 0 !important;
            display: flex !important; align-items: stretch !important;
        }

        [data-testid="column"] {
            padding: 0 !important; margin: 0 !important;
        }

        /* ── ANIMATIONS ─────────────────────────────────────────────── */
        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(24px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.3; }
        }

        /* ── MOBILE AUTH LOGO ──────────────────────────────────────── */
        /* Hidden on desktop (logo appears in left brand panel) */
        .auth-mobile-logo {
            display: none;
        }
        /* Show logo centered above form on mobile */
        @media (max-width: 991px) {
            .auth-mobile-logo {
                display: flex !important;
                justify-content: center !important;
                width: 100% !important;
                margin-bottom: 28px !important;
            }
            .auth-mobile-logo img {
                width: 150px !important;
                height: auto !important;
            }
        }

        /* ── RESPONSIVE OVERRIDES (MOBILE) ─────────────────────────── */
        @media (max-width: 991px) {
            /* Hide the blueprint brand section entirely on mobile to keep it clean */
            .auth-bg-left, .auth-brand-panel {
                display: none !important;
            }
            .auth-bg-right {
                position: fixed !important;
                top: 0; left: 0;
                width: 100vw !important;
                height: 100vh !important;
                background: #000000 !important;
            }

            [data-testid="stHorizontalBlock"] {
                position: relative !important;
                display: block !important;
                width: 100vw !important;
                height: 100vh !important;
                overflow-y: auto !important;
            }

            [data-testid="column"] {
                width: 100% !important;
                min-width: 100% !important;
                height: auto !important;
                min-height: 100vh !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }

            /* Hide the first column (blueprint) on mobile */
            [data-testid="column"]:nth-of-type(1) {
                display: none !important;
            }

            /* Make the form column fill the screen */
            [data-testid="column"]:nth-of-type(2) {
                background: transparent !important;
                padding: 24px !important;
            }

            .auth-form-wrapper {
                padding-top: 0 !important;
                height: auto !important;
            }
            .auth-form-inner {
                width: 90% !important;
                max-width: 360px !important;
            }
        }
    </style>

    <!-- JS: force right column internals to flex-center vertically -->
    <script>
    (function centerAuthForm() {
        function applyCenter() {
            var cols = document.querySelectorAll('[data-testid="column"]');
            if (cols.length < 2) return;
            var rightCol = cols[cols.length - 1];
            // Walk every div child and make them stretch to full height
            var wrappers = rightCol.querySelectorAll(
                '[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stVerticalBlock"]'
            );
            wrappers.forEach(function(el) {
                el.style.setProperty('height', '100%', 'important');
                el.style.setProperty('display', 'flex', 'important');
                el.style.setProperty('flex-direction', 'column', 'important');
                el.style.setProperty('justify-content', 'center', 'important');
            });
            // Also apply to the direct div child of the right column
            var directChild = rightCol.firstElementChild;
            if (directChild) {
                directChild.style.setProperty('height', '100%', 'important');
                directChild.style.setProperty('display', 'flex', 'important');
                directChild.style.setProperty('flex-direction', 'column', 'important');
                directChild.style.setProperty('justify-content', 'center', 'important');
            }
        }
        // Run immediately and after Streamlit re-renders
        applyCenter();
        document.addEventListener('DOMContentLoaded', applyCenter);
        window.addEventListener('load', applyCenter);
        // Poll briefly to catch Streamlit lazy renders
        var tries = 0;
        var iv = setInterval(function() {
            applyCenter();
            tries++;
            if (tries > 20) clearInterval(iv);
        }, 200);
        // Also watch for DOM mutations (Streamlit re-renders)
        if (window.MutationObserver) {
            var mo = new MutationObserver(function() { applyCenter(); });
            mo.observe(document.body, { childList: true, subtree: true });
        }
    })();
    </script>

    <!-- FIXED SPLIT BACKGROUNDS -->
    <div class="auth-bg-left"></div>
    <div class="auth-bg-right"></div>
    """, unsafe_allow_html=True)
    
    # Use columns for side-by-side layout
    # Col 1: Brand (16)
    # Col 2: Form (9)
    with st.container():
        left_col, right_col = st.columns([16, 9], gap="small")
    
    # Left column - Brand content
    with left_col:
        # Load logo for brand panel
        try:
            import base64 as _b64l
            import os as _osl
            _lp = "assets/sidebar_logo.png"
            if _osl.path.exists(_lp):
                with open(_lp, "rb") as _lf:
                    _ld = _b64l.b64encode(_lf.read()).decode("utf-8")
                _logo_html = f'<div class="auth-brand-logo"><img src="data:image/png;base64,{_ld}" alt="SmartClause"></div>'
            else:
                _logo_html = '<div class="auth-brand-logo-fallback">SmartClause</div>'
        except Exception:
            _logo_html = '<div class="auth-brand-logo-fallback">SmartClause</div>'

        st.markdown(f"""
        <div class="auth-brand-panel">
            {_logo_html}
            <div class="auth-brand-headline">
                Draft smarter.<br><em>Close faster.</em>
            </div>
            <div class="auth-brand-sub">
                From complex commercial agreements to affidavits — SmartClause helps legal teams draft with speed, precision, and confidence.
            </div>
            <div class="auth-features">
                <div class="auth-feature-item">
                    <div class="auth-feature-icon">
                        <svg width="100%" height="100%" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 17.5H3.5M6.5 12H2M9 6.5H4M17 3L10.4036 12.235C10.1116 12.6438 9.96562 12.8481 9.97194 13.0185C9.97744 13.1669 10.0486 13.3051 10.1661 13.3958C10.3011 13.5 10.5522 13.5 11.0546 13.5H16L15 21L21.5964 11.765C21.8884 11.3562 22.0344 11.1519 22.0281 10.9815C22.0226 10.8331 21.9514 10.6949 21.8339 10.6042C21.6989 10.5 21.4478 10.5 20.9454 10.5H16L17 3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <div class="auth-feature-text">Generate complete documents in seconds</div>
                </div>
                <div class="auth-feature-item">
                    <div class="auth-feature-icon">
                        <svg width="100%" height="100%" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M2 12.0001L11.6422 16.8212C11.7734 16.8868 11.839 16.9196 11.9078 16.9325C11.9687 16.9439 12.0313 16.9439 12.0922 16.9325C12.161 16.9196 12.2266 16.8868 12.3578 16.8212L22 12.0001M2 17.0001L11.6422 21.8212C11.7734 21.8868 11.839 21.9196 11.9078 21.9325C11.9687 21.9439 12.0313 21.9439 12.0922 21.9325C12.161 21.9196 12.2266 21.8868 12.3578 21.8212L22 17.0001M2 7.00006L11.6422 2.17895C11.7734 2.11336 11.839 2.08056 11.9078 2.06766C11.9687 2.05622 12.0313 2.05622 12.0922 2.06766C12.161 2.08056 12.2266 2.11336 12.3578 2.17895L22 7.00006L12.3578 11.8212C12.2266 11.8868 12.161 11.9196 12.0922 11.9325C12.0313 11.9439 11.9687 11.9439 11.9078 11.9325C11.839 11.9196 11.7734 11.8868 11.6422 11.8212L2 7.00006Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <div class="auth-feature-text">Clause library built for legal professionals</div>
                </div>
                <div class="auth-feature-item">
                    <div class="auth-feature-icon">
                        <svg width="100%" height="100%" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17 11V8C17 5.23858 14.7614 3 12 3C9.23858 3 7 5.23858 7 8V11M8.8 21H15.2C16.8802 21 17.7202 21 18.362 20.673C18.9265 20.3854 19.3854 19.9265 19.673 19.362C20 18.7202 20 17.8802 20 16.2V15.8C20 14.1198 20 13.2798 19.673 12.638C19.3854 12.0735 18.9265 11.6146 18.362 11.327C17.7202 11 16.8802 11 15.2 11H8.8C7.11984 11 6.27976 11 5.63803 11.327C5.07354 11.6146 4.6146 12.0735 4.32698 12.638C4 13.2798 4 14.1198 4 15.8V16.2C4 17.8802 4 18.7202 4.32698 19.362C4.6146 19.9265 5.07354 20.3854 5.63803 20.673C6.27976 21 7.11984 21 8.8 21Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <div class="auth-feature-text">Secure, compliant document management</div>
                </div>
            </div>
            <div class="auth-testimonials-grid">
                <div class="auth-testimonial">
                    <div class="auth-testimonial-quote">
                        "SmartClause cut our contract drafting time in half. It's become indispensable for our entire legal team."
                    </div>
                    <div class="auth-testimonial-author">
                        <div class="auth-testimonial-avatar">SR</div>
                        <div>
                            <div class="auth-testimonial-name">Sarah R.</div>
                            <div class="auth-testimonial-role">General Counsel, Tech Co</div>
                        </div>
                    </div>
                </div>
                <div class="auth-testimonial">
                    <div class="auth-testimonial-quote">
                        "The clause library transformed how we manage templates. Security and speed are now at the heart of our workflow."
                    </div>
                    <div class="auth-testimonial-author">
                        <div class="auth-testimonial-avatar">MK</div>
                        <div>
                            <div class="auth-testimonial-name">Michael K.</div>
                            <div class="auth-testimonial-role">Partner, Legal Firm</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Right column - Form
    with right_col:
        # Build mobile logo HTML (shown above form on small screens via CSS)
        try:
            import base64 as _b64r
            import os as _osr
            _lp_r = "assets/sidebar_logo.png"
            if _osr.path.exists(_lp_r):
                with open(_lp_r, "rb") as _lf_r:
                    _ld_r = _b64r.b64encode(_lf_r.read()).decode("utf-8")
                _mobile_logo_html = f'<div class="auth-mobile-logo"><img src="data:image/png;base64,{_ld_r}" alt="SmartClause"></div>'
            else:
                _mobile_logo_html = '<div class="auth-mobile-logo" style="display:none;font-size:20px;font-weight:800;color:#fff;justify-content:center;margin-bottom:24px;">SmartClause</div>'
        except Exception:
            _mobile_logo_html = '<div class="auth-mobile-logo" style="display:none;font-size:20px;font-weight:800;color:#fff;justify-content:center;margin-bottom:24px;">SmartClause</div>'

        st.markdown(f'<div class="auth-form-wrapper">{_mobile_logo_html}<div class="auth-form-inner">', unsafe_allow_html=True)
        
        if st.session_state["auth_view"] == "login":
            st.markdown("""
            <div class="auth-title">Welcome</div>
            <div class="auth-subtitle">Sign in to SmartClause.</div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Your email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    else:
                        try:
                            supabase = get_supabase_client()
                            response = supabase.auth.sign_in_with_password({
                                "email": email,
                                "password": password
                            })
                            if response.user and response.session:
                                save_session(
                                    response.user.id, 
                                    response.user.email,
                                    response.session.access_token,
                                    response.session.refresh_token
                                )
                                st.session_state["authenticated"] = True
                                
                                # IDENTIFY: Link anonymous session to user
                                Analytics().identify(
                                    user_id=response.user.id,
                                    email=response.user.email
                                )
                                st.session_state["_analytics_identified"] = True
                                
                                Analytics().track_event("user_login_success", {"email": response.user.email})
                                
                                # ── INSTANT UI WIPE ──────────────────────────────────────
                                # Inject a full-screen overlay BEFORE st.rerun() so the
                                # auth form is visually hidden the instant the button fires.
                                # st.stop() then halts the rest of this script run so
                                # Streamlit never renders the sidebar or app content —
                                # the next clean run (via rerun) will show the main app.
                                st.markdown("""
                                    <style>
                                    [data-testid="stAppViewContainer"],
                                    [data-testid="stSidebar"],
                                    section.main, .block-container {
                                        visibility: hidden !important;
                                        opacity: 0 !important;
                                    }
                                    body::after {
                                        content: '';
                                        position: fixed;
                                        inset: 0;
                                        background: #000000;
                                        z-index: 2147483647;
                                    }
                                    </style>
                                """, unsafe_allow_html=True)
                                st.rerun()
                                st.stop()  # Halt this script run — next run will be the clean main app
                        except Exception as e:
                            Analytics().track_event("user_login_failure", {"email": email, "error": str(e)})
                            show_error(e, "login")
            
            if st.button("Forgot your password?", key="forgot_password_link", use_container_width=True):
                st.session_state["auth_view"] = "forgot_password"
                st.rerun()

            st.markdown('<div class="auth-toggle">Don\'t have an account?</div>', unsafe_allow_html=True)

            if st.button("Create new account", key="switch_to_signup", use_container_width=True):
                st.session_state["auth_view"] = "signup"
                st.rerun()

            st.markdown("""
            <div class="auth-privacy-notice">
                By signing in, you agree to our
                <a href="?view=terms" target="_self">Terms of Use</a> and
                <a href="?view=privacy" target="_self">Privacy Policy</a>.
            </div>
            """, unsafe_allow_html=True)

        elif st.session_state["auth_view"] == "forgot_password":
            st.markdown("""
            <div class="auth-title">Reset Password</div>
            <div class="auth-subtitle">Enter your account email to receive a reset link.</div>
            """, unsafe_allow_html=True)
            
            with st.form("forgot_password_form", clear_on_submit=False):
                reset_email = st.text_input("Your email", key="forgot_email")
                send_btn = st.form_submit_button("Send Reset Link", type="primary", use_container_width=True)
                if send_btn:
                    if reset_email:
                        try:
                            admin_client = get_supabase_admin_client()
                            app_url = os.getenv("APP_URL", "https://smartclause.net").rstrip("/")

                            res = admin_client.auth.admin.generate_link({
                                "type": "recovery",
                                "email": reset_email,
                                "options": {
                                    "redirect_to": f"{app_url}/"
                                }
                            })

                            # ── Extract the access token from the action_link ──────────
                            # generate_link returns a Supabase magic link whose hash contains
                            # access_token. We parse it server-side (Python has full access)
                            # and build a clean query-param URL to email the user directly.
                            # This avoids ALL JS bridge / iframe / hash complexity entirely.
                            action_link = None
                            if res:
                                if hasattr(res, 'properties') and res.properties:
                                    props = res.properties
                                    action_link = (
                                        getattr(props, 'action_link', None)
                                        or (props.get('action_link') if isinstance(props, dict) else None)
                                    )
                                if not action_link:
                                    action_link = getattr(res, 'action_link', None) or getattr(res, 'link', None)

                            if action_link:
                                # Parse the token out of the action_link (it's in the hash or as a param)
                                from urllib.parse import urlparse, parse_qs, urlencode
                                parsed = urlparse(action_link)

                                # Supabase puts token_hash + type as query params in generate_link responses
                                qs = parse_qs(parsed.query)
                                token_hash = (qs.get('token_hash') or qs.get('token') or [None])[0]
                                link_type  = (qs.get('type') or ['recovery'])[0]

                                if token_hash:
                                    # Build a direct, clean URL the user can click:
                                    # ?sc_token=<hash>&sc_type=recovery
                                    # Python reads these immediately — no JS needed.
                                    direct_params = urlencode({"sc_token": token_hash, "sc_type": link_type})
                                    direct_reset_url = f"{app_url}/?{direct_params}"
                                else:
                                    # Fallback: send the raw action_link if we can't extract the token
                                    direct_reset_url = action_link

                                email_service = EmailService()
                                email_service.send_password_reset(reset_email, direct_reset_url)
                                Analytics().track_event("password_reset_requested", {"email": reset_email})
                                st.success("✅ Reset link sent if email exists.")
                            else:
                                logger.error(f"Failed to generate reset link for {reset_email}: {res}")
                                st.error("Failed to generate reset link. Please contact support.")

                        except Exception as e:
                            logger.error(f"Error in password reset: {e}", exc_info=True)
                            Analytics().track_error(e, "password reset")
                            show_error(e, "password reset")
            
            if st.button("← Back to login", key="back_to_login_from_forgot", use_container_width=True):
                st.session_state["auth_view"] = "login"
                st.rerun()

        elif st.session_state["auth_view"] == "reset_password":
            st.markdown("""
            <div class="auth-title">New Password</div>
            <div class="auth-subtitle">Set a secure password for your account.</div>
            """, unsafe_allow_html=True)

            # Show error immediately if token verification failed on load
            if st.session_state.get("reset_token_error"):
                st.error(st.session_state["reset_token_error"])
                if st.button("← Request a new reset link", key="back_from_token_error", use_container_width=True):
                    st.session_state.pop("reset_token_error", None)
                    st.session_state.pop("reset_access_token", None)
                    st.session_state["auth_view"] = "forgot_password"
                    # Clear recovery params so the handler doesn't re-trigger on rerun
                    st.query_params.clear()
                    st.rerun()
            else:
                with st.form("reset_password_form", clear_on_submit=False):
                    new_password = st.text_input("New Password", type="password", key="new_password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                    submit = st.form_submit_button("Update Password", type="primary", use_container_width=True)
                    
                    if submit:
                        if not new_password or not confirm_password:
                            st.error("Please fill in both fields")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 8:
                            st.error("Password must be at least 8 characters")
                        else:
                            try:
                                access_token  = st.session_state.get("reset_access_token")
                                refresh_token = st.session_state.get("reset_refresh_token", "")
                                if not access_token:
                                    st.error("Reset session expired. Please request a new link.")
                                else:
                                    supabase = get_supabase_client()
                                    # access_token is a real JWT from /auth/v1/verify
                                    supabase.auth.set_session(access_token, refresh_token)
                                    supabase.auth.update_user({"password": new_password})

                                    st.success("✅ Password updated! Returning to login...")
                                    Analytics().track_event("password_reset_success")

                                    import time as _time
                                    _time.sleep(2)
                                    st.session_state["auth_view"] = "login"
                                    st.session_state.pop("reset_access_token", None)
                                    st.session_state.pop("reset_refresh_token", None)
                                    st.session_state.pop("reset_token_error", None)
                                    st.rerun()
                            except Exception as e:
                                logger.error(f"Error resetting password: {e}", exc_info=True)
                                show_error(e, "reset password")

            if st.button("← Back to login", key="back_to_login_from_reset", use_container_width=True):
                st.session_state["auth_view"] = "login"
                st.session_state.pop("reset_token_error", None)
                st.session_state.pop("reset_access_token", None)
                st.session_state.pop("reset_refresh_token", None)
                # Clear recovery params so the handler doesn't re-trigger on rerun
                st.query_params.clear()
                st.rerun()

        elif st.session_state["auth_view"] == "signup":
            st.markdown("""
            <div class="auth-title">Create account</div>
            <div class="auth-subtitle">Start drafting smarter today.</div>
            """, unsafe_allow_html=True)
            
            with st.form("signup_form", clear_on_submit=False):
                email = st.text_input("Work Email *", key="email_signup", placeholder="you@company.com")
                password = st.text_input("Password *", type="password", key="password_signup", help="Must be at least 8 characters.")
                submit = st.form_submit_button("Get Started", type="primary", use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters")
                    else:
                        try:
                            supabase = get_supabase_client()
                            # Sign up with Supabase
                            response = supabase.auth.sign_up({
                                "email": email,
                                "password": password
                            })
                            
                            if response.user:
                                st.success("✅ Account created! Please check your email for confirmation.")
                                
                                # Send custom confirmation email via Hostinger
                                try:
                                    email_service = EmailService()
                                    email_service.send_confirmation(email)
                                except Exception as e:
                                    logger.error(f"Failed to send confirmation email: {e}")
                                
                                Analytics().track_event("user_signup_success", {"email": email})
                                
                                # If there's an invite token, we might want to handle it here or in the confirmation link
                                # For now, just show success
                            else:
                                st.error("Signup failed. Please try again.")
                                
                        except Exception as e:
                            Analytics().track_event("user_signup_failure", {"email": email, "error": str(e)})
                            if "confirmation email" in str(e).lower():
                                st.error("""
                                    **Unable to send confirmation email via Supabase.**
                                    
                                    Please ensure you have **disabled 'Confirm email'** in your Supabase Project Settings (Authentication > Settings). 
                                    
                                    *SmartClause is configured to send its own branded welcome email via Hostinger once the user is created.*
                                """)
                            else:
                                show_error(e, "signup")

            st.markdown('<div class="auth-toggle">Already have an account?</div>', unsafe_allow_html=True)
            if st.button("Back to login", key="switch_to_login", use_container_width=True):
                st.session_state["auth_view"] = "login"
                st.rerun()

        st.markdown('</div></div>', unsafe_allow_html=True)

        # Inject JS to vertically center the right column - only way that works in Streamlit
        import streamlit.components.v1 as _components
        _components.html("""
        <script>
        (function() {
            function applyStyles() {
                try {
                    var doc = window.parent.document;

                    // 1) Inject a <style> into the parent <head> once — broad selectors, no specificity battles
                    if (!doc.getElementById('sc-auth-width')) {
                        var s = doc.createElement('style');
                        s.id = 'sc-auth-width';
                        s.textContent =
                            '[data-testid="column"]:nth-of-type(2) { align-items: center !important; }' +
                            '[data-testid="column"]:nth-of-type(2) > div,' +
                            '[data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlockBorderWrapper"],' +
                            '[data-testid="column"]:nth-of-type(2) [data-testid="stVerticalBlock"] {' +
                            '  width: 60% !important; max-width: 60% !important;' +
                            '  margin-left: auto !important; margin-right: auto !important;' +
                            '  display: flex !important; flex-direction: column !important;' +
                            '  justify-content: center !important;' +
                            '}' +
                            '[data-testid="column"]:nth-of-type(2) .stTextInput,' +
                            '[data-testid="column"]:nth-of-type(2) .stButton,' +
                            '[data-testid="column"]:nth-of-type(2) [data-testid="stForm"],' +
                            '[data-testid="column"]:nth-of-type(2) [data-testid="stFormSubmitButton"] {' +
                            '  width: 100% !important; max-width: 100% !important;' +
                            '}' +
                            '[data-testid="column"]:nth-of-type(2) .stTextInput input,' +
                            '[data-testid="column"]:nth-of-type(2) .stTextInput > div,' +
                            '[data-testid="column"]:nth-of-type(2) .stButton > button,' +
                            '[data-testid="column"]:nth-of-type(2) [data-testid="stFormSubmitButton"] > button {' +
                            '  width: 100% !important;' +
                            '}';
                        doc.head.appendChild(s);
                    }

                    // 2) Also apply inline styles directly to each element (belt-and-suspenders)
                    var cols = doc.querySelectorAll('[data-testid="column"]');
                    if (cols.length < 2) return;
                    var rightCol = cols[cols.length - 1];
                    rightCol.style.setProperty('align-items', 'center', 'important');

                    var blocks = rightCol.querySelectorAll(
                        '[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stVerticalBlock"]'
                    );
                    blocks.forEach(function(el) {
                        el.style.setProperty('width', '60%', 'important');
                        el.style.setProperty('max-width', '60%', 'important');
                        el.style.setProperty('margin-left', 'auto', 'important');
                        el.style.setProperty('margin-right', 'auto', 'important');
                        el.style.setProperty('display', 'flex', 'important');
                        el.style.setProperty('flex-direction', 'column', 'important');
                        el.style.setProperty('justify-content', 'center', 'important');
                    });
                } catch(e) {}
            }

            // Inject styles once

            // Run immediately and on every re-render
            applyStyles();
            window.addEventListener('load', applyStyles);
            var tries = 0;
            var iv = setInterval(function() {
                applyStyles();
                if (++tries > 40) clearInterval(iv);
            }, 150);
            // Watch for DOM mutations (Streamlit re-renders)
            try {
                var mo = new MutationObserver(applyStyles);
                mo.observe(window.parent.document.body, {childList: true, subtree: true});
            } catch(e) {}
        })();
        </script>
        """, height=0)



def check_authentication():
    """
    Check if user is authenticated with true persistence.
    Uses query param-based session cookies that survive navigation.
    """

    # ── PRIORITY: Password-reset / recovery flow ──────────────────────────
    # If sc_type=recovery + sc_token are present, the user clicked a reset link.
    # Skip session restore entirely and show the reset form.
    # login_page() handles the token exchange and form rendering.
    sc_type  = st.query_params.get("sc_type", "")
    sc_token = st.query_params.get("sc_token", "")

    if sc_type == "recovery" and sc_token:
        login_page()
        st.stop()

    # Check if already authenticated in this session
    if st.session_state.get("authenticated"):
        return True
    
    # Try to restore from session cookie
    if restore_session_from_cookie():
        return True
    
    # No valid session - show login
    login_page()
    st.stop()


def logout():
    """Logout user and clear all session data."""
    try:
        # Try to sign out from Supabase
        access_token = st.session_state.get("access_token")
        refresh_token = st.session_state.get("refresh_token")
        
        if access_token and refresh_token:
            supabase = get_supabase_client()
            supabase.auth.set_session(access_token, refresh_token)
            supabase.auth.sign_out()
    except Exception:
        pass
    
    # Clear all session data
    clear_session()
    
    Analytics().track_event("user_logout")
    
    # Force rerun to show login page
    st.rerun()


def require_auth(func):
    """
    Decorator to ensure user is authenticated before accessing a function.
    """
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated"):
            st.error("Please log in to access this feature")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def update_query_params(params: dict):
    """
    Safely update query parameters while preserving critical state like
    session, invite_token, document_id, and matter_id.
    """
    # 1. Get current state
    cookie = get_session_cookie()
    current_params = st.query_params.to_dict()
    
    # 2. Start with new params
    new_params = params.copy()
    
    # 3. Inject session cookie if not already in new_params
    if cookie and "session" not in new_params:
        new_params["session"] = cookie
        
    # 4. Preserve other critical parameters if they exist in current state or session
    critical_params = ["invite_token", "document_id", "matter_id"]
    for p in critical_params:
        if p not in new_params:
            if p in current_params:
                new_params[p] = current_params[p]
            elif f"preserved_{p}" in st.session_state:
                new_params[p] = st.session_state[f"preserved_{p}"]

    # 5. Update the actual query params
    try:
        st.query_params.clear()
        for k, v in new_params.items():
            if v is not None:
                st.query_params[k] = v
    except Exception:
        # Fallback for older versions or edge cases
        for k, v in new_params.items():
            st.query_params[k] = v


def get_session_param() -> str:
    """
    Helper for HTML links to preserve session.
    Returns '&session=XYZ' or '?session=XYZ' or empty string.
    """
    cookie = get_session_cookie()
    if not cookie:
        return ""
    return f"&session={cookie}"
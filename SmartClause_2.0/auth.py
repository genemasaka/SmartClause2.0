# auth.py - TRULY PERSISTENT SESSION (COOKIE-BASED)
import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
import time
import hashlib
import hmac

load_dotenv()

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
    
    # Clear session from query params
    if "session" in st.query_params:
        del st.query_params["session"]


def login_page():
    """Render login page with modern split-screen design."""
    # CRITICAL: Early exit if already authenticated - don't render anything
    if st.session_state.get("authenticated"):
        return
    
    # Initialize view state
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"
    
    # Add custom CSS for the modern split-screen layout
    st.markdown("""
    <style>
        /* 1. GLOBAL RESET & HIDE - COMPLETE SIDEBAR REMOVAL */
        #MainMenu, header, footer {visibility: hidden;}
        [data-testid="stToolbar"] {display: none;}
        
        /* Force sidebar to be completely hidden and take no space */
        [data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            padding: 0 !important;
            transform: translateX(-100%) !important;
        }
        
        section[data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        [data-testid="collapsedControl"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        
        /* Force main content area to take full width with no left offset */
        [data-testid="stAppViewContainer"] {
            margin-left: 0 !important;
            padding-left: 0 !important;
            width: 100vw !important;
            max-width: 100vw !important;
        }
        
        [data-testid="stAppViewContainer"] > div:first-child {
            margin-left: 0 !important;
            padding-left: 0 !important;
        }
        
        /* Override any sidebar spacing that might exist */
        .main {
            margin-left: 0 !important;
            padding-left: 0 !important;
            width: 100vw !important;
        }
        
        .stApp {
            margin-left: 0 !important;
            padding-left: 0 !important;
        }
        
        .appview-container {
            margin-left: 0 !important;
            padding-left: 0 !important;
            width: 100vw !important;
        }
        
        /* Ensure no gap on the left side */
        body {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* 2. BACKGROUND LAYERS */
        .split-bg-left {
            position: fixed;
            top: 0;
            left: 0;
            width: 50vw;
            height: 100vh;
            background: linear-gradient(135deg, #5CB7FF 0%, #4B9EFF 50%, #FFFFFF 100%);
            z-index: 0;
        }
        
        .split-bg-right {
            position: fixed;
            top: 0;
            right: 0;
            width: 50vw;
            height: 100vh;
            background: #000000;
            z-index: 0;
        }
        
        /* 3. CONTENT CONTAINER */
        .stApp {
            background: transparent !important;
        }
        
        .main {
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            overflow: hidden !important;
        }
        
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
            width: 100% !important;
        }
        
        /* 4. CONTENT ALIGNMENT */
        [data-testid="column"] {
            display: flex;
            flex-direction: column;
            justify-content: center;
            height: 100vh !important;
            z-index: 1;
        }
        
        /* Left Column - Farthest Left Alignment */
        [data-testid="column"]:nth-of-type(1) {
            align-items: flex-start !important;
            padding-left: 40px !important;
        }
        
        [data-testid="column"]:nth-of-type(1) > div {
            width: 100%;
            padding: 0 !important;
        }
        
        /* Right Column - Centered */
        [data-testid="column"]:nth-of-type(2) {
            align-items: center !important;
            justify-content: center !important;
            display: flex !important;
        }
        
        [data-testid="column"]:nth-of-type(2) > div {
            width: 100%;
            max-width: 440px !important; /* Limit width to ensure centering */
            padding: 20px !important; /* Balanced padding */
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 0 auto !important; /* Auto margins for horizontal centering */
        }
        
        /* 5. TYPOGRAPHY & COLORS */
        .auth-brand-content {
            text-align: left !important;
            padding-left: 20px; /* Slight buffer from absolute edge */
        }
        
        .auth-brand-content h1 {
            color: white;
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 24px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .auth-brand-content p {
            color: rgba(255, 255, 255, 0.95);
            font-size: 18px;
            line-height: 1.6;
            max-width: 90%;
        }
        
        /* Logo styling */
        .auth-logo {
            width: 56px;
            height: 56px;
            border-radius: 12px;
            background: linear-gradient(135deg, #4B9EFF 0%, #3B7DD1 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 32px;
            box-shadow: 0 4px 12px rgba(75, 158, 255, 0.3);
        }
        
        /* Right Side Text - Updated for Black Background */
        .auth-title {
            font-size: 32px;
            font-weight: 700;
            color: #FFFFFF !important;
            margin-bottom: 12px;
        }
        
        .auth-subtitle {
            font-size: 15px;
            color: #9CA3AF !important;
            margin-bottom: 32px;
            line-height: 1.5;
        }
        
        .stTextInput label {
            color: #D1D5DB !important;
        }
        
        /* Input Fields - White Background, No Text, Blue Border on Focus */
        .stTextInput input {
            background-color: #FFFFFF !important;
            color: #1A1D24 !important;
            border: 1px solid #D1D5DB !important;
            border-radius: 8px !important;
        }
        
        /* Focus state: Blue border same as buttons */
        .stTextInput > div > div:focus-within {
            border-color: #4B9EFF !important;
            box-shadow: 0 0 0 1px #4B9EFF !important;
        }
        
        .stTextInput input:focus {
            border-color: #4B9EFF !important;
        }
        
        /* 6. BUTTONS - FORCE BLUE */
        /* Target every possible button state to override red */
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stButton"] > button,
        button[kind="primary"],
        button[kind="secondary"],
        button[type="submit"] {
            background: linear-gradient(135deg, #4B9EFF 0%, #3B7DD1 100%) !important;
            background-color: #4B9EFF !important;
            border: none !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 14px 20px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            width: 100% !important;
            margin-top: 8px !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stButton"] > button:hover,
        button:hover {
            background: linear-gradient(135deg, #5BABFF 0%, #4B8EE1 100%) !important;
            box-shadow: 0 6px 12px rgba(75, 158, 255, 0.3) !important;
            transform: translateY(-1px);
        }
        
        /* Toggle Links */
        .auth-toggle {
            color: #9CA3AF !important;
        }
        .auth-toggle-link {
            color: #60A5FA !important;
        }
        
        /* Reset gap */
        [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
        }
    </style>
    
    <!-- FIXED BACKGROUNDS -->
    <div class="split-bg-left"></div>
    <div class="split-bg-right"></div>
    """, unsafe_allow_html=True)
    
    # Use columns for side-by-side layout
    with st.container():
        left_col, right_col = st.columns([1, 1], gap="small")
    
    # Left column - Gradient branding
    with left_col:
        pass # Gradient background only
    
    # Right column - Form
    with right_col:
        # Load and verify logo
        try:
            import base64
            import os
            logo_path = "assets/sidebar_logo.png"
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode("utf-8")
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; margin-bottom: 32px;">
                        <img src="data:image/png;base64,{logo_data}" style="width: 200px; height: auto;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Fallback if logo file missing
                st.markdown('<div class="auth-logo">SC</div>', unsafe_allow_html=True)
        except Exception:
             st.markdown('<div class="auth-logo">SC</div>', unsafe_allow_html=True)
        
        # Check which view to show
        if st.session_state["auth_view"] == "login":
            # Login Form
            st.markdown("""
            <div class="auth-title">Welcome</div>
            <div class="auth-subtitle">Sign in to SmartClause account.</div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                # Removed placeholder text as requested ("no text")
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
                                st.rerun()
                            else:
                                st.error("Invalid credentials")
                            
                        except Exception as e:
                            st.error(f"Login failed: {str(e)}")
            
            # Toggle to signup
            st.markdown("""
            <div class="auth-toggle">
                Don't have an account?
            </div>
            """, unsafe_allow_html=True)
            
            # Hidden button to switch to signup
            if st.button("Create new account", key="switch_to_signup"):
                st.session_state["auth_view"] = "signup"
                st.rerun()
        
        else:
            # Signup Form
            st.markdown("""
            <div class="auth-title">Create an account</div>
            """, unsafe_allow_html=True)
            
            with st.form("signup_form", clear_on_submit=False):
                # Removed placeholder text as requested
                email_signup = st.text_input("Your email", key="signup_email")
                password_signup = st.text_input("Password", type="password", key="signup_password")
                password_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
                submit = st.form_submit_button("Get Started", type="primary", use_container_width=True)
                
                if submit:
                    if not email_signup or not password_signup:
                        st.error("Please fill in all fields")
                    elif password_signup != password_confirm:
                        st.error("Passwords don't match!")
                    elif len(password_signup) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        try:
                            supabase = get_supabase_client()
                            
                            response = supabase.auth.sign_up({
                                "email": email_signup,
                                "password": password_signup,
                                "options": {
                                    "data": {
                                        "full_name": email_signup.split('@')[0].title()
                                    }
                                }
                            })
                            
                            if not response:
                                st.error("Sign up failed: No response from server")
                            elif hasattr(response, 'user') and response.user:
                                if response.session:
                                    st.success("✅ Account created successfully! Logging you in...")
                                    save_session(
                                        response.user.id, 
                                        response.user.email,
                                        response.session.access_token,
                                        response.session.refresh_token
                                    )
                                    
                                    # Initialize organization and subscription for new user
                                    try:
                                        from subscription_manager import SubscriptionManager
                                        from database import DatabaseManager
                                        
                                        db = DatabaseManager()
                                        db.set_session(response.session.access_token, response.session.refresh_token)
                                        subscription_mgr = SubscriptionManager(db)
                                        
                                        # Create organization with user email and name
                                        user_name = response.user.user_metadata.get('full_name', 
                                                                                     email_signup.split('@')[0].title())
                                        subscription_mgr.initialize_user_subscription(
                                            response.user.id, 
                                            email_signup,
                                            user_name
                                        )
                                        print(f"Organization created for new user: {email_signup}")
                                    except Exception as sub_error:
                                        print(f"Organization initialization error: {sub_error}")
                                        import traceback
                                        print(traceback.format_exc())
                                        # Don't block signup if organization init fails
                                    
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Account created! Please check your email to confirm your account before logging in.")
                                    st.info("Check your spam folder if you don't see the confirmation email.")
                            else:
                                error_msg = "Unknown error occurred"
                                if hasattr(response, '__dict__'):
                                    error_msg = str(response.__dict__)
                                st.error(f"Sign up failed: {error_msg}")
                            
                        except Exception as e:
                            error_details = str(e)
                            st.error(f"❌ Sign up failed: {error_details}")
                            
                            if "email" in error_details.lower():
                                st.info("💡 This email may already be registered. Try logging in instead.")
                            elif "password" in error_details.lower():
                                st.info("💡 Password must be at least 6 characters long.")
                            elif "network" in error_details.lower() or "connection" in error_details.lower():
                                st.info("💡 Network error. Please check your internet connection.")
                            else:
                                st.info("💡 If the problem persists, please contact support.")
                            
                            import traceback
                            print(f"Sign up error: {traceback.format_exc()}")
            
            # Toggle to login
            st.markdown("""
            <div class="auth-toggle">
                Already have an account?
            </div>
            """, unsafe_allow_html=True)
            
            # Hidden button to switch to login
            if st.button("Back to login", key="switch_to_login"):
                st.session_state["auth_view"] = "login"
                st.rerun()



def check_authentication():
    """
    Check if user is authenticated with true persistence.
    Uses query param-based session cookies that survive navigation.
    """
    
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
    Safely update query parameters while preserving the session cookie.
    This prevents logout when navigating between pages.
    """
    # 1. Get current session cookie
    cookie = get_session_cookie()
    
    # 2. Clear existing params to ensure clean state
    # (Streamlit 1.30+ behavior: assignment replaces)
    new_params = params.copy()
    
    # 3. Inject session cookie if it exists
    if cookie:
        new_params["session"] = cookie
        
    # 4. Update the actual query params
    # Using st.query_params.clear() then update() ensures we remove old params
    st.query_params.clear()
    st.query_params.update(new_params)
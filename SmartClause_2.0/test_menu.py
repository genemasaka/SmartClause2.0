import streamlit as st
import time

# ============================================================================
# 1. PAGE CONFIG & CSS LOADING
# ============================================================================
st.set_page_config(
    page_title="Mock Card & Action Menu",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CRITICAL CSS for absolute positioning and vertical stacking
CSS = """
/* -------------------- Custom Styles for Absolute Positioning -------------------- */

:root {
  --bg: #0A0B0D;
  --panel: #1A1D24;
  --border: #252930;
  --text: #FFFFFF;
  --text-muted: #9BA1B0;
  --accent: #4B9EFF;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* 1. Positioning Anchor: The container holding the card must be relative */
.sc-matter-card-wrapper {
  position: relative; 
  padding: 0 32px; 
  margin: 16px 0;
}

/* 2. Main Card Styling */
.sc-matter-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  min-height: 70px; /* Ensure space for the button overlay */
}

/* 3. Action Button (⋮) Styling and Absolute Positioning */
button[key^="menu_btn_"] {
  /* Positioning the button relative to the card wrapper */
  position: absolute;
  top: 28px; 
  right: 50px; /* 32px wrapper padding + 18px offset */
  z-index: 20; 
  
  /* Sizing and visual cleanup */
  min-width: 36px !important;
  max-width: 36px !important;
  height: 36px !important;
  padding: 0 !important;
  font-size: 20px !important;
  line-height: 1 !important;
  background: transparent !important; 
  border: 1px solid transparent !important; 
  color: var(--text-muted) !important;
  box-shadow: none !important;
  border-radius: var(--radius-sm) !important;
}

button[key^="menu_btn_"]:hover {
  background: rgba(255, 255, 255, 0.05) !important; 
  color: var(--text) !important;
}

/* 4. Dropdown Menu Container: Absolute positioning relative to .sc-matter-card-wrapper */
.sc-matter-dropdown-container {
  position: absolute;
  top: 66px; /* Position below the ⋮ button (28px top + 36px button height) */
  right: 32px; 
  z-index: 30; 
  min-width: 180px; 
}

/* 5. Menu Content: Responsible for vertical stacking and appearance */
.sc-dropdown-stacked {
  background: var(--panel); 
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px; 
  box-shadow: var(--shadow);
  display: flex; 
  flex-direction: column; /* CRITICAL: Stacks the buttons vertically */
  gap: 4px; 
}

/* Style individual buttons inside the stacked menu */
.sc-dropdown-stacked button {
  background: transparent !important;
  border: none !important;
  color: var(--text) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 10px 14px !important; 
  border-radius: var(--radius-sm) !important;
  justify-content: flex-start !important; 
  white-space: nowrap !important;
  width: 100%;
}

.sc-dropdown-stacked button:hover {
  background: rgba(75, 158, 255, 0.12) !important; 
}

/* General app overrides for dark theme appearance */
html, body, [data-testid="stAppViewContainer"], .main {
  background: var(--bg) !important;
  color: var(--text);
}
.block-container {
  padding: 0 32px 32px 32px !important;
  max-width: 100% !important;
}

"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ============================================================================
# 2. CARD & MENU COMPONENT LOGIC
# ============================================================================

def render_mock_card(matter_id: str, matter_name: str, client_name: str):
    
    # 1. State Management
    menu_open = st.session_state.get(f"show_menu_{matter_id}", False)
    
    # 2. Main Card Wrapper (Sets position: relative)
    st.markdown(f'<div class="sc-matter-card-wrapper">', unsafe_allow_html=True)

    # 3. Streamlit Columns for Card Layout
    # Use columns only for positioning the main content next to the menu button area.
    card_col, menu_col = st.columns([1, 0.05], gap="small")

    with card_col:
        # Mock Card HTML
        st.markdown(f"""
<div class="sc-matter-card" style="margin: 0;">
    <div style="font-size: 16px; font-weight: 600; color: var(--text);">{matter_name}</div>
    <div style="font-size: 13px; color: var(--text-muted);">Client: {client_name}</div>
</div>
""", unsafe_allow_html=True)

    with menu_col:
        # Menu Toggle Button
        if st.button("⋮", key=f"menu_btn_{matter_id}", help="Actions", use_container_width=True):
            # Toggle state and RERUN to redraw the menu
            st.session_state[f"show_menu_{matter_id}"] = not menu_open
            st.rerun()

    # 4. Dropdown Menu Rendering
    if menu_open:
        # Use custom HTML classes defined in the CSS for absolute positioning and vertical stack.
        st.markdown('<div class="sc-matter-dropdown-container">', unsafe_allow_html=True)
        st.markdown('<div class="sc-dropdown-stacked">', unsafe_allow_html=True)
        
        # Action Buttons (Will be vertically stacked by .sc-dropdown-stacked CSS)
        if st.button("📌 Pin (Dummy)", key=f"pin_{matter_id}", use_container_width=True):
            st.session_state[f"show_menu_{matter_id}"] = False
            st.success("Pinned!")
            time.sleep(1)
            st.rerun()
        
        if st.button("📦 Archive (Dummy)", key=f"archive_{matter_id}", use_container_width=True):
            st.session_state[f"show_menu_{matter_id}"] = False
            st.info("Archived!")
            time.sleep(1)
            st.rerun()
        
        if st.button("🗑️ Delete (Dummy)", key=f"delete_{matter_id}", use_container_width=True):
            st.session_state[f"show_menu_{matter_id}"] = False
            st.error("Delete Confirmation TBD...")
            time.sleep(1)
            st.rerun()
            
        if st.button("✖ Close Menu", key=f"close_{matter_id}", use_container_width=True):
            st.session_state[f"show_menu_{matter_id}"] = False
            st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True) # Close sc-matter-card-wrapper


# ============================================================================
# 3. RUNTIME
# ============================================================================

st.markdown('<h1 style="color:var(--text); padding-left: 32px;">Mock Card Test</h1>', unsafe_allow_html=True)

render_mock_card(
    matter_id="mock_test_001",
    matter_name="Simple Service Agreement",
    client_name="Acme Corp"
)

render_mock_card(
    matter_id="mock_test_002",
    matter_name="Complex Licensing Deal",
    client_name="Beta Solutions"
)

st.markdown('<div style="margin: 40px 32px; color: var(--text-muted);">The menu uses absolute positioning CSS to float above the card and is vertically stacked using the `flex-direction: column` CSS property.</div>', unsafe_allow_html=True)
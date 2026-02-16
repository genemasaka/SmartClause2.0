import streamlit as st

def render_settings():
    # Header
    st.markdown(
        """
        <div class="sc-main-header">
          <div class="sc-header-left">
            <div class="sc-page-title">Settings</div>
            <div class="sc-page-subtitle">Configure your firm branding and preferences</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="settings-content-wrap">', unsafe_allow_html=True)

    # --- Firm Branding ---
    st.markdown(
        """
        <div class="sc-section-header">
            <div class="sc-section-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
            </div>
            <div>
                <h2 class="sc-section-title">Firm Branding</h2>
                <p class="sc-section-sub">Customize your firm's logo and branding</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="sc-card">', unsafe_allow_html=True)
        
        # Logo
        st.markdown('<label class="sc-label">Firm Logo</label>', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(
                """
                <div class="logo-preview-box">SC</div>
                <p class="logo-caption">Recommended size: 256x256px, PNG or SVG</p>
                """, unsafe_allow_html=True)
        with col2:
            st.button("⬆ Upload Logo", key="upload_logo")

        # Firm Name
        st.markdown('<div class="sc-form-group"><label class="sc-label">Firm Name</label>', unsafe_allow_html=True)
        st.text_input("firm_name", value="SmartClause Legal", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Address
        st.markdown('<div class="sc-form-group"><label class="sc-label">Address</label>', unsafe_allow_html=True)
        st.text_area("firm_address", value="Nairobi, Kenya", height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Privacy & Security ---
    st.markdown(
        """
        <div class="sc-section-header">
            <div class="sc-section-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            </div>
            <div>
                <h2 class="sc-section-title">Privacy & Security</h2>
                <p class="sc-section-sub">Control data handling and security settings</p>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="sc-card">', unsafe_allow_html=True)

        st.markdown('<div class="sc-toggle-wrapper">', unsafe_allow_html=True)
        st.toggle("scrub_pii", value=False, label_visibility="collapsed")
        st.markdown(
            """
            <div class="sc-toggle-text">
                <label class="sc-label">Scrub PII on Export</label>
                <p class="sc-sublabel">Automatically remove personally identifiable information from exported documents</p>
            </div></div>
            """, unsafe_allow_html=True
        )

        st.markdown('<div class="sc-toggle-wrapper">', unsafe_allow_html=True)
        st.toggle("auto_save", value=True, label_visibility="collapsed")
        st.markdown(
            """
            <div class="sc-toggle-text">
                <label class="sc-label">Auto-save Drafts</label>
                <p class="sc-sublabel">Automatically save your work every 2 minutes</p>
            </div></div>
            """, unsafe_allow_html=True
        )

        st.markdown('<div class="sc-toggle-wrapper">', unsafe_allow_html=True)
        st.toggle("version_history", value=True, label_visibility="collapsed")
        st.markdown(
            """
            <div class="sc-toggle-text">
                <label class="sc-label">Unlimited Version History</label>
                <p class="sc-sublabel">Keep all draft versions indefinitely</p>
            </div></div>
            """, unsafe_allow_html=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Typography & Spacing ---
    st.markdown(
        """
        <div class="sc-section-header">
            <div class="sc-section-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 7 4"></polyline><line x1="20" y1="10" x2="10" y2="10"></line><line x1="20" y1="14" x2="10" y2="14"></line><line x1="20" y1="18" x2="10" y2="18"></line><line x1="14" y1="20" x2="14" y2="4"></line></svg>
            </div>
            <div>
                <h2 class="sc-section-title">Typography & Spacing</h2>
                <p class="sc-section-sub">Preview of document formatting settings</p>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    
    with st.container():
        st.markdown('<div class="sc-card">', unsafe_allow_html=True)

        st.markdown('<div class="sc-form-group"><label class="sc-label">Document Font</label>', unsafe_allow_html=True)
        st.selectbox("doc_font", ["Times New Roman (Default)", "Arial", "Calibri"], label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sc-form-group"><label class="sc-label">Body Text Size</label>', unsafe_allow_html=True)
        st.selectbox("text_size", ["11pt", "12pt", "13pt"], label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sc-form-group"><label class="sc-label">Line Spacing</label>', unsafe_allow_html=True)
        st.selectbox("line_spacing", ["Single", "1.15", "1.5", "Double"], label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="sc-form-group">
                <label class="sc-label">Preview</label>
                <div class="sc-preview-box">
                This Agreement shall be governed by and construed in accordance with the laws of Kenya. The parties hereby submit to the exclusive jurisdiction of the courts of Kenya for the resolution of any disputes arising under this Agreement.
                </div>
            </div>
            """, unsafe_allow_html=True
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # --- Page Actions ---
    st.markdown('<div class="sc-actions-footer">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("Reset to Defaults", key="reset_settings")
    with col2:
        st.button("Save Settings", key="save_settings", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)
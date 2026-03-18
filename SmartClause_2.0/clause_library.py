import streamlit as st
from database import DatabaseManager
import time
from bs4 import BeautifulSoup
import streamlit.components.v1 as components
from error_helpers import show_error
import json
from analytics import Analytics

def render_clause_library():
    """Enhanced clause library with full CRUD operations."""
    db = DatabaseManager()
    db.set_user(st.session_state.user_id)
    

    # PAYWALL CHECK: Clause Library Access
    from subscription_manager import SubscriptionManager
    sub_manager = SubscriptionManager(db)
    
    if not sub_manager.has_access(st.session_state.user_id, "clause_library"):
        st.markdown("""
        <div class="sc-main-header">
            <div class="sc-header-left">
                <div class="sc-page-title">Clause Library</div>
                <div class="sc-page-subtitle">Reusable clauses and precedents</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🔒 The Clause Library is available to Individual Plan subscribers and up.")
        
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; border-radius: 12px; padding: 40px; text-align: center; margin-top: 20px;">
            <div style="display: flex; justify-content: center; margin-bottom: 24px;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M2 12.0001L11.6422 16.8212C11.7734 16.8868 11.839 16.9196 11.9078 16.9325C11.9687 16.9439 12.0313 16.9439 12.0922 16.9325C12.161 16.9196 12.2266 16.8868 12.3578 16.8212L22 12.0001M2 17.0001L11.6422 21.8212C11.7734 21.8868 11.839 21.9196 11.9078 21.9325C11.9687 21.9439 12.0313 21.9439 12.0922 21.9325C12.161 21.9196 12.2266 21.8868 12.3578 21.8212L22 17.0001M2 7.00006L11.6422 2.17895C11.7734 2.11336 11.839 2.08056 11.9078 2.06766C11.9687 2.05622 12.0313 2.05622 12.0922 2.06766C12.161 2.08056 12.2266 2.11336 12.3578 2.17895L22 7.00006L12.3578 11.8212C12.2266 11.8868 12.161 11.9196 12.0922 11.9325C12.0313 11.9439 11.9687 11.9439 11.9078 11.9325C11.839 11.9196 11.7734 11.8868 11.6422 11.8212L2 7.00006Z" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <h2 style="color: #FFFFFF; margin-bottom: 16px;">Unlock the Clause Library</h2>
            <p style="color: #9BA1B0; font-size: 16px; max-width: 600px; margin: 0 auto 32px auto; line-height: 1.6;">
                Save your own custom clauses, categorize them, and insert them into your documents instantly.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Use a Streamlit button + update_query_params so the session cookie is
        # preserved during navigation (HTML <a> tags bypass Streamlit's session
        # management and cause the user to appear logged out).
        from auth import update_query_params
        st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
        col_l, col_btn, col_r = st.columns([2, 1, 2])
        with col_btn:
            if st.button("Upgrade to Individual Plan", type="primary", use_container_width=True):
                update_query_params({"view": "pricing"})
                st.rerun()
        return


    # Page header with 'Add New Clause' button
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown("""
        <div class="sc-header-left">
            <div class="sc-page-title">Clause Library</div>
            <div class="sc-page-subtitle">Reusable clauses and precedents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_btn:
        st.markdown('<div style="margin-top: 24px; float: right;">', unsafe_allow_html=True)
        if st.button("Add New Clause", use_container_width=True, type="primary"):
            Analytics().track_event("clause_add_initiated")
            st.session_state.show_add_clause_form = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons - aligned with content, width reduced by 40%, and height reduced by 20%
    st.markdown("""
    <style>
    div[data-testid="stTextInput"] input {
        height: 32px !important;
        min-height: 32px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        font-size: 14px !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        height: 32px !important;
        min-height: 32px !important;
        display: flex;
        align-items: center;
    }
    div[data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] p {
        font-size: 14px !important;
        line-height: normal !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_spacer, col_content, col_empty = st.columns([0.035, 0.48, 0.485])
    with col_content:
        col1, col2 = st.columns([2, 1])
        with col1:
            search_query = st.text_input("🔍 Search clauses", placeholder="Search by title, category, or tags...", label_visibility="collapsed")
        with col2:
            category_filter = st.selectbox("Filter by Category", ["All", "Boilerplate", "Protection", "Warranties", "Definitions", "Payment Terms", "Termination", "Other"], label_visibility="collapsed")
    
    # Get clauses from database
    all_clauses = db.get_clauses(include_system=True)
    
    # Apply filters
    filtered_clauses = all_clauses
    if search_query:
        filtered_clauses = [c for c in filtered_clauses if 
                          search_query.lower() in c['title'].lower() or 
                          search_query.lower() in c.get('preview', '').lower() or
                          any(search_query.lower() in tag.lower() for tag in c.get('tags', []))]
    
    if category_filter != "All":
        filtered_clauses = [c for c in filtered_clauses if c['category'] == category_filter]

    if search_query:
        Analytics().track_event("clause_search", {"query": search_query})
    
    # Separate pinned and unpinned
    pinned = [c for c in filtered_clauses if c.get("is_pinned", False)]
    others = [c for c in filtered_clauses if not c.get("is_pinned", False)]
    
    # Stats summary - matching width of clause cards (which use columns [20, 1])
    col_stats, _ = st.columns([20, 1])
    with col_stats:
        st.markdown(f"""
        <div style="padding: 16px 32px; background: rgba(75, 158, 255, 0.1); border-radius: 8px; margin: 16px 32px;">
            <div style="color: #FFFFFF; font-size: 14px;">
                📚 <strong>{len(all_clauses)}</strong> total clauses  •  
                📌 <strong>{len(pinned)}</strong> pinned  •  
                🔍 <strong>{len(filtered_clauses)}</strong> matching filters
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Render pinned section
    if pinned:
        st.markdown("""
        <div class="sc-section-line" style="margin: 24px 32px;">
            <svg class="sc-pin-icon" width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="6" r="3" stroke="currentColor" stroke-width="1.2"/>
                <path d="M9 12h6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                <path d="M12 9v6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                <path d="M12 21l-2-6h4l-2 6z" fill="currentColor"/>
            </svg>
            <div class="sc-section-title">PINNED CLAUSES</div>
        </div>
        """, unsafe_allow_html=True)
        for clause in pinned:
            _render_clause_card_db(clause, db)
    
    # Render all clauses
    st.markdown('<div class="sc-section-title" style="margin: 24px 32px;">ALL CLAUSES</div>', unsafe_allow_html=True)
    
    if not others:
        st.info("No clauses found. Try adjusting your filters or add a new clause.")
    else:
        for clause in others:
            _render_clause_card_db(clause, db)
    
    # Add/Edit clause form (if triggered)
    if st.session_state.get("show_add_clause_form"):
        render_add_clause_form(db)
    
    if st.session_state.get("show_edit_clause_form"):
        render_edit_clause_form(db, st.session_state.get("edit_clause_id"))


def _render_clause_card_db(clause: dict, db: DatabaseManager):
    """Render clause card with database integration and action buttons."""
    tags_html = "".join(f'<span class="sc-tag">{t}</span>' for t in clause.get("tags", []))
    
    # Badge style based on category
    badge_colors = {
        "Boilerplate": "#4B9EFF",
        "Protection": "#10B981", 
        "Warranties": "#F59E0B",
        "Definitions": "#8B5CF6",
        "Payment Terms": "#EC4899",
        "Termination": "#EF4444",
        "Other": "#6B7280"
    }
    badge_color = badge_colors.get(clause['category'], "#6B7280")
    
    # Create columns for Card and Menu
    col_card, col_menu = st.columns([20, 1])
    
    with col_card:
        st.markdown(f"""
        <div class="sc-card clause-card" style="margin-bottom: 8px;">
            <div class="cl-left" style="flex: 1;">
                <div class="cl-title-row" style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <div class="sc-card-title" style="color: #FFFFFF; font-size: 15px; font-weight: 600;">{clause['title']}</div>
                    <span class="sc-badge" style="background: {badge_color}; color: #FFFFFF; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">{clause['category']}</span>
                    {f'<span style="color: #9BA1B0; font-size: 11px;">📊 Used {clause.get("usage_count", 0)} times</span>' if not clause.get('is_system') else '<span style="color: #4B9EFF; font-size: 11px;">🔒 System Clause</span>'}
                </div>
                <div class="sc-card-sub" style="color: #9BA1B0; font-size: 13px; margin-bottom: 8px;">{clause.get('preview', '')[:200]}...</div>
                <div class="cl-tags" style="display: flex; flex-wrap: wrap; gap: 6px;">{tags_html}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_menu:
        # Centering helper for the kebab menu
        st.markdown('<div style="position: absolute; top: 15px; right: 20px;">', unsafe_allow_html=True)
        
        with st.popover("⋮"):
            # Pin Action
            pin_text = "Unpin" if clause.get("is_pinned") else "Pin"
            if st.button(pin_text, key=f"pin_{clause['id']}", use_container_width=True):
                db.toggle_clause_pin(clause['id'])
                Analytics().track_event(f"clause_{pin_text.lower()}", {"clause_id": clause['id'], "title": clause['title']})
                st.success(f"Clause {pin_text.lower()}ned!")
                st.rerun()
            
            # Edit Action
            if st.button("Edit", key=f"edit_{clause['id']}", use_container_width=True):
                if clause.get('is_system'):
                    st.warning("System clauses cannot be edited.")
                else:
                    Analytics().track_event("clause_edit_initiated", {"clause_id": clause['id']})
                    st.session_state.show_edit_clause_form = True
                    st.session_state.edit_clause_id = clause['id']
                    st.rerun()
            
            # Copy Action (Custom Component)
            content_json = json.dumps(clause['content'])
            # Updated CSS for Popover styling (Transparent bg, white text, hover effect)
            btn_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body {{ margin: 0; padding: 0; background: transparent; }}
                .copy-btn {{
                    width: 100%;
                    display: block;
                    padding: 0.25rem 0.75rem;
                    text-align: left;
                    font-size: 1rem;
                    font-weight: 400;
                    color: white;
                    background-color: transparent;
                    border: none;
                    cursor: pointer;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
                    line-height: 1.6;
                    border-radius: 0.25rem;
                    transition: background-color 0.15s ease-in-out;
                    padding-left: 12px; /* Match typical Streamlit button padding */
                }}
                .copy-btn:hover {{
                    background-color: #333333;
                }}
                .copy-btn span {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }}
            </style>
            </head>
            <body>
                <button class="copy-btn" onclick="copyContent(this)">
                    <span>Copy</span>
                </button>

                <script>
                    function copyContent(btn) {{
                        const content = {content_json};
                        navigator.clipboard.writeText(content).then(function() {{
                            btn.innerHTML = '<span>Copied!</span>';
                            setTimeout(() => {{ btn.innerHTML = '<span>Copy</span>'; }}, 2000);
                        }}, function(err) {{
                            btn.innerHTML = '<span>Error</span>';
                        }});
                    }}
                </script>
            </body>
            </html>
            """
            # Height adjusted to match text line height roughly
            components.html(btn_html, height=36, scrolling=False)

            # Delete Action
            if st.button("Delete", key=f"delete_{clause['id']}", use_container_width=True):
                if clause.get('is_system'):
                    st.warning("System clauses cannot be deleted.")
                else:
                    Analytics().track_event("clause_delete_initiated", {"clause_id": clause['id']})
                    st.session_state[f"confirm_delete_clause_{clause['id']}"] = True
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Delete confirmation (Outside popover)
    if st.session_state.get(f"confirm_delete_clause_{clause['id']}", False):
        st.warning(f"⚠️ Are you sure you want to delete '{clause['title']}'?")
        col_yes, col_no = st.columns(2)
        
        with col_yes:
            if st.button("Yes, Delete", key=f"confirm_yes_clause_{clause['id']}", use_container_width=True, type="primary"):
                db.update_clause(clause['id'], {"deleted_at": "now()"})
                Analytics().track_event("clause_delete_confirmed", {"clause_id": clause['id']})
                st.session_state[f"confirm_delete_clause_{clause['id']}"] = False
                st.success(f"✅ Deleted '{clause['title']}'")
                time.sleep(0.5)
                st.rerun()
        
        with col_no:
            if st.button("Cancel", key=f"confirm_no_clause_{clause['id']}", use_container_width=True):
                st.session_state[f"confirm_delete_clause_{clause['id']}"] = False
                st.rerun()
    
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


@st.dialog("Add New Clause", width="large")
def render_add_clause_form(db: DatabaseManager):
    """Form to add a new clause."""
    st.markdown("### 📝 Create a New Clause")
    
    title = st.text_input("Clause Title*", placeholder="e.g., Governing Law (Kenya)")
    
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Category*", [
            "Boilerplate",
            "Protection",
            "Warranties",
            "Definitions",
            "Payment Terms",
            "Termination",
            "Other"
        ])
    
    with col2:
        tags_input = st.text_input("Tags (comma-separated)", 
                                    placeholder="e.g., kenya, jurisdiction, dispute")
    
    content = st.text_area("Clause Content*", height=300, 
                          placeholder="Enter the clause text here. You can use rich text formatting in the editor.")
    
    st.markdown("---")
    
    col_cancel, col_save = st.columns([1, 1])
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_add_clause_form = False
            st.rerun()
    
    with col_save:
        if st.button("✅ Add Clause", use_container_width=True, type="primary"):
            if not title or not content:
                st.error("❌ Title and content are required")
            elif len(content.strip()) < 10:
                st.error("❌ Clause content is too short (minimum 10 characters)")
            else:
                try:
                    # Extract plain text
                    soup = BeautifulSoup(content, 'html.parser')
                    content_plain = soup.get_text()
                    
                    tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
                    
                    db.create_clause(
                        title=title.strip(),
                        category=category,
                        content=content,
                        content_plain=content_plain,
                        preview=content_plain[:200],
                        tags=tags,
                        is_system=False
                    )
                    
                    st.session_state.show_add_clause_form = False
                    Analytics().track_event("clause_create_success", {"title": title, "category": category})
                    st.success(f"✅ Clause '{title}' added successfully!")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    show_error(e, "clause")


@st.dialog("Edit Clause", width="large")
def render_edit_clause_form(db: DatabaseManager, clause_id: str):
    """Form to edit an existing clause."""
    clause = db.get_clause(clause_id)
    
    if not clause:
        st.error("❌ Clause not found")
        return
    
    st.markdown(f"### ✏️ Edit Clause: {clause['title']}")
    
    title = st.text_input("Clause Title*", value=clause['title'])
    
    col1, col2 = st.columns(2)
    with col1:
        categories = ["Boilerplate", "Protection", "Warranties", "Definitions", "Payment Terms", "Termination", "Other"]
        category = st.selectbox("Category*", categories, 
                               index=categories.index(clause['category']) if clause['category'] in categories else 0)
    
    with col2:
        tags_str = ", ".join(clause.get('tags', []))
        tags_input = st.text_input("Tags (comma-separated)", value=tags_str)
    
    content = st.text_area("Clause Content*", value=clause['content'], height=300)
    
    st.markdown("---")
    
    col_cancel, col_save = st.columns([1, 1])
    
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_edit_clause_form = False
            st.session_state.edit_clause_id = None
            st.rerun()
    
    with col_save:
        if st.button("Save Changes", use_container_width=True, type="primary"):
            if not title or not content:
                st.error("Title and content are required")
            elif len(content.strip()) < 10:
                st.error("Clause content is too short (minimum 10 characters)")
            else:
                try:
                    soup = BeautifulSoup(content, 'html.parser')
                    content_plain = soup.get_text()
                    
                    tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
                    
                    db.update_clause(clause_id, {
                        "title": title.strip(),
                        "category": category,
                        "content": content,
                        "content_plain": content_plain,
                        "preview": content_plain[:200],
                        "tags": tags
                    })
                    
                    st.session_state.show_edit_clause_form = False
                    st.session_state.edit_clause_id = None
                    Analytics().track_event("clause_update_success", {"clause_id": clause_id, "title": title})
                    st.success(f"Clause '{title}' updated successfully!")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    show_error(e, "clause")
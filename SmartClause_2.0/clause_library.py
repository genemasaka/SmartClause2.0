import streamlit as st
from database import DatabaseManager
import time
from bs4 import BeautifulSoup
import streamlit.components.v1 as components
import json


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
        
        st.info("🔒 The Clause Library is available exclusively to Standard Plan subscribers.")
        
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; border-radius: 12px; padding: 40px; text-align: center; margin-top: 20px;">
            <div style="font-size: 64px; margin-bottom: 24px;">📚</div>
            <h2 style="color: #FFFFFF; margin-bottom: 16px;">Unlock the Clause Library</h2>
            <p style="color: #9BA1B0; font-size: 16px; max-width: 600px; margin: 0 auto 32px auto; line-height: 1.6;">
                Save your own custom clauses, categorize them, and insert them into your documents instantly.
            </p>
            <div style="display: flex; justify-content: center; gap: 16px;">
                <a href="?view=pricing" target="_self" style="background-color: #4B9EFF; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">
                    Upgrade to Standard
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Page header
    st.markdown("""
    <div class="sc-main-header">
        <div class="sc-header-left">
            <div class="sc-page-title">Clause Library</div>
            <div class="sc-page-subtitle">Reusable clauses and precedents</div>
        </div>
        <div class="sc-header-right">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search clauses", placeholder="Search by title, category, or tags...", label_visibility="collapsed")
    with col2:
        category_filter = st.selectbox("Filter by Category", ["All", "Boilerplate", "Protection", "Warranties", "Definitions", "Payment Terms", "Termination", "Other"], label_visibility="collapsed")
    with col3:
        if st.button("Add New Clause", use_container_width=True, type="primary"):
            st.session_state.show_add_clause_form = True
            st.rerun()
    
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
    
    # Separate pinned and unpinned
    pinned = [c for c in filtered_clauses if c.get("is_pinned", False)]
    others = [c for c in filtered_clauses if not c.get("is_pinned", False)]
    
    # Stats summary
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
                st.success(f"Clause {pin_text.lower()}ned!")
                st.rerun()
            
            # Edit Action
            if st.button("Edit", key=f"edit_{clause['id']}", use_container_width=True):
                if clause.get('is_system'):
                    st.warning("System clauses cannot be edited.")
                else:
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
                    st.success(f"✅ Clause '{title}' added successfully!")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to add clause: {str(e)}")


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
                    st.success(f"Clause '{title}' updated successfully!")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to update clause: {str(e)}")
"""
Case Manager Component - Streamlit UI
Professional case management interface for Kenyan legal system
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from database import DatabaseManager
from case_manager_logic import CaseManager


def render_case_manager(matter_id: str, matter_name: str, db: DatabaseManager):
    """Main case manager component."""
    
    # Initialize case manager
    case_mgr = CaseManager(db)
    user_id = st.session_state.get("user_id")
    
    if not user_id:
        st.error("⚠️ Please log in to access case manager")
        return
    
    # Get organization ID
    org_data = db.get_user_organization(user_id)
    organization_id = org_data['id'] if org_data else None
    
    # Style override for dark theme
    st.markdown("""
    <style>
    /* Override Streamlit native styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
        border-bottom: 2px solid #E5E7EB;
        margin-bottom: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #6B7280;
        padding: 12px 4px;
        font-weight: 500;
        font-size: 14px;
        outline: none;
        box-shadow: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #000000;
        border-bottom: 2px solid #000000;
        margin-bottom: -2px;
        font-weight: 600;
        outline: none;
        box-shadow: none;
    }
    
    /* Custom case cards */
    .case-card {
        background: #1A1D24;
        border: 1px solid #252930;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.2s ease;
    }
    
    .case-card:hover {
        border-color: #4B9EFF;
        box-shadow: 0 4px 12px rgba(75, 158, 255, 0.1);
    }
    
    .stat-box {
        background: rgba(75, 158, 255, 0.08);
        border: 1px solid rgba(75, 158, 255, 0.2);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 28px;
        font-weight: 700;
        color: #4B9EFF;
        line-height: 1.2;
    }
    
    .stat-label {
        font-size: 12px;
        color: #9BA1B0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }
    
    .timeline-item {
        position: relative;
        padding-left: 32px;
        padding-bottom: 24px;
        border-left: 2px solid #252930;
    }
    
    .timeline-item:last-child {
        border-left-color: transparent;
    }
    
    .timeline-dot {
        position: absolute;
        left: -7px;
        top: 4px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #4B9EFF;
        border: 2px solid #0A0B0D;
    }
    
    .task-card {
        background: #1A1D24;
        border-left: 4px solid #4B9EFF;
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    
    .task-card.urgent {
        border-left-color: #EF4444;
    }
    
    .task-card.high {
        border-left-color: #F59E0B;
    }
    
    .task-card.completed {
        opacity: 0.6;
        border-left-color: #4ADE80;
    }
    
    .priority-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .priority-urgent {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
    }
    
    .priority-high {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
    }
    
    .priority-medium {
        background: rgba(75, 158, 255, 0.15);
        color: #4B9EFF;
    }
    
    .priority-low {
        background: rgba(155, 161, 176, 0.15);
        color: #9BA1B0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get cases for this matter
    cases = case_mgr.get_cases_for_matter(matter_id)
    
    # Header with New Case button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style="color: #4B9EFF;">
                <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
                <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>
                <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>
                <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>
            </svg>
            <h1 style="font-size: 24px; font-weight: 700; color: #FFFFFF; margin: 0;">Case Manager</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("New Case", use_container_width=True, type="primary", key="new_case_main_btn"):
            st.session_state['show_new_case_form'] = True
            st.session_state['show_case_modal'] = False  # Ensure only one modal is open
            st.rerun()
    
    # Show cases or empty state
    if not cases:
        _render_empty_state(matter_id, matter_name, case_mgr, user_id, organization_id)
    else:
        # Display cases as clickable cards
        st.markdown(f"<div style='font-size: 14px; color: #9BA1B0; margin-bottom: 16px;'>{len(cases)} case{'s' if len(cases) != 1 else ''} for this matter</div>", unsafe_allow_html=True)
        
        # Grid layout for case cards
        cols_per_row = 2
        for i in range(0, len(cases), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(cases):
                    case = cases[i + j]
                    with col:
                        _render_case_card(case, case_mgr, user_id)
    
    # Render modals - only one at a time to avoid Streamlit dialog conflict
    if st.session_state.get('show_new_case_form'):
        _render_new_case_form(matter_id, case_mgr, user_id, organization_id)
    elif st.session_state.get('show_edit_case_form'):
        selected_case_id = st.session_state.get('selected_case_id')
        if selected_case_id:
            _render_edit_case_form(selected_case_id, case_mgr, user_id)
    elif st.session_state.get('show_case_modal'):
        selected_case_id = st.session_state.get('selected_case_id')
        if selected_case_id:
            case = case_mgr.get_case(selected_case_id)
            if case:
                _render_case_modal(case, case_mgr, user_id)


def _render_case_card(case: Dict[str, Any], case_mgr: CaseManager, user_id: str):
    """Render a clickable case card."""
    case_number = case.get('case_number', 'No Case Number')
    case_type = case.get('case_type', '').title()
    court = case.get('court_level', '').replace('_', ' ').title()
    location = case.get('court_location', 'Location TBD')
    status = case.get('case_status', 'active')
    
    # Get quick stats
    tasks = case_mgr.get_case_tasks(case['id'])
    events = case_mgr.get_case_timeline(case['id'])
    pending_tasks = [t for t in tasks if t['status'] == 'pending']
    overdue_tasks = case_mgr.get_overdue_tasks(case['id'])
    
    status_color = {
        'active': '#4ADE80',
        'pending': '#F59E0B',
        'concluded': '#9BA1B0',
        'withdrawn': '#EF4444',
        'settled': '#4B9EFF'
    }.get(status, '#9BA1B0')
    
    # Calculate RGB values for background
    r = int(status_color[1:3], 16)
    g = int(status_color[3:5], 16)
    b = int(status_color[5:7], 16)
    
    overdue_color = '#EF4444' if overdue_tasks else '#4ADE80'
    
    # Render card - HTML must not have leading whitespace
    st.markdown(f"""<div class="case-card" style="margin-bottom: 16px;">
<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
<div>
<div style="font-size: 18px; font-weight: 600; color: #FFFFFF; margin-bottom: 4px;">{case_number}</div>
<div style="font-size: 13px; color: #9BA1B0;">{case_type} • {court}</div>
<div style="font-size: 12px; color: #6B7280; margin-top: 2px;">{location}</div>
</div>
<span style="display: inline-flex; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; background: rgba({r}, {g}, {b}, 0.15); color: {status_color};">
{status.upper()}
</span>
</div>
<div style="display: flex; gap: 20px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #252930;">
<div>
<div style="font-size: 20px; font-weight: 700; color: #4B9EFF;">{len(events)}</div>
<div style="font-size: 11px; color: #9BA1B0;">Events</div>
</div>
<div>
<div style="font-size: 20px; font-weight: 700; color: #4B9EFF;">{len(pending_tasks)}</div>
<div style="font-size: 11px; color: #9BA1B0;">Pending</div>
</div>
<div>
<div style="font-size: 20px; font-weight: 700; color: {overdue_color};">{len(overdue_tasks)}</div>
<div style="font-size: 11px; color: #9BA1B0;">Overdue</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
    
    # Click handler button
    if st.button("View Case", key=f"view_case_{case['id']}", type="secondary", use_container_width=True):
        st.session_state['show_case_modal'] = True
        st.session_state['selected_case_id'] = case['id']
        st.session_state['case_analysis'] = None  # Clear previous analysis
        st.session_state['show_new_case_form'] = False  # Ensure only one modal is open
        st.rerun()


def _render_empty_state(matter_id: str, matter_name: str, case_mgr: CaseManager, user_id: str, organization_id: Optional[str]):
    """Render empty state when no cases exist."""
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.03); border: 2px dashed #252930; border-radius: 12px; padding: 48px; text-align: center; margin: 40px 0;">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" style="color: #6B7280; margin: 0 auto 24px;">
            <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>
            <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>
            <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>
        </svg>
        <div style="font-size: 20px; font-weight: 600; color: #FFFFFF; margin-bottom: 8px;">No Cases Yet</div>
        <div style="font-size: 15px; color: #9BA1B0; margin-bottom: 32px;">Create your first case to start tracking court proceedings for {matter_name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Create First Case", type="primary", use_container_width=True, key="create_first_case"):
        st.session_state['show_new_case_form'] = True
        st.session_state['show_case_modal'] = False
        st.rerun()


@st.dialog("Create New Case", width="large")
def _render_new_case_form(matter_id: str, case_mgr: CaseManager, user_id: str, organization_id: Optional[str]):
    """Form to create a new case."""
    
    st.markdown("### Case Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        case_number = st.text_input(
            "Case Number",
            placeholder="e.g., HC Petition No. 123 of 2024",
            key="new_case_number"
        )
        
        case_type = st.selectbox(
            "Case Type *",
            options=['civil', 'criminal', 'commercial', 'land', 'family', 'constitutional', 'employment', 'other'],
            format_func=lambda x: x.title(),
            key="new_case_type"
        )
        
        court_level = st.selectbox(
            "Court Level *",
            options=['magistrate', 'high_court', 'court_of_appeal', 'supreme_court', 'tribunal'],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="new_court_level"
        )
    
    with col2:
        court_location = st.text_input(
            "Court Location",
            placeholder="e.g., Milimani, Nairobi",
            key="new_court_location"
        )
        
        filing_date = st.date_input(
            "Filing Date",
            value=None,
            key="new_filing_date"
        )
        
        current_stage = st.selectbox(
            "Current Stage",
            options=['filing', 'pleadings', 'interlocutory', 'discovery', 'hearing', 'judgment', 'appeal', 'concluded'],
            format_func=lambda x: x.title(),
            key="new_stage"
        )
    
    st.markdown("### Parties")
    
    plaintiff = st.text_area(
        "Plaintiff/Petitioner",
        placeholder="Enter plaintiff or petitioner name(s)",
        key="new_plaintiff",
        height=80
    )
    
    defendant = st.text_area(
        "Defendant/Respondent",
        placeholder="Enter defendant or respondent name(s)",
        key="new_defendant",
        height=80
    )
    
    col1, col2 = st.columns(2)
    with col1:
        plaintiff_advocate = st.text_input(
            "Plaintiff's Advocate",
            key="new_plaintiff_advocate"
        )
    
    with col2:
        defendant_advocate = st.text_input(
            "Defendant's Advocate",
            key="new_defendant_advocate"
        )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state['show_new_case_form'] = False
            st.rerun()
    
    with col2:
        if st.button("Create Case", type="primary", use_container_width=True):
            if not case_type:
                st.error("Case type is required")
                return
            
            case_data = {
                'case_number': case_number if case_number else None,
                'case_type': case_type,
                'court_level': court_level,
                'court_location': court_location if court_location else None,
                'filing_date': filing_date.isoformat() if filing_date else None,
                'current_stage': current_stage,
                'plaintiff_petitioner': plaintiff if plaintiff else None,
                'defendant_respondent': defendant if defendant else None,
                'plaintiff_advocate': plaintiff_advocate if plaintiff_advocate else None,
                'defendant_advocate': defendant_advocate if defendant_advocate else None,
                'case_status': 'active'
            }
            
            new_case = case_mgr.create_case(matter_id, user_id, organization_id, case_data)
            
            if new_case:
                st.success("✅ Case created successfully!")
                st.session_state['show_new_case_form'] = False
                import time
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Failed to create case. Please try again.")




@st.dialog("Edit Case Details", width="large")
def _render_edit_case_form(case_id: str, case_mgr: CaseManager, user_id: str):
    """Form to edit an existing case."""
    
    case = case_mgr.get_case(case_id)
    if not case:
        st.error("Case not found")
        if st.button("Close"):
            st.session_state['show_edit_case_form'] = False
            st.session_state['show_case_modal'] = False
            st.rerun()
        return

    with st.form("edit_case_form"):
        st.markdown("### Edit Case Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            case_number = st.text_input(
                "Case Number *",
                value=case.get('case_number', ''),
                placeholder="e.g., HC Petition No. 123 of 2024",
                key="edit_case_number"
            )
            
            # Get current index for selectboxes
            case_types = ['civil', 'criminal', 'commercial', 'land', 'family', 'constitutional', 'employment', 'other']
            current_type = case.get('case_type', 'civil')
            type_index = case_types.index(current_type) if current_type in case_types else 0
            
            case_type = st.selectbox(
                "Case Type *",
                options=case_types,
                index=type_index,
                format_func=lambda x: x.title(),
                key="edit_case_type"
            )
            
            court_levels = ['magistrate', 'high_court', 'court_of_appeal', 'supreme_court', 'tribunal']
            current_level = case.get('court_level', 'high_court')
            level_index = court_levels.index(current_level) if current_level in court_levels else 1
            
            court_level = st.selectbox(
                "Court Level *",
                options=court_levels,
                index=level_index,
                format_func=lambda x: x.replace('_', ' ').title(),
                key="edit_court_level"
            )
        
        with col2:
            court_location = st.text_input(
                "Court Location",
                value=case.get('court_location', ''),
                placeholder="e.g., Milimani, Nairobi",
                key="edit_court_location"
            )
            
            filing_date_val = case.get('filing_date')
            if filing_date_val:
                try:
                    filing_date_val = datetime.fromisoformat(filing_date_val).date()
                except ValueError:
                    filing_date_val = None
            
            filing_date = st.date_input(
                "Filing Date",
                value=filing_date_val,
                key="edit_filing_date"
            )
            
            stages = ['filing', 'pleadings', 'interlocutory', 'discovery', 'hearing', 'judgment', 'appeal', 'concluded']
            current_stage = case.get('current_stage', 'filing')
            stage_index = stages.index(current_stage) if current_stage in stages else 0
            
            current_stage_sel = st.selectbox(
                "Current Stage",
                options=stages,
                index=stage_index,
                format_func=lambda x: x.title(),
                key="edit_stage"
            )
        
        st.markdown("### Parties")
        
        plaintiff = st.text_area(
            "Plaintiff/Petitioner",
            value=case.get('plaintiff_petitioner', ''),
            placeholder="Enter plaintiff or petitioner name(s)",
            key="edit_plaintiff",
            height=80
        )
        
        defendant = st.text_area(
            "Defendant/Respondent",
            value=case.get('defendant_respondent', ''),
            placeholder="Enter defendant or respondent name(s)",
            key="edit_defendant",
            height=80
        )
        
        col1, col2 = st.columns(2)
        with col1:
            plaintiff_advocate = st.text_input(
                "Plaintiff's Advocate",
                value=case.get('plaintiff_advocate', ''),
                key="edit_plaintiff_advocate"
            )
        
        with col2:
            defendant_advocate = st.text_input(
                "Defendant's Advocate",
                value=case.get('defendant_advocate', ''),
                key="edit_defendant_advocate"
            )
        
        # Status
        st.markdown("### Status")
        status_options = ['active', 'pending', 'concluded', 'withdrawn', 'settled']
        current_status = case.get('case_status', 'active')
        status_index = status_options.index(current_status) if current_status in status_options else 0
        
        case_status = st.selectbox(
            "Case Status",
            options=status_options,
            index=status_index,
            format_func=lambda x: x.upper(),
            key="edit_case_status"
        )
        
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
        
        if submitted:
            # Validation
            if not case_number or not case_number.strip():
                st.error("❌ Case Number is required")
            elif not case_type:
                st.error("❌ Case Type is required")
            else:
                updates = {
                    'case_number': case_number.strip(),
                    'case_type': case_type,
                    'court_level': court_level,
                    'court_location': court_location if court_location else None,
                    'filing_date': filing_date.isoformat() if filing_date else None,
                    'current_stage': current_stage_sel,
                    'plaintiff_petitioner': plaintiff if plaintiff else None,
                    'defendant_respondent': defendant if defendant else None,
                    'plaintiff_advocate': plaintiff_advocate if plaintiff_advocate else None,
                    'defendant_advocate': defendant_advocate if defendant_advocate else None,
                    'case_status': case_status
                }
                
                result = case_mgr.update_case(case_id, updates)
                
                if result:
                    st.success("✅ Case updated successfully!")
                    st.session_state['show_edit_case_form'] = False
                    st.session_state['show_case_modal'] = True
                    import time
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Failed to update case. Please try again.")

    if st.button("Cancel", key="cancel_edit_case", use_container_width=True):
        st.session_state['show_edit_case_form'] = False
        st.session_state['show_case_modal'] = True # Go back to details
        st.rerun()


@st.dialog("Case Details", width="large")
def _render_case_modal(case: Dict[str, Any], case_mgr: CaseManager, user_id: str):
    """Render case details in a modal dialog."""
    
    # Case header
    case_number = case.get('case_number', 'No Case Number')
    case_type = case.get('case_type', '').title()
    court = case.get('court_level', '').replace('_', ' ').title()
    location = case.get('court_location', 'Location TBD')
    status = case.get('case_status', 'active')
    
    status_color = {
        'active': '#4ADE80',
        'pending': '#F59E0B',
        'concluded': '#9BA1B0'
    }.get(status, '#9BA1B0')
    
    st.markdown(f"""
    <div style="margin-bottom: 20px;">
        <div style="font-size: 22px; font-weight: 600; color: #FFFFFF; margin-bottom: 8px;">{case_number}</div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="font-size: 14px; color: #9BA1B0;">{case_type} • {court} - {location}</div>
            <span style="display: inline-flex; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; background: rgba({int(status_color[1:3], 16)}, {int(status_color[3:5], 16)}, {int(status_color[5:7], 16)}, 0.15); color: {status_color};">
                {status.upper()}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # AI Analysis button - Centered
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    analysis_error = None
    
    with col2:
        if st.button("✏️ Edit Case", use_container_width=True, key="edit_case_btn"):
             st.session_state['show_edit_case_form'] = True
             st.session_state['show_case_modal'] = False
             st.rerun()
    with col3:
        if st.button("AI Analysis", use_container_width=True, type="primary", key="ai_analysis_modal_btn"):
            with st.spinner("Analyzing case..."):
                import time
                time.sleep(0.5)  # Brief delay for UX
                analysis = case_mgr.analyze_case(case['id'])
                if 'error' not in analysis:
                    st.session_state['case_analysis'] = analysis
                    st.rerun()
                else:
                    analysis_error = analysis.get('error', 'Unknown error')
    
    # Show error if occurred (Outside columns for full width)
    if analysis_error:
        st.error(f"Analysis failed: {analysis_error}")
    
    # Show AI analysis if available - Centered 90% width (Widened from 80%)
    if st.session_state.get('case_analysis'):
        analysis = st.session_state['case_analysis']
        strength = analysis.get('risk_assessment', {}).get('strength', 'N/A')
        
        col1, col2, col3 = st.columns([0.5, 9, 0.5])
        with col2:
            st.markdown(f"""
            <div style="background: rgba(75, 158, 255, 0.08); border-left: 4px solid #4B9EFF; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                <div style="font-weight: 600; color: #4B9EFF; margin-bottom: 8px; font-size: 14px;">AI Case Analysis</div>
                <div style="color: #FFFFFF; margin-bottom: 12px; font-size: 14px;">{analysis.get('summary', 'No summary available')}</div>
                <div style="display: flex; gap: 16px; font-size: 13px;">
                    <div><strong style="color: #9BA1B0;">Case Strength:</strong> <span style="color: #4B9EFF; font-weight: 600;">{strength}%</span></div>
                </div>
            """, unsafe_allow_html=True)
            
            # Show strategies if available
            strategies = analysis.get('strategies', [])
            if strategies:
                st.markdown("<div style='margin-top: 12px;'><strong style='color: #9BA1B0; font-size: 13px;'>Strategy Suggestions:</strong></div>", unsafe_allow_html=True)
                for strategy in strategies[:3]:
                    st.markdown(f"<div style='color: #FFFFFF; font-size: 13px; margin-left: 12px;'>• {strategy}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Tabs for different views - with text only labels
    tabs = st.tabs(["Overview", "Timeline", "Tasks", "Notes"])
    
    with tabs[0]:
        _render_overview_tab(case, case_mgr)
    
    with tabs[1]:
        _render_timeline_tab(case['id'], case_mgr, user_id)
    
    with tabs[2]:
        _render_tasks_tab(case['id'], case_mgr, user_id)
    
    with tabs[3]:
        _render_notes_tab(case['id'], case_mgr, user_id)
    
    # Close button
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    if st.button("Close", use_container_width=True, type="primary", key="close_case_modal"):
        st.session_state['show_case_modal'] = False
        st.session_state['selected_case_id'] = None
        st.session_state['case_analysis'] = None
        st.rerun()


def _render_case_view(case: Dict[str, Any], case_mgr: CaseManager, user_id: str):
    """Render detailed case view with tabs (DEPRECATED - use modal instead)."""
    # This function is kept for backward compatibility but not used
    pass


def _render_overview_tab(case: Dict[str, Any], case_mgr: CaseManager):
    """Render case overview with stats."""
    
    # Stats
    tasks = case_mgr.get_case_tasks(case['id'])
    events = case_mgr.get_case_timeline(case['id'])
    documents = case_mgr.get_case_documents(case['id'])
    
    pending_tasks = [t for t in tasks if t['status'] == 'pending']
    overdue_tasks = case_mgr.get_overdue_tasks(case['id'])
    
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(events)}</div>
            <div class="stat-label">Events</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[1]:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(pending_tasks)}</div>
            <div class="stat-label">Pending Tasks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[2]:
        color = "#EF4444" if overdue_tasks else "#4ADE80"
        st.markdown(f"""
        <div class="stat-box" style="border-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.3);">
            <div class="stat-number" style="color: {color};">{len(overdue_tasks)}</div>
            <div class="stat-label">Overdue</div>
        </div>
        """, unsafe_allow_html=True)
    
    with cols[3]:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-number">{len(documents)}</div>
            <div class="stat-label">Documents</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 24px 0;'></div>", unsafe_allow_html=True)
    
    # Case details
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Parties")
        st.markdown(f"""
        <div style="background: #1A1D24; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="font-size: 12px; color: #9BA1B0; margin-bottom: 6px;">PLAINTIFF/PETITIONER</div>
            <div style="color: #FFFFFF;">{case.get('plaintiff_petitioner', 'Not set')}</div>
            <div style="font-size: 13px; color: #9BA1B0; margin-top: 6px;">Advocate: {case.get('plaintiff_advocate', 'Not set')}</div>
        </div>
        <div style="background: #1A1D24; border-radius: 8px; padding: 16px;">
            <div style="font-size: 12px; color: #9BA1B0; margin-bottom: 6px;">DEFENDANT/RESPONDENT</div>
            <div style="color: #FFFFFF;">{case.get('defendant_respondent', 'Not set')}</div>
            <div style="font-size: 13px; color: #9BA1B0; margin-top: 6px;">Advocate: {case.get('defendant_advocate', 'Not set')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Case Information")
        status_color = "#4ADE80" if case['case_status'] == 'active' else "#9BA1B0"
        filing_date = case.get('filing_date', 'Not set')
        if filing_date and filing_date != 'Not set':
            filing_date = datetime.fromisoformat(filing_date).strftime("%B %d, %Y")
        
        st.markdown(f"""
        <div style="background: #1A1D24; border-radius: 8px; padding: 16px;">
            <div style="margin-bottom: 16px;">
                <div style="font-size: 12px; color: #9BA1B0; margin-bottom: 6px;">STATUS</div>
                <div style="color: {status_color}; font-weight: 600;">{case['case_status'].upper()}</div>
            </div>
            <div style="margin-bottom: 16px;">
                <div style="font-size: 12px; color: #9BA1B0; margin-bottom: 6px;">CURRENT STAGE</div>
                <div style="color: #FFFFFF;">{case.get('current_stage', 'Not set').title()}</div>
            </div>
            <div>
                <div style="font-size: 12px; color: #9BA1B0; margin-bottom: 6px;">FILING DATE</div>
                <div style="color: #FFFFFF;">{filing_date}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_timeline_tab(case_id: str, case_mgr: CaseManager, user_id: str):
    """Render case timeline."""
    
    st.markdown("### Case Timeline")
    
    # Add event button
    if st.button("Add Event", key="add_event_btn"):
        st.session_state['show_add_event'] = True
    
    if st.session_state.get('show_add_event'):
        _render_add_event_form(case_id, case_mgr, user_id)
    
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    # Get events
    events = case_mgr.get_case_timeline(case_id)
    
    if events:
        for event in events:
            event_date_str = event.get('event_date')
            if event_date_str:
                try:
                    event_date_obj = datetime.fromisoformat(event_date_str).date() if isinstance(event_date_str, str) else event_date_str
                    event_display_date = event_date_obj.strftime("%b %d, %Y")
                except:
                    event_display_date = str(event_date_str)
            else:
                event_display_date = "Date TBD"
            
            event_type_color = {
                'filing': '#4B9EFF',
                'hearing': '#F59E0B',
                'ruling': '#4ADE80',
                'judgment': '#9333EA'
            }.get(event.get('event_type'), '#9BA1B0')
            
            st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-dot" style="background: {event_type_color};"></div>
                <div style="background: #1A1D24; border-radius: 8px; padding: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                        <div style="font-weight: 600; color: #FFFFFF;">{event.get('event_title', 'Untitled Event')}</div>
                        <div style="font-size: 13px; color: #9BA1B0;">{event_display_date}</div>
                    </div>
                    <div style="font-size: 13px; color: #9BA1B0; margin-bottom: 6px;">{event.get('event_type', '').title()}</div>
                    <div style="font-size: 14px; color: #FFFFFF;">{event.get('event_description', '')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No events recorded yet. Add your first event to start tracking.")


def _render_add_event_form(case_id: str, case_mgr: CaseManager, user_id: str):
    """Form to add a new event."""
    with st.form("add_event_form", clear_on_submit=True):
        st.markdown("#### New Event")
        
        event_title = st.text_input("Event Title *", placeholder="e.g., Filing of Defence")
        
        col1, col2 = st.columns(2)
        with col1:
            event_type = st.selectbox(
                "Type *",
                options=['filing', 'pleading', 'hearing', 'ruling', 'application', 'mention', 'judgment', 'order', 'settlement', 'other'],
                format_func=lambda x: x.title()
            )
        
        with col2:
            event_date = st.date_input("Date *", value=date.today())
        
        event_description = st.text_area("Description", height=100, placeholder="Event details...")
        
        col1, col2 = st.columns(2)
        with col1:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
            if cancel:
                st.session_state['show_add_event'] = False
                st.rerun()
        
        with col2:
            submitted = st.form_submit_button("Add Event", type="primary", use_container_width=True)
            if submitted:
                if not event_title or not event_title.strip():
                    st.error("❌ Event title is required")
                elif not event_type:
                    st.error("❌ Event type is required")
                else:
                    event_data = {
                        'event_title': event_title.strip(),
                        'event_type': event_type,
                        'event_date': event_date.isoformat(),
                        'event_description': event_description.strip() if event_description else ''
                    }
                    
                    try:
                        result = case_mgr.add_event(case_id, event_data, user_id)
                        if result:
                            st.success("✅ Event added successfully!")
                            st.session_state['show_add_event'] = False
                            import time
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Failed to create event. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Error creating event: {str(e)}")
                        import logging
                        logging.error(f"Event creation error: {e}", exc_info=True)


def _render_tasks_tab(case_id: str, case_mgr: CaseManager, user_id: str):
    """Render tasks management."""
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Tasks & Deadlines")
    
    with col2:
        if st.button("Add Task", key="add_task_btn", use_container_width=True):
            st.session_state['show_add_task'] = True
    
    if st.session_state.get('show_add_task'):
        _render_add_task_form(case_id, case_mgr, user_id)
    
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    # Get tasks
    tasks = case_mgr.get_case_tasks(case_id)
    
    if tasks:
        # Group by status
        pending = [t for t in tasks if t['status'] == 'pending']
        in_progress = [t for t in tasks if t['status'] == 'in_progress']
        completed = [t for t in tasks if t['status'] == 'completed']
        
        for task_list, title in [(pending, "Pending"), (in_progress, "In Progress"), (completed, "Completed")]:
            if task_list:
                st.markdown(f"**{title}** ({len(task_list)})")
                for task in task_list:
                    _render_task_card(task, case_mgr, user_id)
                st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
    else:
        st.info("No tasks yet. Add a task to track deadlines.")


def _render_task_card(task: Dict[str, Any], case_mgr: CaseManager, user_id: str):
    """Render a single task card."""
    priority = task.get('priority', 'medium')
    status = task.get('status', 'pending')
    due_date = task.get('due_date')
    
    if due_date:
        due_date_obj = datetime.fromisoformat(due_date).date() if isinstance(due_date, str) else due_date
        due_str = due_date_obj.strftime("%b %d, %Y")
        days_until = (due_date_obj - date.today()).days
        due_color = "#EF4444" if days_until < 0 else ("#F59E0B" if days_until <= 3 else "#9BA1B0")
    else:
        due_str = "No deadline"
        due_color = "#9BA1B0"
    
    st.markdown(f"""
    <div class="task-card {priority} {status}">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
            <div style="font-weight: 600; color: #FFFFFF; flex: 1;">{task.get('title', 'Untitled Task')}</div>
            <span class="priority-badge priority-{priority}">{priority}</span>
        </div>
        <div style="font-size: 13px; color: #9BA1B0; margin-bottom: 8px;">{task.get('description', '')}</div>
        <div style="font-size: 13px; color: {due_color};">📅 {due_str}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick complete button
    if status != 'completed':
        if st.button(f"✓ Complete", key=f"complete_{task['id']}", type="secondary"):
            case_mgr.complete_task(task['id'], user_id)
            st.rerun()


def _render_add_task_form(case_id: str, case_mgr: CaseManager, user_id: str):
    """Form to add a new task."""
    with st.form("add_task_form", clear_on_submit=True):
        st.markdown("#### New Task")
        
        title = st.text_input("Task Title *", placeholder="e.g., File defence papers")
        description = st.text_area("Description", height=80, placeholder="Task details...")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            task_type = st.selectbox(
                "Type",
                options=['filing', 'hearing_prep', 'research', 'client_meeting', 'evidence_gathering', 'drafting', 'submission', 'other'],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        with col2:
            priority = st.selectbox("Priority", options=['low', 'medium', 'high', 'urgent'])
        
        with col3:
            due_date = st.date_input("Due Date", value=None)
        
        col1, col2 = st.columns(2)
        with col1:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
            if cancel:
                st.session_state['show_add_task'] = False
                st.rerun()
        
        with col2:
            submitted = st.form_submit_button("Add Task", type="primary", use_container_width=True)
            if submitted:
                if not title or not title.strip():
                    st.error("❌ Task title is required")
                else:
                    task_data = {
                        'title': title.strip(),
                        'description': description.strip() if description else '',
                        'task_type': task_type,
                        'priority': priority,
                        'due_date': due_date.isoformat() if due_date else None,
                        'status': 'pending'
                    }
                    
                    try:
                        result = case_mgr.create_task(case_id, task_data, user_id)
                        if result:
                            st.success("✅ Task added successfully!")
                            st.session_state['show_add_task'] = False
                            import time
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Failed to create task. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Error creating task: {str(e)}")
                        import logging
                        logging.error(f"Task creation error: {e}", exc_info=True)


def _render_notes_tab(case_id: str, case_mgr: CaseManager, user_id: str):
    """Render case notes."""
    st.markdown("### Case Notes")
    
    # Add note form
    with st.form("add_note_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            note_text = st.text_area("Add a note", height=100, placeholder="Strategy notes, observations, legal issues...")
        
        with col2:
            note_type = st.selectbox(
                "Type",
                options=['general', 'strategy', 'research', 'client', 'court_observation', 'legal_issue'],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        submitted = st.form_submit_button("Add Note", type="primary")
        if submitted:
            if not note_text or not note_text.strip():
                st.error("❌ Note text is required")
            else:
                try:
                    result = case_mgr.add_note(case_id, note_text.strip(), note_type, user_id)
                    if result:
                        st.success("✅ Note added successfully!")
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Failed to add note. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error adding note: {str(e)}")
                    import logging
                    logging.error(f"Note creation error: {e}", exc_info=True)
    
    st.markdown("<div style='margin: 24px 0;'></div>", unsafe_allow_html=True)
    
    # Display notes
    notes = case_mgr.get_case_notes(case_id)
    
    if notes:
        for note in notes:
            created_at = note.get('created_at')
            if created_at:
                try:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_ago = (datetime.now(created_dt.tzinfo) - created_dt).days
                    time_str = f"{time_ago}d ago" if time_ago > 0 else "Today"
                except:
                    time_str = "Recently"
            else:
                time_str = "Recently"
            
            note_type_color = {
                'strategy': '#4B9EFF',
                'legal_issue': '#EF4444',
                'research': '#9333EA'
            }.get(note.get('note_type'), '#9BA1B0')
            
            st.markdown(f"""
            <div style="background: #1A1D24; border-left: 4px solid {note_type_color}; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: {note_type_color}; text-transform: uppercase; font-weight: 600;">{note.get('note_type', 'general').replace('_', ' ')}</span>
                    <span style="font-size: 12px; color: #9BA1B0;">{time_str}</span>
                </div>
                <div style="color: #FFFFFF; line-height: 1.6;">{note.get('note_text', '')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No notes yet. Add your first note above.")

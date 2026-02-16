"""
Organization Dashboard - Admin interface for managing team members and subscription
Styled to match SmartClause app aesthetics with dark theme
"""

import streamlit as st
from typing import Optional, Dict, List
from subscription_manager import SubscriptionManager, PRICING
from database import DatabaseManager


def render_organization_dashboard():
    """Main organization dashboard for admins/owners"""
    
    # Custom styling matching app theme
    st.markdown("""
    <style>
    /* Override Streamlit defaults with app theme */
    .stApp {
        background-color: #0A0B0D;
    }
    
    /* Custom card styling */
    .org-card {
        background: #1A1D24;
        border: 1px solid #252930;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }
    
    .org-card-title {
        font-size: 18px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 16px;
    }
    
    .org-stat {
        background: #0A0B0D;
        border: 1px solid #252930;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    
    .org-stat-value {
        font-size: 32px;
        font-weight: 700;
        color: #4B9EFF;
        margin-bottom: 4px;
    }
    
    .org-stat-label {
        font-size: 14px;
        color: #9BA1B0;
    }
    
    /* Member list styling */
    .member-item {
        background: #0A0B0D;
        border: 1px solid #252930;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .member-info {
        flex: 1;
    }
    
    .member-name {
        font-size: 16px;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 4px;
    }
    
    .member-email {
        font-size: 14px;
        color: #9BA1B0;
    }
    
    .member-role {
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        background: #252930;
        color: #9BA1B0;
    }
    
    .member-role.owner {
        background: rgba(75, 158, 255, 0.15);
        color: #4B9EFF;
    }
    
    .member-role.admin {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
    }
    
    /* Usage chart styling */
    .usage-bar {
        background: #252930;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 8px;
    }
    
    .usage-fill {
        background: linear-gradient(90deg, #4B9EFF 0%, #5BABFF 100%);
        height: 100%;
        transition: width 0.3s ease;
    }
    
    .usage-fill.warning {
        background: linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%);
    }
    
    .usage-fill.danger {
        background: linear-gradient(90deg, #EF4444 0%, #F87171 100%);
    }
    
    /* Button overrides */
    .stButton > button {
        background-color: #4B9EFF !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #5BABFF !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(75, 158, 255, 0.3) !important;
    }
    
    .stButton > button[kind="secondary"] {
        background-color: #252930 !important;
        color: #9BA1B0 !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #2C3039 !important;
        color: #FFFFFF !important;
    }
    
    /* Table styling */
    .dataframe {
        background-color: #1A1D24 !important;
        color: #FFFFFF !important;
        border: 1px solid #252930 !important;
        border-radius: 8px !important;
    }
    
    .dataframe th {
        background-color: #252930 !important;
        color: #9BA1B0 !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    
    .dataframe td {
        padding: 12px !important;
        color: #FFFFFF !important;
        border-color: #252930 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get user info
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Please log in to access organization dashboard")
        return
    
    # Initialize managers
    db = DatabaseManager()
    db.set_user(user_id)
    sub_manager = SubscriptionManager(db)
    
    # Get organization info
    org = sub_manager.get_organization_info(user_id)
    
    if not org:
        st.warning("You are not part of an organization. Please contact support.")
        return
    
    # Check if user has admin rights
    user_role = org.get('organization_members', [{}])[0].get('role', 'member')
    if user_role not in ['owner', 'admin']:
        st.warning("⚠️ You don't have permission to access the organization dashboard")
        st.info("Only organization owners and admins can manage organization settings")
        return
    
    # Page Header
    st.markdown(f"""
    <div style='margin-bottom: 32px;'>
        <div style='font-size: 32px; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;'>
            🏢 Organization Dashboard
        </div>
        <div style='font-size: 16px; color: #9BA1B0;'>
            {org['name']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Subscription Overview
    subscription = sub_manager.get_organization_subscription(org['id']) if org else None
    
    if subscription:
        render_subscription_overview(subscription, org)
    else:
        st.warning("No active subscription found for your organization")
    
    # Usage Statistics
    if user_role in ['owner', 'admin']:
        render_usage_statistics(sub_manager, org, user_id)
    
    # Team Members
    if user_role in ['owner', 'admin']:
        render_team_members(sub_manager, org, user_id, user_role)


def render_subscription_overview(subscription: Dict, org: Dict):
    """Render subscription details card"""
    
    tier = subscription['subscription_tier']
    tier_config = PRICING.get(tier, {})
    
    # Calculate days remaining
    from datetime import datetime
    try:
        end_date = datetime.fromisoformat(subscription['current_period_end'].replace('Z', '+00:00'))
        now = datetime.now(end_date.tzinfo)
        days_remaining = max(0, (end_date - now).days)
    except:
        days_remaining = 0
    
    st.markdown("""
    <div class="org-card">
        <div class="org-card-title">📊 Subscription Overview</div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="org-stat">
            <div class="org-stat-value">{tier.title()}</div>
            <div class="org-stat-label">Plan</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="org-stat">
            <div class="org-stat-value">{subscription['seats_used']}/{subscription['seats_purchased']}</div>
            <div class="org-stat-label">Seats Used</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        docs_limit = tier_config.get('documents_per_month')
        limit_text = "Unlimited" if docs_limit is None else str(docs_limit)
        st.markdown(f"""
        <div class="org-stat">
            <div class="org-stat-value">{limit_text}</div>
            <div class="org-stat-label">Docs/User/Month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="org-stat">
            <div class="org-stat-value">{days_remaining}</div>
            <div class="org-stat-label">Days Remaining</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Subscription actions
    if subscription['status'] == 'active':
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add More Seats", key="add_seats", use_container_width=True):
                st.session_state.show_add_seats_modal = True
                st.rerun()
        with col2:
            if st.button("⬆️ Upgrade Plan", key="upgrade_plan", use_container_width=True):
                from auth import update_query_params
                update_query_params({"view": "pricing"})
                st.rerun()


def render_usage_statistics(sub_manager: SubscriptionManager, org: Dict, user_id: str):
    """Render organization usage statistics"""
    
    usage = sub_manager.get_organization_usage(user_id)
    
    if not usage:
        return
    
    st.markdown("""
    <div class="org-card">
        <div class="org-card-title">📈 Usage Statistics (Current Period)</div>
    """, unsafe_allow_html=True)
    
    total_docs = usage.get('total_documents', 0)
    
    st.markdown(f"""
    <div style='font-size: 24px; font-weight: 700; color: #4B9EFF; margin-bottom: 16px;'>
        {total_docs} documents generated
    </div>
    """, unsafe_allow_html=True)
    
    # Top users
    if usage.get('documents_by_user'):
        st.markdown("<div style='font-size: 16px; font-weight: 600; color: #FFFFFF; margin-top: 24px; margin-bottom: 12px;'>Top Contributors</div>", unsafe_allow_html=True)
        
        for user_usage in usage['documents_by_user'][:5]:
            name = user_usage.get('full_name') or user_usage.get('email', 'Unknown')
            count = user_usage.get('documents_created', 0)
            
            st.markdown(f"""
            <div style='display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #252930;'>
                <span style='color: #FFFFFF;'>{name}</span>
                <span style='color: #4B9EFF; font-weight: 600;'>{count} docs</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_team_members(sub_manager: SubscriptionManager, org: Dict, current_user_id: str, user_role: str):
    """Render team members list"""
    
    members = sub_manager.get_organization_members(current_user_id)
    
    st.markdown("""
    <div class="org-card">
        <div class="org-card-title">👥 Team Members</div>
    """, unsafe_allow_html=True)
    
    if not members:
        st.info("No team members found")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    for member in members:
        user_data = member.get('users') or {}
        email = user_data.get('email', 'Unknown')
        name = user_data.get('raw_user_meta_data', {}).get('full_name', email.split('@')[0])
        role = member.get('role', 'member')
        status = member.get('status', 'active')
        
        status_icon = "✅" if status == 'active' else "⏸️"
        
        st.markdown(f"""
        <div class="member-item">
            <div class="member-info">
                <div class="member-name">{status_icon} {name}</div>
                <div class="member-email">{email}</div>
            </div>
            <div class="member-role {role}">{role.upper()}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Add member button (only for owners/admins)
    if user_role in ['owner', 'admin']:
        if st.button("➕ Invite Team Member", key="invite_member", use_container_width=True):
            st.info("Coming soon: Email invitations for team members")


if __name__ == "__main__":
    render_organization_dashboard()

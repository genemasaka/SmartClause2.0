"""
Organization Dashboard - Admin interface for managing team members and subscription
Styled to match SmartClause app aesthetics with dark theme
"""

import streamlit as st
import secrets
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from subscription_manager import SubscriptionManager, PRICING
from organization_manager import get_user_role_from_org
from database import DatabaseManager

from analytics import Analytics
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Invite helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_admin_supabase_client():
    """
    Return a Supabase client initialised with the Service Role key so we can
    call auth.admin.invite_user_by_email().
    Returns None if SUPABASE_SERVICE_KEY is not configured.
    """
    from supabase import create_client
    url = os.getenv("SUPABASE_URL", "").strip()
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    if not url or not service_key:
        return None
    try:
        return create_client(url, service_key)
    except Exception:
        return None


def _send_invite_email(email: str, org_name: str, role: str, invite_token: str) -> bool:
    """
    Try to send an invite via Supabase's admin invite API.
    Returns True on success, False if we should fall back to a manual link.
    """
    admin_client = _get_admin_supabase_client()
    if not admin_client:
        return False
    try:
        app_url = os.getenv("APP_URL", "http://localhost:8501").rstrip("/")
        redirect_url = f"{app_url}/?invite_token={invite_token}"
        admin_client.auth.admin.invite_user_by_email(
            email,
            options={"redirect_to": redirect_url, "data": {"org_invite": invite_token}},
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send invite email to {email}: {e}")
        return False


def _invite_link(invite_token: str) -> str:
    app_url = os.getenv("APP_URL", "http://localhost:8501").rstrip("/")
    return f"{app_url}/?invite_token={invite_token}"


# ──────────────────────────────────────────────────────────────────────────────
# Invite dialog
# ──────────────────────────────────────────────────────────────────────────────

@st.dialog("Invite Team Member", width="large")
def invite_member_dialog(org: Dict, org_id: str, current_user_id: str, db: DatabaseManager):
    """Modal form to invite a new team member."""

    # ── Determine subscription tier & seat limit ──────────────────────────────
    # Primary: organization_subscriptions table row
    subscription = db.get_organization_subscription(org_id)

    # Fallback: read tier directly from the organizations table
    org_tier = org.get("subscription_tier", "trial")

    TEAM_TIERS = {"team", "enterprise"}
    if org_tier not in TEAM_TIERS and (not subscription or subscription.get("subscription_tier") not in TEAM_TIERS):
        st.error("⚠️ Team invitations are only available on the Team or Enterprise plan.")
        if st.button("Close"):
            st.rerun()
        return

    # Resolve seat numbers — use subscription row if present, else count active members
    if subscription:
        seats_purchased = subscription.get("seats_purchased", 10)
        seats_used = subscription.get("seats_used", 1)
    else:
        # No subscription row: count active members directly from the DB
        try:
            members_result = (
                db.client.table("organization_members")
                .select("id", count="exact")
                .eq("organization_id", org_id)
                .eq("status", "active")
                .execute()
            )
            seats_used = members_result.count or 1
        except Exception:
            seats_used = 1
        seats_purchased = 10  # sensible default

    seats_available = seats_purchased - seats_used

    # ── Seat availability banner ──────────────────────────────────────────────
    if seats_available <= 0:
        st.error(
            f"⚠️ All **{seats_purchased}** seats are in use. "
            "Add more seats from the Subscription Overview before inviting members."
        )
        if st.button("Close"):
            st.rerun()
        return

    st.success(f"✅ {seats_available} of {seats_purchased} seat(s) available")

    # ── Invite form ───────────────────────────────────────────────────────────
    email = st.text_input(
        "Email address",
        placeholder="colleague@example.com",
        help="The person will receive an invitation email.",
    )
    role = st.selectbox(
        "Role",
        ["member", "admin"],
        format_func=lambda r: {
            "member": "Member – can create documents",
            "admin": "Admin – can manage team",
        }.get(r, r),
    )

    col_cancel, col_send = st.columns(2)
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with col_send:
        if st.button("Send Invitation", type="primary", use_container_width=True):
            
            if not email or "@" not in email:
                st.error("Please enter a valid email address.")
                return

            # Check for duplicate pending invite
            pending = db.get_pending_invitations(org_id)
            if any(i["invited_email"].lower() == email.lower() for i in pending):
                st.warning("An invitation is already pending for this email.")
                return

            # Generate secure token and expiry (7 days)
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()

            invite = db.create_organization_invitation(
                organization_id=org_id,
                invited_email=email.lower().strip(),
                role=role,
                invited_by=current_user_id,
                token=token,
                expires_at=expires_at,
            )

            if invite is None:
                st.warning(
                    "⚠️ Could not save the invitation record "
                    "(the `organization_invitations` table may not exist yet — "
                    "see setup instructions). Share the link below manually:"
                )
                st.code(_invite_link(token), language=None)
            else:
                sent = _send_invite_email(email, org.get("name", "SmartClause"), role, token)
                if sent:
                    Analytics().track_event("team_invite_sent", {"role": role, "email_domain": email.split('@')[-1]})
                    st.success(f"✅ Invitation email sent to **{email}**!")
                else:
                    st.info(
                        "Automatic email is not configured. "
                        "Copy and share this invite link with your team member:"
                    )
                    st.code(_invite_link(token), language=None)

            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Main dashboard
# ──────────────────────────────────────────────────────────────────────────────

def render_organization_dashboard():
    """Main organization dashboard for admins/owners"""

    st.markdown("""
    <style>
    .stApp { background-color: #0A0B0D; }

    .org-card {
        padding: 0;
        margin-bottom: 24px;
    }
    .org-card-title {
        font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;
    }
    .org-stat {
        background: #0A0B0D; border: 1px solid #252930;
        border-radius: 8px; padding: 16px; text-align: center;
    }
    .org-stat-value { font-size: 32px; font-weight: 700; color: #4B9EFF; margin-bottom: 4px; }
    .org-stat-label { font-size: 14px; color: #9BA1B0; }

    .member-item {
        background: #0A0B0D; border: 1px solid #252930;
        border-radius: 8px; padding: 14px 16px; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .member-name  { font-size: 15px; font-weight: 600; color: #FFFFFF; margin-bottom: 2px; }
    .member-email { font-size: 13px; color: #9BA1B0; }
    .member-role  {
        padding: 3px 10px; border-radius: 6px;
        font-size: 11px; font-weight: 600; text-transform: uppercase;
        background: #252930; color: #9BA1B0;
    }
    .member-role.owner { background: rgba(75,158,255,.15); color: #4B9EFF; }
    .member-role.admin { background: rgba(245,158,11,.15);  color: #F59E0B; }

    .invite-item {
        background: rgba(75,158,255,.05); border: 1px dashed #334155;
        border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .invite-email { font-size: 14px; color: #9BA1B0; }
    .invite-badge {
        font-size: 11px; font-weight: 600; color: #4B9EFF;
        background: rgba(75,158,255,.12); padding: 2px 8px; border-radius: 4px;
    }

    .usage-bar  { background:#252930; height:8px; border-radius:4px; overflow:hidden; margin-bottom:8px; }
    .usage-fill { background:linear-gradient(90deg,#4B9EFF,#5BABFF); height:100%; }
    .usage-fill.warning { background:linear-gradient(90deg,#F59E0B,#FBBF24); }
    .usage-fill.danger  { background:linear-gradient(90deg,#EF4444,#F87171); }

    .stButton > button {
        background-color:#4B9EFF !important; color:white !important;
        border:none !important; border-radius:8px !important;
        font-weight:600 !important; transition:all .2s ease !important;
    }
    .stButton > button:hover {
        background-color:#5BABFF !important;
        transform:translateY(-1px);
        box-shadow: 0 4px 12px rgba(75,158,255,.3) !important;
    }
    .stButton > button[kind="secondary"] { background-color:#252930 !important; color:#9BA1B0 !important; }
    .stButton > button[kind="secondary"]:hover { background-color:#2C3039 !important; color:#FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Please log in to access the organization dashboard")
        return

    db = DatabaseManager()
    db.set_user(user_id)
    sub_manager = SubscriptionManager(db)

    org = sub_manager.get_organization_info(user_id)
    if not org:
        st.warning("You are not part of an organization. Please contact support.")
        return

    # Role is looked up by user_id to avoid fragile index-0 ordering assumption
    user_role = get_user_role_from_org(org, user_id)
    if user_role not in ["owner", "admin"]:
        st.warning("⚠️ You don't have permission to access the organization dashboard.")
        st.info("Only organization owners and admins can manage organization settings.")
        return

    # ── Database synchronization ──────────────────────────────────────────
    # Proactively ensure a subscription record exists if the org is on a paid tier
    # This fixes "No active subscription" errors on-the-fly for admins
    org_tier = org.get("subscription_tier", "trial")
    subscription = db.ensure_organization_subscription(org["id"], org_tier)
    
    analytics = Analytics()
    Analytics().track_page_visit("Organization Dashboard")

    # ── Page Header ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='margin-bottom:32px;'>
        <div style='font-size:32px;font-weight:700;color:#FFFFFF;margin-bottom:8px;display:flex;align-items:center;'>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right:12px;color:#4B9EFF;">
                <path d="M7.5 11H4.6C4.03995 11 3.75992 11 3.54601 11.109C3.35785 11.2049 3.20487 11.3578 3.10899 11.546C3 11.7599 3 12.0399 3 12.6V21M16.5 11H19.4C19.9601 11 20.2401 11 20.454 11.109C20.6422 11.2049 20.7951 11.3578 20.891 11.546C21 11.7599 21 12.0399 21 12.6V21M16.5 21V6.2C16.5 5.0799 16.5 4.51984 16.282 4.09202C16.0903 3.71569 15.7843 3.40973 15.408 3.21799C14.9802 3 14.4201 3 13.3 3H10.7C9.57989 3 9.01984 3 8.59202 3.21799C8.21569 3.40973 7.90973 3.71569 7.71799 4.09202C7.5 4.51984 7.5 5.0799 7.5 6.2V21M22 21H2M11 7H13M11 11H13M11 15H13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Organization Dashboard
        </div>
        <div style='font-size:16px;color:#9BA1B0;'>{org['name']}</div>
    </div>
    """, unsafe_allow_html=True)

    if subscription:
        render_subscription_overview(subscription, org)
    else:
        st.warning("No active subscription details available for your organization.")

    render_usage_statistics(sub_manager, org, user_id)
    render_team_members(db, sub_manager, org, user_id, user_role)


# ──────────────────────────────────────────────────────────────────────────────
# Sub-sections
# ──────────────────────────────────────────────────────────────────────────────

def render_subscription_overview(subscription: Dict, org: Dict):
    """Render subscription details card"""
    tier = subscription["subscription_tier"]
    tier_config = PRICING.get(tier, {})
    is_virtual = subscription.get("is_virtual", False)

    try:
        end_date = datetime.fromisoformat(subscription["current_period_end"].replace("Z", "+00:00"))
        days_remaining = max(0, (end_date - datetime.now(end_date.tzinfo)).days)
    except Exception:
        days_remaining = 30 if is_virtual else 0

    st.markdown('''
        <div style="display:flex;align-items:center;margin-bottom:20px;margin-top:24px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right:10px;color:#4B9EFF;">
                <path d="M12 16V21M12 16L18 21M12 16L6 21M21 3V11.2C21 12.8802 21 13.7202 20.673 14.362C20.3854 14.9265 19.9265 15.3854 19.362 15.673C18.7202 16 17.8802 16 16.2 16H7.8C6.11984 16 5.27976 16 4.63803 15.673C4.07354 15.3854 3.6146 14.9265 3.32698 14.362C3 13.7202 3 12.8802 3 11.2V3M8 9V12M12 7V12M16 11V12M22 3H2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div style="font-size:18px;font-weight:700;color:#FFFFFF;">Subscription Overview</div>
        </div>
    ''', unsafe_allow_html=True)

    if is_virtual:
        st.info("ℹ️ Your organization is currently assigned to a managed plan.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="org-stat"><div class="org-stat-value">{tier.title()}</div><div class="org-stat-label">Plan</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="org-stat"><div class="org-stat-value">{subscription["seats_used"]}/{subscription["seats_purchased"]}</div><div class="org-stat-label">Seats Used</div></div>', unsafe_allow_html=True)
    with col3:
        docs_limit = tier_config.get("documents_per_month")
        limit_text = "Unlimited" if docs_limit is None else str(docs_limit)
        st.markdown(f'<div class="org-stat"><div class="org-stat-value">{limit_text}</div><div class="org-stat-label">Docs/User/Month</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="org-stat"><div class="org-stat-value">{days_remaining}</div><div class="org-stat-label">Days Remaining</div></div>', unsafe_allow_html=True)




def render_usage_statistics(sub_manager: SubscriptionManager, org: Dict, user_id: str):
    """Render organization usage statistics"""
    usage = sub_manager.get_organization_usage(user_id)
    if not usage:
        return

    st.markdown('''
        <div style="display:flex;align-items:center;margin-bottom:20px;margin-top:24px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right:10px;color:#4B9EFF;">
                <path d="M21 21H4.6C4.03995 21 3.75992 21 3.54601 20.891C3.35785 20.7951 3.20487 20.6422 3.10899 20.454C3 20.2401 3 19.9601 3 19.4V3M20 8L16.0811 12.1827C15.9326 12.3412 15.8584 12.4204 15.7688 12.4614C15.6897 12.4976 15.6026 12.5125 15.516 12.5047C15.4179 12.4958 15.3215 12.4458 15.1287 12.3457L11.8713 10.6543C11.6785 10.5542 11.5821 10.5042 11.484 10.4953C11.3974 10.4875 11.3103 10.5024 11.2312 10.5386C11.1416 10.5796 11.0674 10.6588 10.9189 10.8173L7 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div style="font-size:18px;font-weight:700;color:#FFFFFF;">Usage Statistics (Current Period)</div>
        </div>
    ''', unsafe_allow_html=True)
    total_docs = usage.get("total_documents", 0)
    st.markdown(f"<div style='font-size:24px;font-weight:700;color:#4B9EFF;margin-bottom:16px;'>{total_docs} documents generated</div>", unsafe_allow_html=True)

    if usage.get("documents_by_user"):
        st.markdown("<div style='font-size:16px;font-weight:600;color:#FFFFFF;margin-top:24px;margin-bottom:12px;'>Top Contributors</div>", unsafe_allow_html=True)
        for user_usage in usage["documents_by_user"][:5]:
            name = user_usage.get("full_name") or user_usage.get("email", "Unknown")
            count = user_usage.get("documents_created", 0)
            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #252930;'><span style='color:#FFFFFF;'>{name}</span><span style='color:#4B9EFF;font-weight:600;'>{count} docs</span></div>", unsafe_allow_html=True)




def render_team_members(
    db: DatabaseManager,
    sub_manager: SubscriptionManager,
    org: Dict,
    current_user_id: str,
    user_role: str,
):
    """Render team members list with invite and remove capabilities."""
    org_id = org["id"]
    members = sub_manager.get_organization_members(current_user_id)
    pending_invites = db.get_pending_invitations(org_id)

    st.markdown('''
        <div style="display:flex;align-items:center;margin-bottom:20px;margin-top:24px;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right:10px;color:#4B9EFF;">
                <path d="M22 21V19C22 17.1362 20.7252 15.5701 19 15.126M15.5 3.29076C16.9659 3.88415 18 5.32131 18 7C18 8.67869 16.9659 10.1159 15.5 10.7092M17 21C17 19.1362 17 18.2044 16.6955 17.4693C16.2895 16.4892 15.5108 15.7105 14.5307 15.3045C13.7956 15 12.8638 15 11 15H8C6.13623 15 5.20435 15 4.46927 15.3045C3.48915 15.7105 2.71046 16.4892 2.30448 17.4693C2 18.2044 2 19.1362 2 21M13.5 7C13.5 9.20914 11.7091 11 9.5 11C7.29086 11 5.5 9.20914 5.5 7C5.5 4.79086 7.29086 3 9.5 3C11.7091 3 13.5 4.79086 13.5 7Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div style="font-size:18px;font-weight:700;color:#FFFFFF;">Team Members</div>
        </div>
    ''', unsafe_allow_html=True)

    # ── Active members ──
    if not members:
        st.info("No team members found.")
    else:
        # Build a lookup map: user_id -> {email, name} from session state for current user
        current_user_email = st.session_state.get("user_email", "")
        current_user_name = st.session_state.get("user_name", "") or (current_user_email.split("@")[0] if current_user_email else "")

        # Fetch accurate metadata for all team members via Admin API
        uids_to_fetch = [m.get("user_id") for m in members if m.get("user_id")]
        users_meta = db.get_users_metadata(uids_to_fetch) if uids_to_fetch else {}

        for member in members:
            user_data = member.get("users") or {}
            uid = member.get("user_id", "")
            role = member.get("role", "member")
            status = member.get("status", "active")
            status_icon = "✅" if status == "active" else "⏸️"
            is_self = uid == current_user_id
            is_owner = role == "owner"

            # Resolve display info from `users_meta`
            meta = users_meta.get(uid, {})
            
            if is_self and current_user_email:
                email = current_user_email
                name = current_user_name or current_user_email.split("@")[0]
            else:
                email = meta.get("email") or user_data.get("email") or member.get("email") or ""
                raw_meta = user_data.get("raw_user_meta_data") or {}
                name = meta.get("full_name") or raw_meta.get("full_name") or raw_meta.get("name") or ""
                
                if not email and not name:
                    # Last resort: show a shortened user ID
                    email = f"user:{uid[:8]}…" if uid else "Unknown"
                    name = email
                elif not name:
                    name = email.split("@")[0]

            col_info, col_role, col_action = st.columns([5, 2, 1])
            with col_info:
                st.markdown(
                    f'<div class="member-item" style="margin-bottom:0;">'
                    f'<div><div class="member-name">{status_icon} {name}</div>'
                    f'<div class="member-email">{email}</div></div></div>',
                    unsafe_allow_html=True,
                )
            with col_role:
                st.markdown(
                    f'<div style="padding-top:12px;">'
                    f'<span class="member-role {role}">{role.upper()}</span></div>',
                    unsafe_allow_html=True,
                )
            with col_action:
                if not is_self and not is_owner and user_role in ["owner", "admin"]:
                    if st.button("✕", key=f"remove_{member.get('user_id')}", help="Remove member"):
                        
                        Analytics().track_event("team_member_remove_initiated", {"member_uid": member.get('user_id')})
                        st.session_state[f"confirm_remove_{member.get('user_id')}"] = True
                        st.rerun()

            # Removal confirmation
            uid = member.get("user_id", "")
            if st.session_state.get(f"confirm_remove_{uid}"):
                st.warning(f"Remove **{name}** ({email}) from the organization?")
                cy, cn = st.columns(2)
                with cy:
                    if st.button("Yes, Remove", key=f"yes_remove_{uid}", type="primary", use_container_width=True):
                        try:
                            # Route removal through OrganizationManager so that:
                            # (a) the soft-delete uses the correct raw-SQL path, and
                            # (b) _update_seats_used() is called in one place,
                            #     eliminating the counter drift described in Issue 4.
                            org_manager = sub_manager.org_manager
                            org_manager.remove_organization_member(org_id, uid)
                            
                            
                            Analytics().track_event("team_member_removed", {"member_uid": uid})
                            
                            st.session_state[f"confirm_remove_{uid}"] = False
                            st.success("Member removed.")
                        except ValueError as ve:
                            st.error(f"Cannot remove member: {ve}")
                        except Exception as e:
                            st.error(f"Could not remove member: {e}")
                        st.rerun()
                with cn:
                    if st.button("Cancel", key=f"no_remove_{uid}", use_container_width=True):
                        st.session_state[f"confirm_remove_{uid}"] = False
                        st.rerun()

    # ── Pending invitations ──
    if pending_invites:
        st.markdown(
            "<div style='font-size:14px;font-weight:600;color:#9BA1B0;"
            "margin:20px 0 10px;text-transform:uppercase;letter-spacing:.05em;'>"
            "Pending Invitations</div>",
            unsafe_allow_html=True,
        )
        for invite in pending_invites:
            inv_email = invite.get("invited_email", "")
            inv_role = invite.get("role", "member")
            inv_id = invite.get("id", "")
            try:
                exp = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00"))
                exp_str = exp.strftime("%b %d, %Y")
            except Exception:
                exp_str = "—"

            col_i, col_badge, col_exp, col_cancel = st.columns([4, 2, 2, 1])
            with col_i:
                st.markdown(f'<div class="invite-email">✉️ {inv_email}</div>', unsafe_allow_html=True)
            with col_badge:
                st.markdown(f'<span class="invite-badge">{inv_role.upper()}</span>', unsafe_allow_html=True)
            with col_exp:
                st.markdown(f'<span style="font-size:12px;color:#6B7280;">Expires {exp_str}</span>', unsafe_allow_html=True)
            with col_cancel:
                if st.button("✕", key=f"cancel_inv_{inv_id}", help="Cancel invitation"):
                    db.cancel_invitation(inv_id)
                    
                    
                    Analytics().track_event("team_invite_cancelled", {"invite_id": inv_id})
                    
                    st.success(f"Invitation to {inv_email} cancelled.")
                    st.rerun()



    # ── Invite button ──
    if user_role in ["owner", "admin"]:
        st.markdown('<div style="margin-top:8px;"></div>', unsafe_allow_html=True)
        invite_col, _, _, _, _ = st.columns([1, 1, 1, 1, 1])
        with invite_col:
            if st.button("➕ Invite Team Member", key="invite_member", use_container_width=True):
                invite_member_dialog(org, org_id, current_user_id, db)
        st.markdown('<div style="margin-bottom:48px;"></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    render_organization_dashboard()

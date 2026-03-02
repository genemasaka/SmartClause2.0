"""
Paywall UI Components for SmartClause
Streamlit components for subscription status, paywall gates, and upgrade prompts.

Updated to use the current organization-based subscription model:
  Tiers: trial → individual → team → enterprise
"""

import streamlit as st
from typing import Optional, Dict, Any
from subscription_manager import (
    PRICING,
    TRIAL_TIER, INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER,
    FEATURES,
)


# ─────────────────────────────────────────────────────────────────────────────
# Tier display helpers
# ─────────────────────────────────────────────────────────────────────────────

_TIER_META = {
    TRIAL_TIER: {
        "label": "Free Trial",
        "color": "#9BA1B0",
        "icon": "⏳",
        "next_tier": INDIVIDUAL_TIER,
        "next_label": "Individual",
    },
    INDIVIDUAL_TIER: {
        "label": "Individual",
        "color": "#4ADE80",
        "icon": "👤",
        "next_tier": TEAM_TIER,
        "next_label": "Team",
    },
    TEAM_TIER: {
        "label": "Team",
        "color": "#F59E0B",
        "icon": "👥",
        "next_tier": ENTERPRISE_TIER,
        "next_label": "Enterprise",
    },
    ENTERPRISE_TIER: {
        "label": "Enterprise",
        "color": "#4B9EFF",
        "icon": "🏢",
        "next_tier": None,
        "next_label": None,
    },
}

_FEATURE_LABELS = {
    "document_editor": "Document Editor",
    "clause_library": "Clause Library",
    "admin_dashboard": "Admin Dashboard",
    "custom_templates": "Custom Templates",
    "priority_support": "Priority Support",
    "sso": "SSO Integration",
    "api_access": "API Access",
    "ai_chatbot": "AI Chatbot",
}


def _tier_meta(tier: str) -> Dict[str, Any]:
    """Return display metadata for a tier, with safe fallback."""
    return _TIER_META.get(tier, {"label": tier.title(), "color": "#9BA1B0", "icon": "📋", "next_tier": None, "next_label": None})


# ─────────────────────────────────────────────────────────────────────────────
# Subscription status badge (for sidebar / header)
# ─────────────────────────────────────────────────────────────────────────────

def render_subscription_status(subscription_data: Dict[str, Any]):
    """
    Display a compact subscription status badge.

    Args:
        subscription_data: Dict returned by SubscriptionManager.get_user_status()
    """
    tier = subscription_data.get("tier", TRIAL_TIER)
    is_active = subscription_data.get("is_active", True)
    days_remaining = subscription_data.get("days_remaining")
    documents_remaining = subscription_data.get("documents_remaining")

    meta = _tier_meta(tier)
    color = meta["color"] if is_active else "#EF4444"
    label = meta["label"]
    icon = meta["icon"]

    # Build the status line
    if not is_active:
        status_line = "Expired — upgrade to continue"
        status_color = "#EF4444"
    elif tier == TRIAL_TIER:
        if days_remaining is not None:
            status_line = f"{days_remaining} day{'s' if days_remaining != 1 else ''} left in trial"
        else:
            status_line = "Trial active"
        status_color = "#F59E0B" if (days_remaining or 99) <= 3 else "#9BA1B0"
    else:
        if documents_remaining is not None:
            status_line = f"{documents_remaining} docs remaining this month"
        elif days_remaining is not None:
            status_line = f"Renews in {days_remaining} day{'s' if days_remaining != 1 else ''}"
        else:
            status_line = "Active"
        status_color = "#4ADE80"

    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.04);
        border: 1px solid {color}33;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    ">
        <div style="font-size: 12px; color: #9BA1B0; margin-bottom: 2px;">Plan</div>
        <div style="font-size: 14px; font-weight: 600; color: {color};">
            {icon} {label}
        </div>
        <div style="font-size: 11px; color: {status_color}; margin-top: 4px;">
            {status_line}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Upgrade CTA for trial / expired
    if not is_active or tier == TRIAL_TIER:
        if st.button("⬆️ Upgrade Plan", key="paywall_upgrade_btn", use_container_width=True):
            st.query_params["view"] = "pricing"
            st.rerun()

    # Renewal warning for paid tiers expiring soon
    elif days_remaining is not None and days_remaining <= 5:
        st.warning(f"⚠️ Your {label} plan expires in {days_remaining} day(s). Renew on the Pricing page.")


# ─────────────────────────────────────────────────────────────────────────────
# Paywall gate — shown inside a locked feature page
# ─────────────────────────────────────────────────────────────────────────────

def render_paywall_gate(
    feature_key: str,
    current_tier: str,
    is_active: bool = True,
    page_title: Optional[str] = None,
    page_subtitle: Optional[str] = None,
):
    """
    Render a professional paywall screen when a user tries to access a locked feature.

    Args:
        feature_key:   Feature identifier (e.g. "clause_library").
        current_tier:  User's current tier string.
        is_active:     Whether their subscription is active.
        page_title:    Optional heading override.
        page_subtitle: Optional subtitle override.
    """
    feature_label = _FEATURE_LABELS.get(feature_key, feature_key.replace("_", " ").title())
    allowed_tiers = FEATURES.get(feature_key, [])

    # Determine the *minimum* tier that unlocks the feature
    tier_order = [TRIAL_TIER, INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER]
    min_tier = next((t for t in tier_order if t in allowed_tiers), INDIVIDUAL_TIER)
    min_tier_meta = _tier_meta(min_tier)

    title = page_title or f"{feature_label} — Upgrade Required"
    subtitle = page_subtitle or (
        f"This feature is available from the **{min_tier_meta['label']}** plan and above."
    )

    if not is_active and current_tier != TRIAL_TIER:
        # Subscription lapsed — different message
        current_meta = _tier_meta(current_tier)
        headline = f"Your {current_meta['label']} plan has expired"
        body = "Renew your subscription to regain access to this feature."
    else:
        headline = title
        body = subtitle

    st.markdown(f"""
    <div style="
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 48px 40px;
        text-align: center;
        margin-top: 16px;
    ">
        <div style="
            width: 56px; height: 56px;
            background: rgba(75,158,255,0.12);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 20px;
            font-size: 26px;
        ">🔒</div>
        <h2 style="color: #FFFFFF; font-size: 22px; margin-bottom: 10px;">{headline}</h2>
        <p style="color: #9BA1B0; font-size: 15px; max-width: 480px; margin: 0 auto 28px; line-height: 1.6;">
            {body}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    col_l, col_btn, col_r = st.columns([1, 2, 1])
    with col_btn:
        if st.button(
            f"View Plans →",
            key=f"paywall_goto_pricing_{feature_key}",
            use_container_width=True,
            type="primary",
        ):
            st.query_params["view"] = "pricing"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Document limit warning banner
# ─────────────────────────────────────────────────────────────────────────────

def render_document_limit_warning(documents_remaining: Optional[int], tier: str):
    """
    Show a banner when the user is close to or at their document limit.

    Args:
        documents_remaining: Number of docs remaining (None = unlimited).
        tier: Current tier string.
    """
    if documents_remaining is None:
        return  # Unlimited — no banner needed

    if documents_remaining == 0:
        st.error(
            "📄 You've reached your monthly document limit. "
            "[Upgrade your plan](?view=pricing) to create more documents."
        )
    elif documents_remaining <= 5:
        st.warning(
            f"⚠️ Only **{documents_remaining}** document{'s' if documents_remaining != 1 else ''} "
            f"remaining this month. [Upgrade for more](?view=pricing)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Payment feedback helpers
# ─────────────────────────────────────────────────────────────────────────────

def show_payment_success(tier: Optional[str] = None):
    """Display a success message after a completed payment."""
    st.balloons()
    tier_label = _tier_meta(tier)["label"] if tier else "new"
    st.success(f"✅ Payment successful! Your **{tier_label}** plan is now active.")


def show_payment_error(message: str):
    """Display a user-friendly payment error."""
    st.error(f"❌ Payment failed: {message}")
    st.info("If your M-Pesa was charged, please contact support at **support@smartclause.co.ke** with your phone number.")


def show_payment_verification_spinner(message: str = "Verifying payment…"):
    """Convenience wrapper for a payment verification spinner."""
    return st.spinner(message)

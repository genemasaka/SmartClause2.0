"""
Paywall UI Components for SmartClause
Streamlit components for pricing, paywalls, and payment modals
"""

import streamlit as st
from typing import Optional, Dict, Any
from subscription_manager import PRICING, SINGLE_CREDIT_TIER, PAY_AS_YOU_GO_TIER, STANDARD_TIER

def render_pricing_cards():
    """
    Display pricing tiers in a 3-column layout.
    Returns the selected tier or None.
    """
    st.markdown("### 💳 Choose Your Plan")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    # Individual Tier
    with col1:
        st.markdown("""
        <div style='border: 2px solid #4ADE80; border-radius: 10px; padding: 20px; text-align: center; background-color: #1A1D24;'>
            <h3 style='color: #4ADE80;'>👤 Individual</h3>
            <h2 style='color: #FFFFFF;'>KES 8,500</h2>
            <p style='color: #9BA1B0;'>Per Month</p>
            <hr style='border-color: #252930;'>
            <p style='text-align: left; font-size: 14px; color: #FFFFFF;'>
                ✅ 50 documents/month<br>
                ✅ Full Document Editor<br>
                ✅ Clause Library<br>
            </p>
            <p style='color: #9BA1B0; font-size: 12px;'>Perfect for solo practitioners</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Get Individual", key="buy_individual_modal", use_container_width=True):
             from subscription_manager import INDIVIDUAL_TIER
             return INDIVIDUAL_TIER
    
    # Team Tier
    with col2:
        st.markdown("""
        <div style='border: 3px solid #F59E0B; border-radius: 10px; padding: 20px; text-align: center; background-color: #1A1D24;'>
            <div style='background-color: #F59E0B; color: #000; padding: 5px; margin: -20px -20px 10px -20px; border-radius: 8px 8px 0 0;'>
                <strong>⭐ BEST VALUE</strong>
            </div>
            <h3 style='color: #F59E0B;'>👥 Team</h3>
            <h2 style='color: #FFFFFF;'>KES 6,500</h2>
            <p style='color: #9BA1B0;'>Per User / Month</p>
            <hr style='border-color: #252930;'>
            <p style='text-align: left; font-size: 14px; color: #FFFFFF;'>
                ✅ 100 documents/user/mo<br>
                ✅ Admin Dashboard<br>
                ✅ Team Features<br>
            </p>
            <p style='color: #9BA1B0; font-size: 12px;'>Ideal for small law firms</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Get Team", key="buy_team_modal", use_container_width=True):
            from subscription_manager import TEAM_TIER
            return TEAM_TIER
    
    # Enterprise Tier
    with col3:
        st.markdown("""
        <div style='border: 2px solid #4B9EFF; border-radius: 10px; padding: 20px; text-align: center; background-color: #1A1D24;'>
            <h3 style='color: #4B9EFF;'>🏢 Enterprise</h3>
            <h2 style='color: #FFFFFF;'>KES 5,000</h2>
            <p style='color: #9BA1B0;'>Per User / Month</p>
            <hr style='border-color: #252930;'>
            <p style='text-align: left; font-size: 14px; color: #FFFFFF;'>
                ✅ Unlimited documents<br>
                ✅ SSO & API Access<br>
                ✅ Dedicated Support<br>
            </p>
            <p style='color: #9BA1B0; font-size: 12px;'>For enterprise teams</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Contact Sales", key="buy_enterprise_modal", use_container_width=True):
            from subscription_manager import ENTERPRISE_TIER
            return ENTERPRISE_TIER
            
    return None


def render_paywall_modal(reason: str, current_tier: str):
    """
    Display a paywall modal when user hits a restriction.
    
    Args:
        reason: Why the paywall is shown (e.g., "no_credits", "editor_locked")
        current_tier: User's current subscription tier
    """
    if reason == "no_credits":
        st.warning("⚠️ You've run out of credits!")
        st.markdown("""
        You need credits to generate documents. Choose a plan below to continue:
        """)
        
    elif reason == "editor_locked":
        st.warning("🔒 Document Editor is locked")
        st.markdown("""
        The Document Editor is available on the **Individual** plan and higher.
        Upgrade to access full editing capabilities.
        """)
        
    elif reason == "library_locked":
        st.warning("🔒 Clause Library is locked")
        st.markdown("""
        The Clause Library is available on the **Individual** plan and higher.
        Upgrade to create and manage custom clauses.
        """)
    
    # Show pricing options
    selected_tier = render_pricing_cards()
    return selected_tier


def render_payment_modal(payment_type: str, tier: str) -> Optional[str]:
    """
    Display payment modal with phone number input.
    
    Args:
        payment_type: "credit_purchase" or "subscription"
        tier: The tier being purchased
        
    Returns:
        Phone number if submitted, None otherwise
    """
    pricing = PRICING[tier]
    amount = pricing["amount"]
    tier_name = pricing["name"]
    
    st.markdown(f"### 💳 Complete Payment - {tier_name}")
    st.markdown(f"**Amount:** KES {amount:,}")
    
    if tier in [TESTER_TIER, PAY_AS_YOU_GO_TIER]:
        st.markdown(f"**Credits:** {pricing['credits']}")
    else:
        st.markdown("**Duration:** 30 days")
    
    st.markdown("---")
    
    with st.form("payment_form"):
        st.markdown("**Enter your M-Pesa phone number:**")
        phone_number = st.text_input(
            "Phone Number",
            placeholder="254XXXXXXXXX or 07XXXXXXXX",
            help="Enter your Safaricom phone number to receive the payment prompt"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Pay Now", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        
        if submit and phone_number:
            return phone_number
        elif cancel:
            return "CANCEL"
    
    return None


def render_credit_balance(credits: int, tier: str):
    """
    Display credit balance indicator for credit-based tiers.
    
    Args:
        credits: Number of remaining credits
        tier: User's tier
    """
    if tier in [SINGLE_CREDIT_TIER, PAY_AS_YOU_GO_TIER]:
        # Color based on credit level
        if credits == 0:
            color = "#f44336"  # Red
            icon = "⚠️"
        elif credits <= 2:
            color = "#FF9800"  # Orange
            icon = "⚡"
        else:
            color = "#4CAF50"  # Green
            icon = "✅"
        
        st.markdown(f"""
        <div style='background-color: {color}; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;'>
            <strong>{icon} Credits: {credits}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        if credits == 0:
            if st.button("🛒 Buy More Credits", key="buy_credits_sidebar", use_container_width=True):
                st.session_state.show_pricing = True


def render_subscription_status(subscription_data: Dict[str, Any]):
    """
    Display subscription status in sidebar.
    
    Args:
        subscription_data: Dict with tier, credits, expiry_date, etc.
    """
    tier = subscription_data.get("tier", TESTER_TIER)
    credits = subscription_data.get("credits", 0)
    is_active = subscription_data.get("is_active", True)
    days_remaining = subscription_data.get("days_remaining")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Subscription Status")
    
    # Tier display
    tier_names = {
        SINGLE_CREDIT_TIER: "🧪 Single Credit",
        PAY_AS_YOU_GO_TIER: "📄 Pay-As-You-Go",
        STANDARD_TIER: "🏢 Standard"
    }
    
    tier_display = tier_names.get(tier, tier)
    st.sidebar.markdown(f"**Plan:** {tier_display}")
    
    # Credit balance for credit-based tiers
    if tier in [SINGLE_CREDIT_TIER, PAY_AS_YOU_GO_TIER]:
        render_credit_balance(credits, tier)
    
    # Subscription expiry for Standard tier
    elif tier == STANDARD_TIER:
        if is_active and days_remaining is not None:
            if days_remaining <= 3:
                st.sidebar.warning(f"⚠️ Expires in {days_remaining} days")
            else:
                st.sidebar.success(f"✅ Active ({days_remaining} days left)")
        elif not is_active:
            st.sidebar.error("❌ Subscription Expired")
            if st.sidebar.button("🔄 Renew Subscription", use_container_width=True):
                st.session_state.show_pricing = True
    
    # Upgrade button for non-Standard users
    if tier != STANDARD_TIER:
        st.sidebar.markdown("---")
        if st.sidebar.button("⬆️ Upgrade to Standard", key="upgrade_sidebar", use_container_width=True):
            st.session_state.show_pricing = True


def show_payment_verification_spinner(message: str = "Verifying payment..."):
    """
    Display a spinner during payment verification.
    
    Args:
        message: Message to display
    """
    with st.spinner(message):
        import time
        time.sleep(1)  # Visual feedback


def show_payment_success(credits_added: Optional[int] = None):
    """
    Display success message after payment.
    
    Args:
        credits_added: Number of credits added (if applicable)
    """
    st.balloons()
    
    if credits_added:
        st.success(f"✅ Payment successful! {credits_added} credit(s) added to your account.")
    else:
        st.success("✅ Payment successful! You now have full Standard access.")


def show_payment_error(message: str):
    """
    Display error message for failed payment.
    
    Args:
        message: Error message to display
    """
    st.error(f"❌ {message}")

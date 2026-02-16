"""
Pricing Page for SmartClause Enterprise Subscription Model
Displays Individual, Team, and Enterprise pricing tiers
"""

import streamlit as st
from subscription_manager import SubscriptionManager, PRICING, TRIAL_TIER, INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER
from database import DatabaseManager
from payment_flow import PaymentFlowManager
from mpesa_handler import MpesaHandler
import time


def render_pricing_page():
    """Main pricing page with enterprise subscription tiers"""
    
    # Custom styling matching app theme
    st.markdown("""
    <style>
    /* Override Streamlit defaults */
    .stApp {
        background-color: #0A0B0D;
    }
    
    /* Pricing card styling */
    .pricing-card {
        background: #1A1D24;
        border: 2px solid #252930;
        border-radius: 12px;
        padding: 24px;
        min-height: 600px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s ease;
    }
    
    .pricing-card:hover {
        transform: translateY(-4px);
        border-color: #4B9EFF;
        box-shadow: 0 8px 24px rgba(75, 158, 255, 0.15);
    }
    
    .pricing-card.featured {
        background: linear-gradient(135deg, #1A1D24 0%, #252930 100%);
        border-color: #F59E0B;
    }
    
    .pricing-card.featured:hover {
        border-color: #FBBF24;
        box-shadow: 0 8px 24px rgba(245, 158, 11, 0.2);
    }
    
    .pricing-badge {
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: #F59E0B;
        color: #0A0B0D;
        padding: 4px 16px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #4B9EFF !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #5BABFF !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(75, 158, 255, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize managers
    db = DatabaseManager()
    user_id = st.session_state.get("user_id")
    
    if user_id:
        db.set_user(user_id)
        sub_manager = SubscriptionManager(db)
        
        # Initialize payment manager
        try:
            mpesa = MpesaHandler()
            payment_manager = PaymentFlowManager(db, mpesa)
        except Exception as e:
            st.error(f"Failed to initialize payment system: {e}")
            payment_manager = None
            
        status = sub_manager.get_user_status(user_id)
        current_tier = status.get("tier", TRIAL_TIER)
        org_name = status.get("organization_name", "None")
    else:
        current_tier = TRIAL_TIER
        org_name = "None"
    
    # Page Header
    st.markdown("""
    <div style='margin-bottom: 32px;'>
        <div style='font-size: 32px; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;'>
            💼 Choose Your Plan
        </div>
        <div style='font-size: 16px; color: #9BA1B0;'>
            Scale with confidence - from solo practitioners to enterprise law firms
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Current plan status
    if user_id:
        tier_display = current_tier.title() if current_tier else "Trial"
        st.markdown(f"""
        <div style='background: #1A1D24; border: 1px solid #252930; border-radius: 12px; padding: 16px; margin-bottom: 32px;'>
            <div style='font-size: 14px; color: #9BA1B0; margin-bottom: 4px;'>Current Plan</div>
            <div style='font-size: 18px; font-weight: 600; color: #FFFFFF;'>
                {tier_display} • {org_name}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Pricing cards
    col1, col2, col3 = st.columns(3)
    
    # Individual Tier
    with col1:
        st.markdown("""
        <div style='position: relative;'>
        <div class='pricing-card'>
            <div style='text-align: center;'>
                <div style='font-size: 32px; margin-bottom: 8px;'>👤</div>
                <div style='font-size: 20px; font-weight: 700; color: #4ADE80; margin-bottom: 8px;'>Individual</div>
                <div style='font-size: 36px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;'>KES 8,500</div>
                <div style='font-size: 14px; color: #9BA1B0; margin-bottom: 24px;'>Per Month</div>
                <div style='border-top: 1px solid #252930; padding-top: 20px; text-align: left;'>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ 50 documents/month
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Full Document Editor
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Clause Library
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Email Support
                    </div>
                    <div style='font-size: 14px; color: #6B7280; margin-bottom: 20px;'>
                        ❌ No Team Features
                    </div>
                    <div style='font-size: 12px; color: #9BA1B0; font-style: italic;'>
                        Perfect for solo practitioners
                    </div>
                </div>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        
        if user_id and current_tier != INDIVIDUAL_TIER:
            if st.button("Get Individual (KES 8,500/mo)", key="buy_individual", use_container_width=True):
                st.session_state.show_payment_modal = True
                st.session_state.payment_tier = INDIVIDUAL_TIER
                st.session_state.payment_seats = 1
                st.session_state.payment_amount = 8500
                st.rerun()
        else:
            st.info("Current Plan" if current_tier == INDIVIDUAL_TIER else "Log in to subscribe")
    
    # Team Tier (Featured)
    with col2:
        st.markdown("""
        <div style='position: relative;'>
        <div class='pricing-badge'>⭐ BEST VALUE</div>
        <div class='pricing-card featured'>
            <div style='text-align: center; margin-top: 12px;'>
                <div style='font-size: 32px; margin-bottom: 8px;'>👥</div>
                <div style='font-size: 20px; font-weight: 700; color: #F59E0B; margin-bottom: 8px;'>Team</div>
                <div style='font-size: 36px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;'>KES 6,500</div>
                <div style='font-size: 14px; color: #9BA1B0; margin-bottom: 4px;'>Per User / Month</div>
                <div style='font-size: 14px; font-weight: 700; color: #4ADE80; margin-bottom: 24px;'>Min. 3 users</div>
                <div style='border-top: 1px solid #252930; padding-top: 20px; text-align: left;'>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ 100 documents/user/month
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Full Document Editor
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Clause Library
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Admin Dashboard
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Custom Templates
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 20px;'>
                        ✅ Priority Support
                    </div>
                    <div style='font-size: 12px; color: #9BA1B0; font-style: italic;'>
                        Ideal for small law firms
                    </div>
                </div>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        
        if user_id and current_tier != TEAM_TIER:
            if st.button("Get Team (from KES 19,500/mo)", key="buy_team", use_container_width=True):
                st.session_state.show_payment_modal = True
                st.session_state.payment_tier = TEAM_TIER
                st.session_state.payment_seats = 3 # Default minimum
                st.session_state.payment_amount = 6500 * 3
                st.rerun()
        else:
            st.info("Current Plan" if current_tier == TEAM_TIER else "Log in to subscribe")
    
    # Enterprise Tier
    with col3:
        st.markdown("""
        <div style='position: relative;'>
        <div class='pricing-card'>
            <div style='text-align: center;'>
                <div style='font-size: 32px; margin-bottom: 8px;'>🏢</div>
                <div style='font-size: 20px; font-weight: 700; color: #4B9EFF; margin-bottom: 8px;'>Enterprise</div>
                <div style='font-size: 36px; font-weight: 700; color: #FFFFFF; margin-bottom: 4px;'>KES 5,000</div>
                <div style='font-size: 14px; color: #9BA1B0; margin-bottom: 4px;'>Per User / Month</div>
                <div style='font-size: 14px; font-weight: 700; color: #4ADE80; margin-bottom: 24px;'>Min. 10 users</div>
                <div style='border-top: 1px solid #252930; padding-top: 20px; text-align: left;'>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Unlimited documents
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Full Document Editor
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Clause Library
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Admin Dashboard
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ SSO Integration
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ API Access
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 12px;'>
                        ✅ Dedicated Support
                    </div>
                    <div style='font-size: 14px; color: #FFFFFF; margin-bottom: 20px;'>
                        ✅ Custom SLA
                    </div>
                    <div style='font-size: 12px; color: #9BA1B0; font-style: italic;'>
                        For enterprise legal teams
                    </div>
                </div>
            </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        
        if user_id and current_tier != ENTERPRISE_TIER:
            if st.button("Contact Sales", key="buy_enterprise", use_container_width=True):
                st.info("📧 Contact us at sales@smartclause.co.ke for Enterprise pricing")
        else:
            st.info("Current Plan" if current_tier == ENTERPRISE_TIER else "Log in to subscribe")
    
    # Feature comparison
    st.markdown("---")
    st.markdown("""
    <div style='margin-top: 48px; margin-bottom: 24px;'>
        <div style='font-size: 24px; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;'>
            Compare Plans
        </div>
        <div style='font-size: 14px; color: #9BA1B0;'>
            All plans include AI-powered document generation
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature comparison table
    import pandas as pd
    
    comparison_data = {
        "Feature": [
            "Documents per Month",
            "Document Editor",
            "Clause Library",
            "Team Members",
            "Admin Dashboard",
            "Custom Templates",
            "Priority Support",
            "SSO Integration",
            "API Access",
            "Dedicated Support"
        ],
        "Individual": ["50", "✅", "✅", "1", "❌", "❌", "❌", "❌", "❌", "❌"],
        "Team": ["100/user", "✅", "✅", "3-10", "✅", "✅", "✅", "❌", "❌", "❌"],
        "Enterprise": ["Unlimited", "✅", "✅", "10+", "✅", "✅", "✅", "✅", "✅", "✅"]
    }
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Payment Modal Logic
    if st.session_state.get("show_payment_modal"):
        render_payment_modal(payment_manager, user_id, org_name)
    
    # FAQ Section
    st.markdown("---")
    st.markdown("""
    <div style='margin-top: 48px; margin-bottom: 24px;'>
        <div style='font-size: 24px; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;'>
            Frequently Asked Questions
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    faq_data = [
        ("Can I upgrade or downgrade anytime?", "Yes, you can upgrade your plan at any time. Changes take effect immediately."),
        ("What payment methods do you accept?", "We accept M-Pesa. Payments are processed securely and instantly."),
        ("Do you offer refunds?", "We offer a 7-day money-back guarantee if you're not satisfied with our service."),
        ("What happens to my documents if I cancel?", "Your documents remain accessible in read-only mode even after cancellation.")
    ]
    
    for question, answer in faq_data:
        with st.expander(question):
            st.write(answer)


def render_payment_modal(payment_manager, user_id, org_name):
    """
    Render modal for M-Pesa payment
    """
    if not payment_manager:
        st.error("Payment system unavailable. Please try again later.")
        if st.button("Close"):
            st.session_state.show_payment_modal = False
            st.rerun()
        return

    tier = st.session_state.get("payment_tier")
    seats = st.session_state.get("payment_seats", 1)
    base_amount = st.session_state.get("payment_amount", 0)
    
    # Calculate total amount (re-verify)
    tier_config = PRICING.get(tier, {})
    price_per_seat = tier_config.get("amount", 0) / 100 # Convert to KES
    
    # Styling for modal content
    st.markdown("""
    <div style='background: #1A1D24; padding: 24px; border-radius: 12px; border: 1px solid #252930; margin-bottom: 24px;'>
        <div style='font-size: 20px; font-weight: 700; color: #FFFFFF; margin-bottom: 16px;'>
            Confirm Subscription
        </div>
        <div style='font-size: 14px; color: #9BA1B0; margin-bottom: 8px;'>
            Plan: <span style='color: #FFFFFF; font-weight: 600;'>{tier}</span>
        </div>
        <div style='font-size: 14px; color: #9BA1B0; margin-bottom: 8px;'>
            Organization: <span style='color: #FFFFFF; font-weight: 600;'>{org}</span>
        </div>
    </div>
    """.format(tier=tier.title(), org=org_name), unsafe_allow_html=True)
    
    # Seat selection for Team tier
    if tier == TEAM_TIER:
        new_seats = st.number_input("Number of Users (Seats)", min_value=3, value=seats, step=1)
        if new_seats != seats:
            st.session_state.payment_seats = new_seats
            st.session_state.payment_amount = int(new_seats * price_per_seat)
            st.rerun()
        
        amount = int(new_seats * price_per_seat)
        seats = new_seats
    else:
        amount = int(base_amount)
    
    st.markdown(f"""
    <div style='font-size: 32px; font-weight: 700; color: #4ADE80; margin-bottom: 24px;'>
        KES {amount:,}
    </div>
    """, unsafe_allow_html=True)
    
    # Phone number input
    phone_number = st.text_input("M-Pesa Phone Number", placeholder="e.g., 254712345678")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Cancel", key="cancel_payment", use_container_width=True):
            st.session_state.show_payment_modal = False
            st.rerun()
            
    with col2:
        if st.button("Pay Now", key="confirm_payment", type="primary", use_container_width=True):
            if not phone_number:
                st.error("Please enter a phone number")
            elif not phone_number.startswith("254") or len(phone_number) != 12:
                st.error("Please enter a valid format: 2547XXXXXXXX")
            else:
                with st.spinner("Initiating M-Pesa payment..."):
                    # Get organization ID (if not exists, we might need to handle basic user vs org)
                    # For now, assume user has org or we use 'user_id' as org placeholder if needed
                    # checking payment_flow implementation: initiate_organization_purchase(user_id, organization_id, ...)
                    # SubscriptionManager.initialize_user_subscription ensures org exists
                    
                    # We need the Org ID. pricing_page doesn't pass it fully.
                    # We can fetch it again or assume the user has one.
                    # Let's get it from db helper in the function if needed, or pass it.
                    # Actually, render_pricing_page has sub_manager.
                    # We should probably pass org_id to this function or fetch it.
                    # Let's use the one from session state or fetch it.
                    # Wait, payment_manager has db.
                    
                    # Fetch org ID
                    org_data = payment_manager.db.get_user_organization(user_id)
                    if not org_data:
                        st.error("Organization not found. Please contact support.")
                        return
                    
                    org_id = org_data['id']
                    
                    result = payment_manager.initiate_organization_purchase(
                        user_id=user_id,
                        organization_id=org_id,
                        tier=tier,
                        seats=seats,
                        phone_number=phone_number
                    )
                    
                    if result['success']:
                        st.success("✅ Payment initiated! Check your phone.")
                        time.sleep(2)
                        st.session_state.show_payment_modal = False
                        st.rerun()
                    else:
                        st.error(f"Payment failed: {result['message']}")
    
    with st.expander("What happens when I reach my document limit?"):
        st.markdown("""
        For Individual and Team plans, you'll be notified when approaching your monthly limit. 
        You can upgrade to a higher tier or wait for your limit to reset at the start of the next billing cycle.
        """)
    
    with st.expander("Is there a free trial?"):
        st.markdown("""
        Yes! New users get a 14-day trial with 10 free documents to explore SmartClause features.
        """)


if __name__ == "__main__":
    render_pricing_page()

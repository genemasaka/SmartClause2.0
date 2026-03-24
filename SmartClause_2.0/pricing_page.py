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
import logging
from analytics import Analytics

# Configure logging
logger = logging.getLogger(__name__)

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
    
    Analytics().track_page_visit("Pricing")
    
    if user_id:
        db.set_user(user_id)
        subscription_mgr = SubscriptionManager(db)
        
        # Initialize payment manager
        try:
            mpesa = MpesaHandler()
            payment_manager = PaymentFlowManager(db, mpesa)
        except Exception as e:
            st.error(f"Failed to initialize payment system: {e}")
            payment_manager = None
            
        status = subscription_mgr.get_user_status(user_id)
        current_tier = status.get("tier", TRIAL_TIER)
        org_name = status.get("organization_name", "None")
    else:
        current_tier = TRIAL_TIER
        org_name = "None"
    
    # Page Header
    st.markdown("""
    <div style='margin-bottom: 32px;'>
        <div style='display: flex; align-items: center; gap: 14px; font-size: 32px; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;'>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 7C16 6.07003 16 5.60504 15.8978 5.22354C15.6204 4.18827 14.8117 3.37962 13.7765 3.10222C13.395 3 12.93 3 12 3C11.07 3 10.605 3 10.2235 3.10222C9.18827 3.37962 8.37962 4.18827 8.10222 5.22354C8 5.60504 8 6.07003 8 7M5.2 21H18.8C19.9201 21 20.4802 21 20.908 20.782C21.2843 20.5903 21.5903 20.2843 21.782 19.908C22 19.4802 22 18.9201 22 17.8V10.2C22 9.07989 22 8.51984 21.782 8.09202C21.5903 7.71569 21.2843 7.40973 20.908 7.21799C20.4802 7 19.9201 7 18.8 7H5.2C4.07989 7 3.51984 7 3.09202 7.21799C2.71569 7.40973 2.40973 7.71569 2.21799 8.09202C2 8.51984 2 9.07989 2 10.2V17.8C2 18.9201 2 19.4802 2.21799 19.908C2.40973 20.2843 2.71569 20.5903 3.09202 20.782C3.51984 21 4.0799 21 5.2 21Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Choose Your Plan
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
                <div style='display: flex; justify-content: center; margin-bottom: 8px;'>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 21C20 19.6044 20 18.9067 19.8278 18.3389C19.44 17.0605 18.4395 16.06 17.1611 15.6722C16.5933 15.5 15.8956 15.5 14.5 15.5H9.5C8.10444 15.5 7.40665 15.5 6.83886 15.6722C5.56045 16.06 4.56004 17.0605 4.17224 18.3389C4 18.9067 4 19.6044 4 21M16.5 7.5C16.5 9.98528 14.4853 12 12 12C9.51472 12 7.5 9.98528 7.5 7.5C7.5 5.01472 9.51472 3 12 3C14.4853 3 16.5 5.01472 16.5 7.5Z" stroke="#4ADE80" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
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
                Analytics().track_event("plan_selection_initiated", {"tier": INDIVIDUAL_TIER, "amount": 8500})
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
                <div style='display: flex; justify-content: center; margin-bottom: 8px;'>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22 21V19C22 17.1362 20.7252 15.5701 19 15.126M15.5 3.29076C16.9659 3.88415 18 5.32131 18 7C18 8.67869 16.9659 10.1159 15.5 10.7092M17 21C17 19.1362 17 18.2044 16.6955 17.4693C16.2895 16.4892 15.5108 15.7105 14.5307 15.3045C13.7956 15 12.8638 15 11 15H8C6.13623 15 5.20435 15 4.46927 15.3045C3.48915 15.7105 2.71046 16.4892 2.30448 17.4693C2 18.2044 2 19.1362 2 21M13.5 7C13.5 9.20914 11.7091 11 9.5 11C7.29086 11 5.5 9.20914 5.5 7C5.5 4.79086 7.29086 3 9.5 3C11.7091 3 13.5 4.79086 13.5 7Z" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
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
                Analytics().track_event("plan_selection_initiated", {"tier": TEAM_TIER, "amount": 6500 * 3})
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
                <div style='display: flex; justify-content: center; margin-bottom: 8px;'>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M7.5 11H4.6C4.03995 11 3.75992 11 3.54601 11.109C3.35785 11.2049 3.20487 11.3578 3.10899 11.546C3 11.7599 3 12.0399 3 12.6V21M16.5 11H19.4C19.9601 11 20.2401 11 20.454 11.109C20.6422 11.2049 20.7951 11.3578 20.891 11.546C21 11.7599 21 12.0399 21 12.6V21M16.5 21V6.2C16.5 5.0799 16.5 4.51984 16.282 4.09202C16.0903 3.71569 15.7843 3.40973 15.408 3.21799C14.9802 3 14.4201 3 13.3 3H10.7C9.57989 3 9.01984 3 8.59202 3.21799C8.21569 3.40973 7.90973 3.71569 7.71799 4.09202C7.5 4.51984 7.5 5.0799 7.5 6.2V21M22 21H2M11 7H13M11 11H13M11 15H13" stroke="#4B9EFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
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
                Analytics().track_event("plan_selection_initiated", {"tier": ENTERPRISE_TIER, "is_contact_sales": True})
                st.info("📧 Contact us at support@smartclause.net for Enterprise pricing")
        else:
            st.info("Current Plan" if current_tier == ENTERPRISE_TIER else "Log in to subscribe")
    


    # Payment Modal Logic
    if st.session_state.get("show_payment_modal"):
        render_payment_modal(payment_manager, user_id, org_name, subscription_mgr)
    
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
        ("What happens to my documents if I cancel?", "Your documents remain accessible in read-only mode even after cancellation.")
    ]
    
    for question, answer in faq_data:
        with st.expander(question):
            st.write(answer)


def render_payment_modal(payment_manager, user_id, org_name, subscription_mgr):
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
                        # FALLBACK: Try to initialize one proactively
                        logger.info(f"Proactively initializing organization for user {user_id} during payment")
                        org_data = subscription_mgr.initialize_user_subscription(
                            user_id=user_id,
                            user_email=st.session_state.get("email", ""),
                            user_name=st.session_state.get("full_name")
                        )
                    
                    if not org_data:
                        st.error("Organization not found and could not be initialized. Please contact support.")
                        return
                    
                    org_id = org_data['id']
                    
                    result = payment_manager.initiate_organization_purchase(
                        user_id=user_id,
                        organization_id=org_id,
                        tier=tier,
                        seats=seats,
                        phone_number=phone_number
                    )
                    
                    Analytics().track_event("payment_initiated", {"tier": tier, "seats": seats, "amount": amount})
                    
                    if result['success']:
                        st.success("✅ Payment initiated! Check your phone.")
                        
                        # Verification Loop
                        checkout_request_id = result['checkout_request_id']
                        with st.spinner("Waiting for M-Pesa confirmation..."):
                            # Helper inside payment_manager handles polling/retries
                            verify_result = payment_manager.verify_and_process_payment(
                                checkout_request_id=checkout_request_id,
                                user_id=user_id,
                                max_attempts=12,  # 12 * 5s = 60s timeout
                                delay=5
                            )
                        
                        if verify_result['success']:
                            Analytics().track_event("payment_success", {"tier": tier, "seats": seats, "amount": amount})
                            # Import success helpers from paywall_ui
                            from paywall_ui import show_payment_success, show_payment_error
                            show_payment_success(tier)
                            time.sleep(3)
                            st.session_state.show_payment_modal = False
                            st.rerun()
                        else:
                            Analytics().track_event("payment_verification_failed", {"tier": tier, "error": verify_result['message']})
                            st.error(f"❌ Payment Verification Failed: {verify_result['message']}")
                            st.info("If your M-Pesa was charged, please contact support with your phone number.")
                    else:
                        Analytics().track_event("payment_initiation_failed", {"tier": tier, "error": result['message']})
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

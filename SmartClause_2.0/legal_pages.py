"""
Legal Pages for SmartClause
Renders the Privacy Policy and Terms of Use pages.
Tailored for the Kenyan market under the Data Protection Act, 2019.
"""

import streamlit as st
from auth import update_query_params, get_session_param


# ============================================================================
# SHARED LEGAL-PAGE STYLING
# ============================================================================
_LEGAL_CSS = """
<style>
    .legal-container {
        max-width: 820px;
        margin: 0 auto;
        padding: 48px 24px 80px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #D1D5DB;
        line-height: 1.75;
    }
    .legal-container h1 {
        font-size: 36px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 8px;
    }
    .legal-container .legal-updated {
        font-size: 13px;
        color: #6B7280;
        margin-bottom: 40px;
    }
    .legal-container h2 {
        font-size: 22px;
        font-weight: 600;
        color: #FFFFFF;
        margin-top: 40px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .legal-container h3 {
        font-size: 17px;
        font-weight: 600;
        color: #E5E7EB;
        margin-top: 24px;
        margin-bottom: 8px;
    }
    .legal-container p, .legal-container li {
        font-size: 15px;
        color: #9CA3AF;
    }
    .legal-container ul {
        padding-left: 24px;
    }
    .legal-container li {
        margin-bottom: 6px;
    }
    .legal-container a {
        color: #60A5FA;
        text-decoration: none;
    }
    .legal-container a:hover {
        text-decoration: underline;
    }
    .legal-container .legal-highlight {
        background: rgba(75, 158, 255, 0.08);
        border-left: 3px solid #4B9EFF;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin: 20px 0;
    }
    .legal-container .legal-highlight p {
        margin: 0;
        color: #D1D5DB;
    }
    .legal-back-btn {
        margin-bottom: 24px;
    }
</style>
"""

EFFECTIVE_DATE = "24 February 2026"


# ============================================================================
# PRIVACY POLICY
# ============================================================================
def render_privacy_policy():
    """Render the SmartClause Privacy Policy page."""
    st.markdown(_LEGAL_CSS, unsafe_allow_html=True)

    # Back button
    st.markdown('<div class="legal-back-btn">', unsafe_allow_html=True)
    if st.button("← Back", key="privacy_back"):
        update_query_params({"view": "matters"})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
<div class="legal-container">
<h1>Privacy Policy</h1>
<p class="legal-updated">Effective Date: {EFFECTIVE_DATE}</p>

<div class="legal-highlight">
<p>SmartClause is committed to protecting your personal data in accordance with the <strong>Kenya Data Protection Act, 2019</strong> (DPA) and the regulations issued by the <strong>Office of the Data Protection Commissioner (ODPC)</strong>.</p>
</div>

<h2>1. Data Controller</h2>
<p>SmartClause (the "Company", "we", "us") is the data controller responsible for your personal data collected through the SmartClause platform ("Platform"). For any data protection inquiries, contact us at:</p>
<ul>
    <li><strong>Email:</strong> support@smartclause.net</li>
    <li><strong>Address:</strong> Nairobi, Kenya</li>
</ul>

<h2>2. Personal Data We Collect</h2>
<p>We collect the following categories of personal data:</p>

<h3>2.1 Account Information</h3>
<ul>
    <li>Email address</li>
    <li>Password (stored in hashed form by our authentication provider)</li>
    <li>Full name (derived from your email at sign-up)</li>
    <li>Organization name and membership details</li>
</ul>

<h3>2.2 Legal Matter &amp; Document Data</h3>
<ul>
    <li>Matter details: matter name, client name, counterparty, jurisdiction, internal reference, and matter type</li>
    <li>Document content: legal drafts, clauses, comments, and version history created or edited on the Platform</li>
    <li>Clause library entries you create or save</li>
</ul>

<h3>2.3 Payment Data</h3>
<ul>
    <li>M-Pesa phone number (used to initiate STK push payments)</li>
    <li>Transaction reference IDs, amounts, and payment status</li>
    <li>Subscription tier and billing cycle</li>
</ul>
<p>We do <strong>not</strong> store your M-Pesa PIN or full mobile-money account details. Payment processing is handled by Safaricom's M-Pesa Daraja API.</p>

<h3>2.4 AI Interaction Data</h3>
<ul>
    <li>Queries and prompts you send to the AI Chat assistant</li>
    <li>AI-generated responses and edit suggestions</li>
    <li>Document context shared with our AI provider (OpenAI) for processing</li>
</ul>

<h3>2.5 Technical &amp; Usage Data</h3>
<ul>
    <li>Session tokens and authentication cookies</li>
    <li>Browser type, device information, and IP address (collected automatically)</li>
    <li>Feature usage patterns and navigation data</li>
</ul>

<h2>3. Legal Basis for Processing</h2>
<p>Under Section 30 of the Kenya DPA, we process your data on the following lawful bases:</p>
<ul>
    <li><strong>Consent:</strong> You provide consent when you create an account and agree to these terms.</li>
    <li><strong>Contractual Necessity:</strong> Processing is necessary to provide the services you have subscribed to (document drafting, AI assistance, clause management).</li>
    <li><strong>Legitimate Interest:</strong> We have a legitimate interest in maintaining platform security, preventing fraud, and improving our services.</li>
    <li><strong>Legal Obligation:</strong> We may process data to comply with applicable Kenyan law, court orders, or regulatory requirements.</li>
</ul>

<h2>4. How We Use Your Data</h2>
<ul>
    <li>To create and manage your account and organization</li>
    <li>To generate, store, and version legal documents on your behalf</li>
    <li>To provide AI-powered drafting assistance and clause suggestions</li>
    <li>To process subscription payments via M-Pesa</li>
    <li>To enforce subscription limits and feature access</li>
    <li>To send service-related notifications (e.g., trial expiry, payment confirmations)</li>
    <li>To improve platform performance, security, and reliability</li>
</ul>

<h2>5. Data Sharing &amp; Third Parties</h2>
<p>We share personal data only with the following categories of recipients, under appropriate safeguards:</p>
<ul>
    <li><strong>Supabase (Database &amp; Authentication):</strong> Stores your account data and documents. Supabase servers are hosted outside Kenya; we rely on Standard Contractual Clauses and Supabase's DPA for cross-border transfer compliance under Section 48 of the Kenya DPA.</li>
    <li><strong>OpenAI (AI Processing):</strong> Document excerpts and chat queries are sent to OpenAI's API for AI-powered features. OpenAI processes data under their Data Processing Agreement and does not use your data to train models when accessed via the API.</li>
    <li><strong>Safaricom M-Pesa (Payments):</strong> Your phone number is shared with Safaricom to initiate payment transactions via the Daraja API.</li>
</ul>
<p>We do <strong>not</strong> sell your personal data to third parties.</p>

<h2>6. Cross-Border Data Transfers</h2>
<p>Some of our service providers (Supabase, OpenAI) process data outside Kenya. In accordance with Section 48 of the DPA, we take steps to ensure that adequate safeguards are in place before transferring personal data, including:</p>
<ul>
    <li>Entering into Data Processing Agreements (DPAs) with each provider</li>
    <li>Relying on internationally recognized transfer mechanisms, such as Standard Contractual Clauses (SCCs), where applicable</li>
    <li>Assessing whether the recipient jurisdiction provides adequate data protection comparable to Kenya's DPA</li>
</ul>

<h2>7. Data Retention</h2>
<ul>
    <li><strong>Account data:</strong> Retained for as long as your account is active, or as required by law.</li>
    <li><strong>Matters &amp; documents:</strong> Retained until you delete them. Soft-deleted items are permanently purged after 90 days.</li>
    <li><strong>Payment records:</strong> Retained for 7 years to comply with Kenya Revenue Authority (KRA) tax record requirements.</li>
    <li><strong>AI chat history:</strong> Retained for the duration of your active session or document context. Not stored permanently by OpenAI.</li>
</ul>

<h2>8. Your Rights</h2>
<p>Under the Kenya DPA, you have the right to:</p>
<ul>
    <li><strong>Access</strong> your personal data held by us (Section 26(a))</li>
    <li><strong>Rectification</strong> of inaccurate or incomplete data (Section 26(c))</li>
    <li><strong>Erasure</strong> ("right to be forgotten") of your data, subject to legal retention obligations (Section 26(b))</li>
    <li><strong>Data portability</strong> — receive your data in a structured, commonly used format (Section 26(d))</li>
    <li><strong>Object</strong> to processing based on legitimate interest (Section 26(e))</li>
    <li><strong>Withdraw consent</strong> at any time, without affecting the lawfulness of prior processing (Section 32)</li>
    <li><strong>Lodge a complaint</strong> with the Office of the Data Protection Commissioner (ODPC) at <a href="https://www.odpc.go.ke" target="_blank">www.odpc.go.ke</a></li>
</ul>
<p>To exercise any of these rights, email us at <strong>support@smartclause.net</strong>. We will respond within 30 days.</p>

<h2>9. Data Security</h2>
<p>We implement appropriate technical and organizational measures to protect your data, including:</p>
<ul>
    <li>Encryption in transit (TLS/HTTPS) and at rest</li>
    <li>Row-Level Security (RLS) policies ensuring users can only access their own data</li>
    <li>Secure session management with signed cookies</li>
    <li>Access tokens with automatic refresh and expiry</li>
    <li>Regular security reviews of third-party integrations</li>
</ul>

<h2>10. Cookies &amp; Session Management</h2>
<p>SmartClause uses session-based cookies (stored in URL query parameters) to maintain your authentication state. We do not use third-party tracking cookies or advertising pixels.</p>

<h2>11. Children's Privacy</h2>
<p>SmartClause is intended for professional use by legal practitioners. We do not knowingly collect data from individuals under the age of 18. If we discover that a minor's data has been collected, we will delete it promptly.</p>

<h2>12. Changes to This Policy</h2>
<p>We may update this Privacy Policy from time to time. Material changes will be communicated via email or an in-app notification. The "Effective Date" at the top indicates when this version became active.</p>

<h2>13. Contact Us</h2>
<p>If you have questions about this Privacy Policy or our data practices, reach us at:</p>
<ul>
    <li><strong>Email:</strong> support@smartclause.net</li>
    <li><strong>ODPC Complaints:</strong> <a href="https://www.odpc.go.ke" target="_blank">www.odpc.go.ke</a></li>
</ul>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# TERMS OF USE
# ============================================================================
def render_terms_of_use():
    """Render the SmartClause Terms of Use page."""
    st.markdown(_LEGAL_CSS, unsafe_allow_html=True)

    # Back button
    st.markdown('<div class="legal-back-btn">', unsafe_allow_html=True)
    if st.button("← Back", key="terms_back"):
        update_query_params({"view": "matters"})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    session_param = get_session_param()
    st.markdown(f"""
<div class="legal-container">
<h1>Terms of Use</h1>
<p class="legal-updated">Effective Date: {EFFECTIVE_DATE}</p>

<div class="legal-highlight">
<p>Please read these Terms of Use carefully before using SmartClause. By creating an account or using the Platform, you agree to be bound by these Terms.</p>
</div>

<h2>1. Acceptance of Terms</h2>
<p>By accessing or using the SmartClause platform ("Platform"), you ("User", "you") agree to these Terms of Use ("Terms") and our <a href="?view=privacy{session_param}" target="_self">Privacy Policy</a>. If you do not agree, you must not use the Platform.</p>

<h2>2. About SmartClause</h2>
<p>SmartClause is an AI-powered legal drafting assistant designed to help legal professionals in Kenya create, manage, and collaborate on legal documents. The Platform provides:</p>
<ul>
    <li>Matter and document management</li>
    <li>AI-powered document drafting and clause suggestions</li>
    <li>Clause library for reusable legal language</li>
    <li>Version tracking and commenting</li>
    <li>Organization and team management</li>
    <li>M-Pesa integrated subscription billing</li>
</ul>

<h2>3. Eligibility</h2>
<p>You must be at least 18 years old and have the legal capacity to enter into a binding agreement under Kenyan law. By using the Platform, you represent that you meet these requirements.</p>

<h2>4. Account Registration</h2>
<ul>
    <li>You must provide a valid email address and create a secure password.</li>
    <li>You are responsible for maintaining the confidentiality of your login credentials.</li>
    <li>You must notify us immediately of any unauthorized use of your account.</li>
    <li>We reserve the right to suspend or terminate accounts that violate these Terms.</li>
</ul>

<h2>5. Subscription Plans &amp; Payments</h2>
<h3>5.1 Tiers</h3>
<p>SmartClause offers the following subscription plans:</p>
<ul>
    <li><strong>Free Trial:</strong> 14-day unlimited access for new users.</li>
    <li><strong>Individual (KSh 8,500/month):</strong> Up to 50 documents per month for solo practitioners.</li>
    <li><strong>Team (KSh 6,500/user/month):</strong> Up to 100 documents per month, minimum 3 seats, with team features.</li>
    <li><strong>Enterprise (KSh 5,000/user/month):</strong> Unlimited documents, minimum 10 seats, SSO, and API access.</li>
</ul>

<h3>5.2 Payments</h3>
<ul>
    <li>All payments are processed via <strong>M-Pesa</strong> (Safaricom Daraja API).</li>
    <li>Prices are quoted in <strong>Kenya Shillings (KSh)</strong> and are inclusive of applicable taxes unless otherwise stated.</li>
    <li>Subscriptions renew automatically every 30 days. You will receive an STK push prompt for each renewal.</li>
    <li>Failed payments may result in temporary service suspension until payment is resolved.</li>
</ul>

<h3>5.3 Refunds</h3>
<p>Subscription payments are generally non-refundable. However, we may consider refund requests on a case-by-case basis if the Platform was materially unavailable during your billing period. Contact support@smartclause.net for refund inquiries.</p>

<h2>6. Acceptable Use</h2>
<p>You agree to use the Platform only for lawful purposes and in accordance with these Terms. You must <strong>not</strong>:</p>
<ul>
    <li>Use the Platform for any illegal activity or to facilitate illegal transactions</li>
    <li>Upload or generate content that is defamatory, obscene, or infringes on any third party's rights</li>
    <li>Attempt to gain unauthorized access to other users' data or accounts</li>
    <li>Interfere with or disrupt the Platform's infrastructure or security</li>
    <li>Use automated tools (bots, scrapers) to access the Platform without authorization</li>
    <li>Reverse-engineer, decompile, or attempt to extract the Platform's source code</li>
    <li>Resell or redistribute access to the Platform without written authorization</li>
</ul>

<h2>7. Intellectual Property</h2>
<h3>7.1 Platform IP</h3>
<p>All intellectual property in the Platform — including the software, design, trademarks, and documentation — belongs to SmartClause. These Terms do not grant you any ownership rights in the Platform.</p>

<h3>7.2 Your Content</h3>
<p>You retain ownership of all legal documents, matters, and clauses you create using the Platform ("Your Content"). By using the Platform, you grant SmartClause a limited, non-exclusive licence to store, process, and display Your Content solely for the purpose of providing the services.</p>

<h3>7.3 AI-Generated Content</h3>
<p>Documents and suggestions generated by the AI assistant are provided as drafts and reference material. You are solely responsible for reviewing, editing, and validating any AI-generated content before use in legal proceedings or transactions.</p>

<h2>8. Disclaimer — Not Legal Advice</h2>
<div class="legal-highlight">
<p><strong>SmartClause is a productivity tool, not a law firm.</strong> The Platform does not provide legal advice, legal opinions, or attorney-client representation. AI-generated content is produced by machine learning models and may contain errors, omissions, or inaccuracies. You must independently verify all documents and exercise professional judgement before relying on any output from the Platform.</p>
</div>

<h2>9. Limitation of Liability</h2>
<p>To the maximum extent permitted by Kenyan law:</p>
<ul>
    <li>SmartClause is provided on an <strong>"as is"</strong> and <strong>"as available"</strong> basis.</li>
    <li>We do not warrant that the Platform will be uninterrupted, error-free, or free from viruses or harmful components.</li>
    <li>We shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including loss of profits, data, or business opportunities.</li>
    <li>Our total aggregate liability for any claims arising from your use of the Platform shall not exceed the total fees paid by you to SmartClause in the 12 months preceding the claim.</li>
</ul>

<h2>10. Indemnification</h2>
<p>You agree to indemnify, defend, and hold harmless SmartClause, its directors, officers, and employees from any claims, losses, or damages (including legal fees) arising out of your breach of these Terms, misuse of the Platform, or violation of applicable law.</p>

<h2>11. Termination</h2>
<ul>
    <li>You may close your account at any time by contacting support@smartclause.net.</li>
    <li>We may suspend or terminate your access for breach of these Terms, non-payment, or any activity that threatens the security or integrity of the Platform.</li>
    <li>Upon termination, your right to use the Platform ceases immediately. We will retain your data in accordance with our Privacy Policy and applicable legal retention requirements.</li>
</ul>

<h2>12. Governing Law &amp; Dispute Resolution</h2>
<ul>
    <li>These Terms are governed by and construed in accordance with the <strong>laws of the Republic of Kenya</strong>.</li>
    <li>Any disputes arising from these Terms shall first be resolved through good-faith negotiation.</li>
    <li>If negotiation fails, disputes shall be referred to <strong>arbitration</strong> under the Arbitration Act (Cap. 49, Laws of Kenya), administered by the Nairobi Centre for International Arbitration (NCIA).</li>
    <li>The courts of Kenya shall have jurisdiction over any matters that cannot be resolved through arbitration.</li>
</ul>

<h2>13. Modifications to These Terms</h2>
<p>We reserve the right to amend these Terms at any time. Material changes will be notified via email or an in-app banner at least 14 days before they take effect. Continued use of the Platform after the effective date constitutes acceptance of the revised Terms.</p>

<h2>14. Severability</h2>
<p>If any provision of these Terms is found to be invalid or unenforceable by a court of competent jurisdiction, the remaining provisions shall remain in full force and effect.</p>

<h2>15. Contact Us</h2>
<p>For questions about these Terms, contact:</p>
<ul>
    <li><strong>Email:</strong> support@smartclause.net</li>
    <li><strong>Address:</strong> Nairobi, Kenya</li>
</ul>
</div>
""", unsafe_allow_html=True)

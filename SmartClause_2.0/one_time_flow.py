import os
import tempfile
from copy import deepcopy
from typing import Dict, Any

import streamlit as st
from bs4 import BeautifulSoup

from analytics import Analytics
from database import DatabaseManager
from document_editor import _html_to_docx
from document_generator import DocumentGenerator
from mpesa_handler import MpesaHandler
from payment_flow import PaymentFlowManager


ONE_TIME_PRICES = {
    "Agreement": 1500,
    "Affidavit": 1000,
    "Will": 750,
    "Power of Attorney": 1200,
}


def _init_state() -> None:
    defaults = {
        "ot_generated_html": "",
        "ot_generated_text": "",
        "ot_checkout_request_id": "",
        "ot_payment_verified": False,
        "ot_doc_type": "Agreement",
        "ot_subtype": "",
        "ot_client_name": "",
        "ot_key_terms": "",
        "ot_phone": "",
        "ot_email": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _build_generation_payload(doc_type: str, subtype: str, client_name: str, key_terms: str) -> Dict[str, Any]:
    return {
        "matter": {
            "name": f"One-Time {doc_type}",
            "client": client_name.strip() or "[Client Name]",
            "jurisdiction": "Kenya",
        },
        "document": {
            "type": doc_type,
            "subtype": subtype.strip(),
            "variables": {
                "client_name": client_name.strip() or "[Client Name]",
                "special_instructions": key_terms.strip(),
            },
        },
    }


def _get_partial_preview(html: str) -> str:
    text = BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)
    st.session_state["ot_generated_text"] = text
    if not text:
        return "No preview available yet."
    return text[:1200] + ("..." if len(text) > 1200 else "")


def _sanitize_preview_html(html: str) -> str:
    """Strip scripts/event handlers before rendering preview."""
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup.find_all("script"):
        tag.decompose()
    for tag in soup.find_all():
        attrs_to_remove = [a for a in tag.attrs.keys() if a.lower().startswith("on")]
        for attr in attrs_to_remove:
            del tag.attrs[attr]
    return str(soup)


def _build_gated_html_preview(html: str, max_text_chars: int = 1600) -> str:
    """
    Preserve document formatting while exposing only a partial snippet.
    This keeps full content server-gated pre-payment.
    """
    if not html.strip():
        return "<p>No preview available yet.</p>"

    sanitized = BeautifulSoup(_sanitize_preview_html(html), "html.parser")
    source_root = sanitized.body if sanitized.body else sanitized

    wrapper = BeautifulSoup("<div></div>", "html.parser")
    out = wrapper.div
    consumed = 0

    for child in source_root.children:
        child_text = child.get_text(" ", strip=True) if hasattr(child, "get_text") else str(child).strip()
        if not child_text:
            continue
        consumed += len(child_text)
        out.append(deepcopy(child))
        if consumed >= max_text_chars:
            break

    if consumed >= max_text_chars:
        out.append(wrapper.new_tag("p"))
        out.p.string = "..."

    rendered = "".join(str(c) for c in out.contents).strip()
    return rendered or "<p>No preview available yet.</p>"


def _build_docx_bytes(html: str, doc_type: str) -> bytes:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp_path = tmp_file.name
    tmp_file.close()
    try:
        _html_to_docx(html, tmp_path, f"One-Time {doc_type}")
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def render_one_time_flow() -> None:
    _init_state()
    Analytics().track_page_visit("OneTimeDocument")

    st.markdown(
        """
        <head>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-197JT7ZFHD"></script>
        <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('config', 'G-197JT7ZFHD');
        </script>
        </head>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        .ot-shell {
            background: var(--sc-bg);
        }
        .ot-shell .sc-main-header {
            margin-bottom: 22px !important;
        }
        .ot-shell .sc-header-left {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .ot-shell .sc-page-title {
            font-size: 34px !important;
            line-height: 1.1;
            margin: 0 !important;
        }
        .ot-section {
            background: var(--sc-surface);
            border: 1px solid var(--sc-border);
            border-radius: var(--sc-radius);
            padding: 20px 24px;
            margin-bottom: 16px;
        }
        .ot-muted {
            color: var(--sc-text-muted);
            margin: 0;
            font-size: 18px;
            line-height: 1.35;
        }
        .ot-link {
            display: inline-block;
            margin-top: 10px;
            color: var(--sc-accent) !important;
            text-decoration: none;
            font-size: 13px;
        }
        .ot-link:hover {
            color: var(--sc-accent-hover) !important;
            text-decoration: underline;
        }
        .ot-label {
            color: var(--sc-text);
            font-weight: 600;
            margin-bottom: 8px;
        }
        .ot-price {
            background: rgba(75, 158, 255, 0.12);
            border: 1px solid rgba(75, 158, 255, 0.28);
            border-radius: var(--sc-radius-sm);
            color: #CFE2FF;
            padding: 12px 16px;
            margin-bottom: 0;
            font-weight: 600;
            min-width: 180px;
            text-align: center;
            font-size: 16px;
        }
        .ot-price-row {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 14px;
        }
        .ot-subtitle {
            font-size: 17px;
            font-weight: 700;
            color: var(--sc-text);
            margin: 0;
        }
        .ot-preview {
            user-select: none;
            -webkit-user-select: none;
            border: 1px solid var(--sc-border);
            border-radius: var(--sc-radius-sm);
            padding: 14px;
            background: #141821;
            white-space: pre-wrap;
        }
        .ot-preview * {
            user-select: none;
            -webkit-user-select: none;
            pointer-events: none;
        }
        .ot-preview-gated {
            max-height: 420px;
            overflow: hidden;
            position: relative;
            filter: blur(0.8px);
            opacity: 0.96;
        }
        .ot-preview-gated::after {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 70px;
            background: linear-gradient(to bottom, rgba(20,24,33,0), rgba(20,24,33,1));
        }
        div[data-testid="stButton"] > button,
        button[kind="primary"],
        button[kind="secondary"],
        div[data-testid="stLinkButton"] > a {
            border-radius: var(--sc-radius-sm) !important;
            font-weight: 600 !important;
            border: 1px solid var(--sc-accent) !important;
            background: var(--sc-accent) !important;
            color: white !important;
            box-shadow: none !important;
        }
        div[data-testid="stButton"] > button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        div[data-testid="stLinkButton"] > a:hover {
            border-color: var(--sc-accent-hover) !important;
            background: var(--sc-accent-hover) !important;
            color: white !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"],
        div[data-testid="stLinkButton"] > a[kind="secondary"] {
            background: rgba(255, 255, 255, 0.07) !important;
            border: 1px solid var(--sc-border) !important;
            color: var(--sc-text) !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover,
        div[data-testid="stLinkButton"] > a[kind="secondary"]:hover {
            background: rgba(255, 255, 255, 0.13) !important;
            border-color: #3D4350 !important;
        }
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div {
            border-radius: var(--sc-radius-sm) !important;
            border-color: var(--sc-border) !important;
            background: #161A22 !important;
        }
        .stAlert,
        .element-container .stMarkdown > div:has(.ot-preview),
        .ot-section,
        .ot-preview {
            border-radius: var(--sc-radius-sm) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="ot-shell">
            <div class="sc-main-header">
                <div class="sc-header-left">
                    <div class="sc-page-title">One-Time Legal Document</div>
                    <p class="ot-muted">Generate quickly, pay via M-Pesa, then download your DOCX.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "Back to full SmartClause login",
        "/?show_auth=true",
        type="secondary",
        use_container_width=False,
    )
    st.markdown('<div class="ot-shell">', unsafe_allow_html=True)

    st.markdown('<div class="ot-section">', unsafe_allow_html=True)
    current_price = ONE_TIME_PRICES.get(st.session_state.get("ot_doc_type", "Agreement"), 0)
    st.markdown(f"<div class='ot-price-row'><div class='ot-price'>Price: KES {current_price:,}</div></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.3, 1])
    with col1:
        selected_doc_type = st.selectbox(
            "Document Type",
            list(ONE_TIME_PRICES.keys()),
            key="ot_doc_type",
        )
        st.session_state["ot_subtype"] = st.text_input("Subtype (optional)", value=st.session_state["ot_subtype"], placeholder="e.g. Employment Agreement, General Affidavit")
        st.session_state["ot_client_name"] = st.text_input("Client/Party Name", value=st.session_state["ot_client_name"])
        st.session_state["ot_key_terms"] = st.text_area("Key Terms / Instructions", value=st.session_state["ot_key_terms"], height=140)

    with col2:
        st.session_state["ot_phone"] = st.text_input("M-Pesa Phone Number", value=st.session_state["ot_phone"], placeholder="2547XXXXXXXX")
        st.session_state["ot_email"] = st.text_input("Email (optional)", value=st.session_state["ot_email"], placeholder="for receipt/support")

    generate_btn = st.button("Generate Preview", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if generate_btn:
        if not st.session_state["ot_key_terms"].strip():
            st.error("Add key terms before generating.")
        else:
            generator = DocumentGenerator()
            payload = _build_generation_payload(
                st.session_state["ot_doc_type"],
                st.session_state["ot_subtype"],
                st.session_state["ot_client_name"],
                st.session_state["ot_key_terms"],
            )
            progress_placeholder = st.empty()
            stream_preview_placeholder = st.empty()
            content = ""
            with st.spinner("Generating document..."):
                for idx, chunk in enumerate(generator.generate_document_stream(payload), start=1):
                    content += chunk
                    if idx % 10 == 0:
                        progress_placeholder.info(f"Streaming draft... {len(content):,} characters generated")
                        stream_preview_placeholder.markdown(
                            (
                                "<div class='ot-preview'>"
                                "<strong>PREVIEW ONLY (LIVE)</strong>"
                                f"<div style='margin-top:10px'>{_build_gated_html_preview(content, max_text_chars=1000)}</div>"
                                "</div>"
                            ),
                            unsafe_allow_html=True,
                        )
                st.session_state["ot_generated_html"] = content
                st.session_state["ot_payment_verified"] = False
                st.session_state["ot_checkout_request_id"] = ""
            progress_placeholder.empty()
            stream_preview_placeholder.empty()
            Analytics().track_event("one_time_generation_complete", {"document_type": st.session_state["ot_doc_type"]})
            st.success("Preview generated.")

    st.markdown('<div class="ot-section">', unsafe_allow_html=True)
    st.markdown("<p class='ot-subtitle'>Preview (Server-Gated)</p>", unsafe_allow_html=True)
    preview_html = _build_gated_html_preview(st.session_state["ot_generated_html"])
    st.markdown(
        (
            "<div class='ot-preview'>"
            "<strong>PREVIEW ONLY</strong>"
            f"<div class='ot-preview-gated' style='margin-top:10px'>{preview_html}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.caption("Full text remains locked until payment verification succeeds.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="ot-section">', unsafe_allow_html=True)
    st.markdown("<p class='ot-subtitle'>Pay and Unlock Download</p>", unsafe_allow_html=True)
    pay_col, verify_col = st.columns(2)
    with pay_col:
        if st.button("Pay with M-Pesa", use_container_width=True):
            if not st.session_state["ot_generated_html"]:
                st.error("Generate a preview first.")
            elif not st.session_state["ot_phone"].strip():
                st.error("Enter a valid M-Pesa phone number.")
            else:
                db = DatabaseManager()
                payment_mgr = PaymentFlowManager(db, MpesaHandler())
                result = payment_mgr.initiate_one_time_purchase(
                    document_type=st.session_state["ot_doc_type"],
                    phone_number=st.session_state["ot_phone"],
                    email=st.session_state["ot_email"],
                    user_id=None,
                )
                if result.get("success"):
                    st.session_state["ot_checkout_request_id"] = result.get("checkout_request_id", "")
                    Analytics().track_event("one_time_payment_initiated", {"document_type": st.session_state["ot_doc_type"]})
                    st.success(result.get("message", "Payment initiated."))
                else:
                    st.error(result.get("message", "Could not initiate payment."))

    with verify_col:
        if st.button("Verify Payment", use_container_width=True):
            checkout_id = st.session_state.get("ot_checkout_request_id", "")
            if not checkout_id:
                st.error("Start payment first.")
            else:
                db = DatabaseManager()
                payment_mgr = PaymentFlowManager(db, MpesaHandler())
                with st.spinner("Verifying payment. Please approve STK prompt on your phone..."):
                    result = payment_mgr.verify_one_time_payment(checkout_id, max_attempts=18, delay=5)
                if result.get("success"):
                    st.session_state["ot_payment_verified"] = True
                    Analytics().track_event("one_time_payment_verified", {"document_type": st.session_state["ot_doc_type"]})
                    st.success("Payment verified. Download unlocked.")
                else:
                    st.error(result.get("message", "Payment not yet confirmed."))

    if st.session_state.get("ot_payment_verified") and st.session_state.get("ot_generated_html"):
        docx_bytes = _build_docx_bytes(st.session_state["ot_generated_html"], st.session_state["ot_doc_type"])
        safe_name = st.session_state["ot_doc_type"].replace(" ", "_")
        st.download_button(
            "Download DOCX",
            data=docx_bytes,
            file_name=f"SmartClause_{safe_name}_OneTime.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
            key="ot_download_docx_btn",
        )
    st.markdown("</div></div>", unsafe_allow_html=True)

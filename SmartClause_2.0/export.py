import streamlit as st

def render_exports():
    # Page header
    st.markdown("""
<div class="sc-main-header">
  <div class="sc-header-left">
    <div class="sc-page-title">Exports</div>
    <div class="sc-page-subtitle">Download clean or marked-up versions of your documents</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Top export tiles
    st.markdown("""
<div class="export-grid">
  <div class="export-tile">
    <div class="export-tile-left">
      <div class="export-icon export-icon-blue">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <rect x="4" y="3" width="16" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/>
          <path d="M8 7h8M8 11h8M8 15h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <div class="export-title">Clean Export</div>
        <div class="export-sub">Export the current version without any markup or tracked changes</div>
      </div>
    </div>
    <div class="export-actions">
      <button class="sc-btn sc-btn-primary sc-btn-small">DOCX</button>
      <button class="sc-btn sc-btn-primary sc-btn-small">PDF</button>
    </div>
  </div>

  <div class="export-tile">
    <div class="export-tile-left">
      <div class="export-icon export-icon-amber">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="M6 6h12v12H6z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M8 12h8M12 8v8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <div class="export-title">Redline Export</div>
        <div class="export-sub">Export with tracked changes showing differences between versions</div>
      </div>
    </div>
    <div class="export-actions">
      <button class="sc-btn sc-btn-primary sc-btn-small">DOCX</button>
      <button class="sc-btn sc-btn-primary sc-btn-small">PDF</button>
    </div>
  </div>

  <div class="export-tile">
    <div class="export-tile-left">
      <div class="export-icon export-icon-green">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <rect x="4" y="5" width="16" height="14" rx="2" stroke="currentColor" stroke-width="1.5"/>
          <path d="M8 9h8M8 13h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <div class="export-title">Signing Pack</div>
        <div class="export-sub">Complete package with document, cover email, and execution pages</div>
      </div>
    </div>
    <div class="export-actions">
      <button class="sc-btn sc-btn-primary sc-btn-small">Export Pack</button>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Section: Recent Exports
    st.markdown('<div class="sc-section-title sc-section-title--indent mt-20">RECENT EXPORTS</div>', unsafe_allow_html=True)

    rows = [
        {
            "title": "Acme Corp - Share Purchase Agreement",
            "sub": "Clean DOCX",
            "version": "v3",
            "time": "2 hours ago",
            "status": "Ready",
        },
        {
            "title": "Acme Corp - Share Purchase Agreement",
            "sub": "Redline DOCX",
            "version": "v2 → v3",
            "time": "2 hours ago",
            "status": "Ready",
        },
        {
            "title": "TechStart Inc - Shareholders Agreement",
            "sub": "Signing Pack",
            "version": "v1",
            "time": "1 day ago",
            "status": "Ready",
        },
    ]

    for r in rows:
        st.markdown(f"""
<div class="export-row">
  <div class="export-row-left">
    <div class="export-doc-icon">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <rect x="4" y="3" width="16" height="18" rx="2" stroke="currentColor" stroke-width="1.5"/>
        <path d="M8 7h8M8 11h8M8 15h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </div>
    <div class="export-row-text">
      <div class="export-row-title">{r["title"]}</div>
      <div class="export-row-sub">
        {r["sub"]}
        <span class="sc-dot">•</span>
        <span class="sc-badge-mini">{r["version"]}</span>
        <span class="sc-dot">•</span>
        {r["time"]}
      </div>
    </div>
  </div>
  <div class="export-row-right">
    <span class="status-ready">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M20 6l-11 11-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      {r["status"]}
    </span>
    <button class="sc-btn sc-btn-primary export-download">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M12 3v12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M7 11l5 5 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="4" y="18" width="16" height="3" rx="1.5" fill="currentColor"/>
      </svg>
      <span>Download</span>
    </button>
  </div>
</div>
""", unsafe_allow_html=True)
"""
Search functionality for SmartClause
Handles search queries across matters, documents, and clauses
"""

import streamlit as st
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re
import streamlit as st

def perform_search(db, query: str, view: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Perform search across relevant entities based on current view.
    Returns categorized results.
    """
    if not query or len(query.strip()) < 2:
        return {}
    
    query = query.strip()
    results = {}
    
    # Search based on current view
    if view == "clause_library":
        # Only search clauses in clause library view
        results["clauses"] = search_clauses(db, query)
    else:
        # In matters view, search matters and documents
        results["matters"] = search_matters(db, query)
        results["documents"] = search_documents(db, query)
        
        # Optionally include clauses in global search
        clause_results = search_clauses(db, query)
        if clause_results:
            results["clauses"] = clause_results
    
    return results


def search_matters(db, query: str) -> List[Dict[str, Any]]:
    """Search matters by name, client name, or internal reference."""
    try:
        # Get all matters (limited set)
        matters = db.get_matters(limit=200)
        
        # Filter in memory for speed
        query_lower = query.lower()
        matches = []
        
        for matter in matters:
            # Search in name, client name, counterparty, internal reference
            searchable_text = " ".join([
                matter.get("name", "").lower(),
                matter.get("client_name", "").lower(),
                matter.get("counterparty", "").lower() if matter.get("counterparty") else "",
                matter.get("internal_reference", "").lower() if matter.get("internal_reference") else "",
                matter.get("matter_type", "").lower()
            ])
            
            if query_lower in searchable_text:
                # Add relevance score
                matter["_relevance"] = calculate_relevance(query_lower, searchable_text)
                matches.append(matter)
        
        # Sort by relevance
        matches.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
        
        return matches[:10]  # Return top 10 matches
    
    except Exception as e:
        st.error(f"Error searching matters: {e}")
        return []


def search_documents(db, query: str) -> List[Dict[str, Any]]:
    """Search documents by title or type."""
    try:
        # Get all matters first
        matters = db.get_matters(limit=200)
        matter_ids = [m["id"] for m in matters]
        
        if not matter_ids:
            return []
        
        # Get documents for these matters
        all_documents = []
        for matter_id in matter_ids:
            docs = db.get_documents(matter_id, include_content=False)
            # Attach matter info for display
            matter = next((m for m in matters if m["id"] == matter_id), None)
            for doc in docs:
                doc["_matter_name"] = matter["name"] if matter else "Unknown"
                doc["_client_name"] = matter["client_name"] if matter else "Unknown"
            all_documents.extend(docs)
        
        # Filter in memory
        query_lower = query.lower()
        matches = []
        
        for doc in all_documents:
            searchable_text = " ".join([
                doc.get("title", "").lower(),
                doc.get("document_type", "").lower(),
                doc.get("document_subtype", "").lower() if doc.get("document_subtype") else "",
                doc.get("_matter_name", "").lower()
            ])
            
            if query_lower in searchable_text:
                doc["_relevance"] = calculate_relevance(query_lower, searchable_text)
                matches.append(doc)
        
        # Sort by relevance and recency
        matches.sort(key=lambda x: (x.get("_relevance", 0), x.get("updated_at", "")), reverse=True)
        
        return matches[:10]
    
    except Exception as e:
        st.error(f"Error searching documents: {e}")
        return []


def search_clauses(db, query: str) -> List[Dict[str, Any]]:
    """Search clauses by title, category, or content."""
    try:
        # Get all clauses
        clauses = db.get_clauses(include_system=True)
        
        # Filter in memory
        query_lower = query.lower()
        matches = []
        
        for clause in clauses:
            searchable_text = " ".join([
                clause.get("title", "").lower(),
                clause.get("category", "").lower(),
                clause.get("content_plain", "").lower()[:500],  # First 500 chars of content
                " ".join(clause.get("tags", [])).lower()
            ])
            
            if query_lower in searchable_text:
                clause["_relevance"] = calculate_relevance(query_lower, searchable_text)
                matches.append(clause)
        
        # Sort by relevance
        matches.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
        
        return matches[:10]
    
    except Exception as e:
        st.error(f"Error searching clauses: {e}")
        return []


def calculate_relevance(query: str, text: str) -> float:
    """
    Calculate relevance score for search results.
    Higher score = more relevant.
    """
    score = 0.0
    
    # Exact match in text
    if query in text:
        score += 10.0
    
    # Match at start of text (higher weight)
    if text.startswith(query):
        score += 20.0
    
    # Word boundary matches
    words = query.split()
    for word in words:
        if len(word) > 2:  # Skip very short words
            # Count occurrences
            count = text.count(word)
            score += count * 2.0
    
    return score


def get_time_ago(dt_str: str) -> str:
    """Convert ISO datetime string to relative time."""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Just now"
    except:
        return ""


def render_search_results(results: Dict[str, List[Dict[str, Any]]], query: str):
    """
    Render search results in a modal dialog.
    """
    total_results = sum(len(items) for items in results.values())
    
    if total_results == 0:
        st.info(f"No results found for '{query}'")
        return
    
    # Display results by category
    if "matters" in results and results["matters"]:
        st.markdown("### 📁 Matters")
        for matter in results["matters"]:
            render_matter_result(matter)
        st.markdown("---")
    
    if "documents" in results and results["documents"]:
        st.markdown("### 📄 Documents")
        for doc in results["documents"]:
            render_document_result(doc)
        st.markdown("---")
    
    if "clauses" in results and results["clauses"]:
        st.markdown("### 📋 Clauses")
        for clause in results["clauses"]:
            render_clause_result(clause)


def render_matter_result(matter: Dict[str, Any]):
    """Render a single matter search result."""
    session_param = get_session_param()
    
    st.markdown(f"""
    <a href="?view=matter_details&matter_id={matter['id']}{session_param}" target="_self" 
       style="text-decoration: none; display: block; margin-bottom: 12px;">
        <div style="
            padding: 12px 16px;
            background: rgba(75, 158, 255, 0.05);
            border-left: 3px solid #4B9EFF;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        " onmouseover="this.style.background='rgba(75, 158, 255, 0.1)'" 
           onmouseout="this.style.background='rgba(75, 158, 255, 0.05)'">
            <div style="font-weight: 600; color: #FFFFFF; margin-bottom: 4px;">
                {matter['name']}
            </div>
            <div style="font-size: 13px; color: #9BA1B0; margin-bottom: 4px;">
                {matter['client_name']}
            </div>
            <div style="font-size: 12px; color: #6B7280;">
                {matter.get('matter_type', 'General')} • {matter['jurisdiction']} • 
                {get_time_ago(matter['updated_at'])}
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)


def render_document_result(doc: Dict[str, Any]):
    """Render a single document search result."""
    session_param = get_session_param()
    
    status_colors = {
        "generating": "#FFA500",
        "ready": "#4B9EFF",
        "error": "#EF4444"
    }
    
    status_color = status_colors.get(doc.get("status", "ready"), "#4B9EFF")
    
    st.markdown(f"""
    <a href="?view=editor&document_id={doc['id']}{session_param}" target="_self"
       style="text-decoration: none; display: block; margin-bottom: 12px;">
        <div style="
            padding: 12px 16px;
            background: rgba(139, 92, 246, 0.05);
            border-left: 3px solid #8B5CF6;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        " onmouseover="this.style.background='rgba(139, 92, 246, 0.1)'" 
           onmouseout="this.style.background='rgba(139, 92, 246, 0.05)'">
            <div style="font-weight: 600; color: #FFFFFF; margin-bottom: 4px;">
                {doc['title']}
            </div>
            <div style="font-size: 13px; color: #9BA1B0; margin-bottom: 4px;">
                Matter: {doc.get('_matter_name', 'Unknown')} • {doc.get('_client_name', '')}
            </div>
            <div style="font-size: 12px; color: #6B7280;">
                <span style="color: {status_color}; font-weight: 500;">●</span>
                {doc.get('document_type', 'Document')} • {get_time_ago(doc['updated_at'])}
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)


def render_clause_result(clause: Dict[str, Any]):
    """Render a single clause search result."""
    preview = clause.get('preview', clause.get('content_plain', ''))[:150]
    if len(preview) == 150:
        preview += "..."
    
    # Create a button for inserting clause (if in editor)
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"""
        <div style="
            padding: 12px 16px;
            background: rgba(16, 185, 129, 0.05);
            border-left: 3px solid #10B981;
            border-radius: 6px;
            margin-bottom: 12px;
        ">
            <div style="font-weight: 600; color: #FFFFFF; margin-bottom: 4px;">
                {clause['title']}
            </div>
            <div style="font-size: 13px; color: #9BA1B0; margin-bottom: 6px;">
                {clause['category']}
            </div>
            <div style="font-size: 12px; color: #6B7280; line-height: 1.5;">
                {preview}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.session_state.get("current_view") == "editor":
            if st.button("Insert", key=f"insert_clause_{clause['id']}", use_container_width=True):
                # Store clause to insert
                st.session_state["clause_to_insert"] = clause
                st.rerun()


def get_session_param() -> str:
    """Get session parameter for URLs."""
    session_cookie = st.session_state.get("session_cookie", "")
    if session_cookie:
        return f"&session={session_cookie}"
    return ""


def render_search_modal(db, view: str):
    """
    Render search modal using Streamlit's dialog feature.
    """
    if not st.session_state.get("show_search_modal", False):
        return
    
    @st.dialog("🔍 Search", width="large")
    def search_dialog():
        # Search input
        search_query = st.text_input(
            "Search",
            placeholder=f"Search {'clauses' if view == 'clause_library' else 'matters, documents, and clauses'}...",
            key="search_modal_input",
            label_visibility="collapsed"
        )
        
        # Perform search when query changes
        if search_query and len(search_query) >= 2:
            with st.spinner("Searching..."):
                results = perform_search(db, search_query, view)
                render_search_results(results, search_query)
        elif search_query:
            st.info("Please enter at least 2 characters to search")
        
        # Close button
        if st.button("Close", use_container_width=True, type="secondary"):
            st.session_state["show_search_modal"] = False
            st.rerun()
    
    search_dialog()
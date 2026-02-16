"""
Advanced features for the WYSIWYG editor:
- Clause insertion from library
- Smart formatting for legal documents
- Find & replace
- Document outline/navigation
- Comments and annotations
"""

import streamlit as st
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup


def insert_clause_from_library() -> str:
    """
    Generate HTML for clause insertion modal.
    Returns JavaScript to insert selected clause.
    """
    # This would integrate with your clause_library.py
    clauses = [
        {
            "id": "governing_law_kenya",
            "title": "Governing Law (Kenya)",
            "content": "<p><strong>Governing Law.</strong> This Agreement shall be governed by and construed in accordance with the laws of the Republic of Kenya.</p>"
        },
        {
            "id": "indemnification",
            "title": "Indemnification",
            "content": "<p><strong>Indemnification.</strong> The Seller shall indemnify and hold harmless the Purchaser against all losses, damages, costs and expenses arising from any breach of the warranties contained herein.</p>"
        },
        {
            "id": "confidentiality",
            "title": "Confidentiality",
            "content": "<p><strong>Confidentiality.</strong> Each party undertakes to keep confidential all information received from the other party pursuant to this Agreement, subject to applicable law including the Data Protection Act, 2019.</p>"
        }
    ]
    
    js_clauses = "const clauses = " + str(clauses).replace("'", '"') + ";"
    
    modal_html = """
    <div id="clauseModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000;">
        <div style="background:#1A1D24; border:1px solid #252930; border-radius:12px; max-width:600px; margin:100px auto; padding:24px;">
            <h3 style="color:#FFFFFF; margin-bottom:16px;">Insert Clause</h3>
            <div id="clauseList"></div>
            <button onclick="closeClauseModal()" style="margin-top:16px; padding:8px 16px; background:#252930; color:#FFFFFF; border:none; border-radius:6px; cursor:pointer;">Cancel</button>
        </div>
    </div>
    """
    
    js_code = js_clauses + """
    function openClauseModal() {
        const modal = document.getElementById('clauseModal');
        const list = document.getElementById('clauseList');
        list.innerHTML = '';
        
        clauses.forEach(clause => {
            const div = document.createElement('div');
            div.style.cssText = 'padding:12px; margin:8px 0; background:#13151A; border:1px solid #252930; border-radius:8px; cursor:pointer;';
            div.innerHTML = `<strong style="color:#FFFFFF;">${clause.title}</strong>`;
            div.onclick = () => insertClause(clause.content);
            list.appendChild(div);
        });
        
        modal.style.display = 'block';
    }
    
    function closeClauseModal() {
        document.getElementById('clauseModal').style.display = 'none';
    }
    
    function insertClause(content) {
        document.execCommand('insertHTML', false, content);
        closeClauseModal();
        editor.focus();
    }
    """
    
    return modal_html, js_code


def generate_find_replace_html() -> str:
    """Generate find and replace UI."""
    return """
    <div id="findReplaceBar" style="display:none; position:fixed; top:80px; right:20px; background:#1A1D24; border:1px solid #252930; border-radius:8px; padding:16px; z-index:999; min-width:320px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <h4 style="color:#FFFFFF; margin:0;">Find & Replace</h4>
            <button onclick="closeFindReplace()" style="background:transparent; border:none; color:#9BA1B0; cursor:pointer; font-size:18px;">×</button>
        </div>
        
        <input type="text" id="findInput" placeholder="Find..." style="width:100%; padding:8px; margin-bottom:8px; background:#13151A; border:1px solid #252930; border-radius:6px; color:#FFFFFF;">
        
        <input type="text" id="replaceInput" placeholder="Replace with..." style="width:100%; padding:8px; margin-bottom:12px; background:#13151A; border:1px solid #252930; border-radius:6px; color:#FFFFFF;">
        
        <div style="display:flex; gap:8px;">
            <button onclick="findNext()" style="flex:1; padding:8px; background:#4B9EFF; color:#FFFFFF; border:none; border-radius:6px; cursor:pointer; font-size:13px;">Find Next</button>
            <button onclick="replaceOne()" style="flex:1; padding:8px; background:#252930; color:#FFFFFF; border:none; border-radius:6px; cursor:pointer; font-size:13px;">Replace</button>
            <button onclick="replaceAll()" style="flex:1; padding:8px; background:#252930; color:#FFFFFF; border:none; border-radius:6px; cursor:pointer; font-size:13px;">Replace All</button>
        </div>
        
        <div id="findResults" style="margin-top:8px; font-size:12px; color:#9BA1B0;"></div>
    </div>
    
    <script>
        let currentMatch = 0;
        let matches = [];
        
        function openFindReplace() {
            document.getElementById('findReplaceBar').style.display = 'block';
            document.getElementById('findInput').focus();
        }
        
        function closeFindReplace() {
            document.getElementById('findReplaceBar').style.display = 'none';
            clearHighlights();
        }
        
        function clearHighlights() {
            const editor = document.getElementById('editor');
            const highlighted = editor.querySelectorAll('.search-highlight');
            highlighted.forEach(el => {
                const parent = el.parentNode;
                parent.replaceChild(document.createTextNode(el.textContent), el);
                parent.normalize();
            });
        }
        
        function findNext() {
            const searchTerm = document.getElementById('findInput').value;
            if (!searchTerm) return;
            
            clearHighlights();
            const editor = document.getElementById('editor');
            const text = editor.textContent;
            const regex = new RegExp(searchTerm, 'gi');
            matches = [];
            let match;
            
            while ((match = regex.exec(text)) !== null) {
                matches.push(match.index);
            }
            
            if (matches.length > 0) {
                highlightMatches(searchTerm);
                document.getElementById('findResults').textContent = `Found ${matches.length} match(es)`;
            } else {
                document.getElementById('findResults').textContent = 'No matches found';
            }
        }
        
        function highlightMatches(searchTerm) {
            const editor = document.getElementById('editor');
            const regex = new RegExp(`(${searchTerm})`, 'gi');
            
            function highlightNode(node) {
                if (node.nodeType === 3) { // Text node
                    const parent = node.parentNode;
                    const text = node.textContent;
                    if (regex.test(text)) {
                        const fragment = document.createDocumentFragment();
                        const parts = text.split(regex);
                        
                        parts.forEach((part, i) => {
                            if (i % 2 === 1) {
                                const span = document.createElement('span');
                                span.className = 'search-highlight';
                                span.style.backgroundColor = '#F59E0B';
                                span.style.color = '#000000';
                                span.textContent = part;
                                fragment.appendChild(span);
                            } else {
                                fragment.appendChild(document.createTextNode(part));
                            }
                        });
                        
                        parent.replaceChild(fragment, node);
                    }
                } else if (node.nodeType === 1 && node.childNodes) {
                    Array.from(node.childNodes).forEach(child => highlightNode(child));
                }
            }
            
            highlightNode(editor);
        }
        
        function replaceOne() {
            const searchTerm = document.getElementById('findInput').value;
            const replaceTerm = document.getElementById('replaceInput').value;
            if (!searchTerm) return;
            
            const editor = document.getElementById('editor');
            const content = editor.innerHTML;
            const regex = new RegExp(searchTerm, 'i');
            editor.innerHTML = content.replace(regex, replaceTerm);
            
            sendUpdate();
            findNext();
        }
        
        function replaceAll() {
            const searchTerm = document.getElementById('findInput').value;
            const replaceTerm = document.getElementById('replaceInput').value;
            if (!searchTerm) return;
            
            const editor = document.getElementById('editor');
            const content = editor.innerHTML;
            const regex = new RegExp(searchTerm, 'gi');
            const count = (content.match(regex) || []).length;
            editor.innerHTML = content.replace(regex, replaceTerm);
            
            sendUpdate();
            clearHighlights();
            document.getElementById('findResults').textContent = `Replaced ${count} occurrence(s)`;
        }
        
        // Keyboard shortcut: Ctrl+F
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                openFindReplace();
            }
            if (e.key === 'Escape') {
                closeFindReplace();
            }
        });
    </script>
    """




def generate_legal_formatting_tools() -> str:
    """Generate legal-specific formatting tools."""
    return """
    <script>
        // Insert numbered clause
        function insertNumberedClause() {
            const editor = document.getElementById('editor');
            const clauseNum = prompt('Clause number (e.g., 1.1):');
            if (clauseNum) {
                const clause = `<p><strong>${clauseNum}</strong> [Clause content]</p>`;
                document.execCommand('insertHTML', false, clause);
            }
        }
        
        // Insert definition
        function insertDefinition() {
            const term = prompt('Defined term:');
            if (term) {
                const definition = `<p><strong>"${term}"</strong> means [definition];</p>`;
                document.execCommand('insertHTML', false, definition);
            }
        }
        
        // Insert cross-reference
        function insertCrossRef() {
            const ref = prompt('Section reference (e.g., 3.2):');
            if (ref) {
                const crossref = `<a href="#clause-${ref}" style="color:#4B9EFF;">Section ${ref}</a>`;
                document.execCommand('insertHTML', false, crossref);
            }
        }
        
        // Insert schedule/annex
        function insertSchedule() {
            const scheduleNum = prompt('Schedule number/letter:');
            if (scheduleNum) {
                const schedule = `
                    <div style="page-break-before: always; margin-top: 40px;">
                        <h2 style="text-align: center;">SCHEDULE ${scheduleNum}</h2>
                        <p>[Schedule content]</p>
                    </div>
                `;
                document.execCommand('insertHTML', false, schedule);
            }
        }
        
        // Auto-number clauses
        function autoNumberClauses() {
            const editor = document.getElementById('editor');
            const paragraphs = editor.querySelectorAll('p');
            let mainCounter = 1;
            let subCounter = 1;
            
            paragraphs.forEach(p => {
                const text = p.textContent.trim();
                if (text.startsWith('[')) {
                    p.innerHTML = `<strong>${mainCounter}.${subCounter}</strong> ${text}`;
                    subCounter++;
                } else if (text.length > 50) {
                    subCounter = 1;
                    mainCounter++;
                }
            });
            
            sendUpdate();
        }
        
        // Insert signature block
        function insertSignatureBlock() {
            const parties = prompt('Number of parties:', '2');
            let sigBlock = '<div style="margin-top: 60px;">';
            
            for (let i = 0; i < parseInt(parties); i++) {
                sigBlock += `
                    <div style="margin: 40px 0;">
                        <p style="margin-bottom: 40px;">SIGNED by [Party Name]:</p>
                        <div style="display: flex; gap: 40px;">
                            <div>
                                <p>_________________________</p>
                                <p style="font-size: 12px;">Signature</p>
                            </div>
                            <div>
                                <p>_________________________</p>
                                <p style="font-size: 12px;">Date</p>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            sigBlock += '</div>';
            document.execCommand('insertHTML', false, sigBlock);
        }
    </script>
    """


def generate_comments_system() -> str:
    """Generate a comments/annotations system."""
    return """
    <div id="commentsPanel" style="position:fixed; right:0; top:140px; width:320px; max-height:calc(100vh - 200px); background:#1A1D24; border:1px solid #252930; border-radius:8px 0 0 8px; padding:16px; overflow-y:auto; z-index:997; display:none;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <h4 style="color:#FFFFFF; margin:0; font-size:14px;">Comments</h4>
            <button onclick="toggleCommentsPanel()" style="background:transparent; border:none; color:#9BA1B0; cursor:pointer; font-size:18px;">×</button>
        </div>
        <div id="commentsList"></div>
    </div>
    
    <script>
        let comments = [];
        
        function toggleCommentsPanel() {
            const panel = document.getElementById('commentsPanel');
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            renderComments();
        }
        
        function addCommentToSelection() {
            const sel = window.getSelection();
            if (sel.rangeCount && !sel.isCollapsed) {
                const comment = prompt('Enter your comment:');
                if (comment) {
                    const range = sel.getRangeAt(0);
                    const commentId = 'comment-' + Date.now();
                    
                    const span = document.createElement('span');
                    span.className = 'has-comment';
                    span.setAttribute('data-comment-id', commentId);
                    span.style.cssText = 'background-color: rgba(250, 204, 21, 0.2); border-bottom: 2px dotted #F59E0B; cursor: help;';
                    
                    try {
                        range.surroundContents(span);
                    } catch(e) {
                        alert('Cannot add comment to selection spanning multiple elements');
                        return;
                    }
                    
                    comments.push({
                        id: commentId,
                        text: comment,
                        selectedText: sel.toString(),
                        timestamp: new Date().toISOString(),
                        author: 'User'
                    });
                    
                    span.onclick = () => showCommentPopup(commentId);
                    
                    renderComments();
                    sendUpdate();
                }
            } else {
                alert('Please select text to comment on');
            }
        }
        
        function showCommentPopup(commentId) {
            const comment = comments.find(c => c.id === commentId);
            if (comment) {
                toggleCommentsPanel();
                document.getElementById(commentId).scrollIntoView({ behavior: 'smooth' });
            }
        }
        
        function renderComments() {
            const list = document.getElementById('commentsList');
            list.innerHTML = '';
            
            if (comments.length === 0) {
                list.innerHTML = '<p style="color:#6B7280; font-size:12px;">No comments yet</p>';
                return;
            }
            
            comments.forEach(comment => {
                const div = document.createElement('div');
                div.id = comment.id;
                div.style.cssText = 'padding: 12px; margin: 8px 0; background: #13151A; border-radius: 8px; border-left: 3px solid #F59E0B;';
                
                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <strong style="color: #FFFFFF; font-size: 12px;">${comment.author}</strong>
                        <button onclick="deleteComment('${comment.id}')" style="background: transparent; border: none; color: #9BA1B0; cursor: pointer; font-size: 16px;">×</button>
                    </div>
                    <p style="color: #9BA1B0; font-size: 13px; margin-bottom: 8px;">"${comment.selectedText.substring(0, 50)}${comment.selectedText.length > 50 ? '...' : ''}"</p>
                    <p style="color: #FFFFFF; font-size: 13px;">${comment.text}</p>
                    <p style="color: #6B7280; font-size: 11px; margin-top: 8px;">${new Date(comment.timestamp).toLocaleString()}</p>
                `;
                
                list.appendChild(div);
            });
        }
        
        function deleteComment(commentId) {
            if (confirm('Delete this comment?')) {
                comments = comments.filter(c => c.id !== commentId);
                
                const spans = document.querySelectorAll(`[data-comment-id="${commentId}"]`);
                spans.forEach(span => {
                    const parent = span.parentNode;
                    while (span.firstChild) {
                        parent.insertBefore(span.firstChild, span);
                    }
                    parent.removeChild(span);
                    parent.normalize();
                });
                
                renderComments();
                sendUpdate();
            }
        }
    </script>
    """


def generate_smart_suggestions() -> str:
    """Generate AI-powered smart suggestions for legal drafting."""
    return """
    <script>
        // Smart capitalization for defined terms
        function enforceDefinedTerms() {
            const editor = document.getElementById('editor');
            const definedTerms = [];
            
            // Extract defined terms (words in quotes followed by 'means')
            const regex = /"([^"]+)"\s+means/gi;
            const text = editor.textContent;
            let match;
            
            while ((match = regex.exec(text)) !== null) {
                definedTerms.push(match[1]);
            }
            
            // Highlight undefined capitalized terms
            if (definedTerms.length > 0) {
                console.log('Defined terms found:', definedTerms);
            }
        }
        
        // Check for common legal drafting issues
        function legalStyleCheck() {
            const editor = document.getElementById('editor');
            const text = editor.textContent;
            const issues = [];
            
            // Check for "shall" consistency
            if (text.includes('must') && text.includes('shall')) {
                issues.push('Mixed use of "shall" and "must" - consider consistency');
            }
            
            // Check for ambiguous pronouns
            if (/\b(he|she|it|they)\b/gi.test(text)) {
                issues.push('Consider replacing pronouns with party names for clarity');
            }
            
            // Check for undefined acronyms
            const acronyms = text.match(/\b[A-Z]{2,}\b/g);
            if (acronyms) {
                issues.push(`Acronyms found: ${acronyms.join(', ')} - ensure they are defined`);
            }
            
            if (issues.length > 0) {
                console.log('Style issues:', issues);
                return issues;
            }
            
            return [];
        }
        
        // Suggest clause improvements
        function suggestImprovements() {
            const styleIssues = legalStyleCheck();
            if (styleIssues.length > 0) {
                alert('Style suggestions:\\n\\n' + styleIssues.join('\\n'));
            } else {
                alert('No style issues found!');
            }
        }
    </script>
    """


def integrate_all_features() -> str:
    """Combine all enhancement features into one HTML block."""
    clause_modal, clause_js = insert_clause_from_library()
    
    return f"""
    {clause_modal}
    {generate_find_replace_html()}
    {generate_comments_system()}
    {generate_legal_formatting_tools()}
    {generate_smart_suggestions()}
    
    <script>
    {clause_js}
    </script>
    
    <style>
        .has-comment {{
            position: relative;
        }}
        
        .has-comment:hover::after {{
            content: '💬';
            position: absolute;
            right: -20px;
            top: -5px;
            font-size: 14px;
        }}
    </style>
    """
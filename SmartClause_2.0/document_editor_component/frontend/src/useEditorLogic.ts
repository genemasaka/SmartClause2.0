import { version } from "os";
import { RefObject, useEffect, useMemo } from "react";

interface Clause {
  id: string;
  title: string;
  category: string;
  content: string;
  tags: string[];
  usage_count: number;
  is_pinned: boolean;
  is_system: boolean;
}

interface Comment {
  id: string;
  text: string;
  selectedText: string;
  timestamp: string;
  author: string;
  authorEmail: string;
  resolved: boolean;
}

export const useEditorLogic = (
  editorRef: RefObject<HTMLDivElement>,
  clauses: Clause[] = [],
  versionId: string = ""
) => {
  const clauseModalHtml = useMemo(
    () => `
    <div id="clauseModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; overflow-y: auto;">
        <div style="background:#1A1D24; border:1px solid #252930; border-radius:12px; max-width:800px; margin:50px auto; padding:24px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h3 style="color:#FFFFFF; margin:0;">📚 Insert Clause from Library</h3>
                <button id="closeClauseModalBtn" style="background:transparent; border:none; color:#9BA1B0; cursor:pointer; font-size:24px; padding:0; line-height:1;">×</button>
            </div>
            
            <div style="margin-bottom: 16px;">
                <input type="text" id="clauseSearchInput" placeholder="🔍 Search clauses..." 
                       style="width:100%; padding:10px; background:#13151A; border:1px solid #252930; border-radius:6px; color:#FFFFFF; font-size:14px; margin-bottom:8px;">
                <select id="clauseCategoryFilter" style="width:100%; padding:10px; background:#13151A; border:1px solid #252930; border-radius:6px; color:#FFFFFF; font-size:14px;">
                    <option value="">All Categories</option>
                    <option value="Boilerplate">Boilerplate</option>
                    <option value="Protection">Protection</option>
                    <option value="Warranties">Warranties</option>
                    <option value="Definitions">Definitions</option>
                    <option value="Payment Terms">Payment Terms</option>
                    <option value="Termination">Termination</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            
            <div id="clauseStats" style="padding:10px; background:rgba(75, 158, 255, 0.1); border-radius:6px; margin-bottom:16px; color:#9BA1B0; font-size:13px;"></div>
            
            <div id="clauseList" style="max-height: 400px; overflow-y: auto;"></div>
            
            <button id="cancelClauseBtn" style="margin-top:16px; padding:10px 20px; background:#252930; color:#FFFFFF; border:none; border-radius:6px; cursor:pointer; width:100%;">Cancel</button>
        </div>
    </div>
  `,
    []
  );

  const findReplaceHtml = useMemo(
    () => `
    <div id="findReplaceBar" style="display:none; position:fixed; top:80px; right:20px; background:#1A1D24; border:1px solid #252930; border-radius:8px; padding:16px; z-index:999; min-width:320px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <h4 style="color:#FFFFFF; margin:0;">Find & Replace</h4>
            <button id="closeFindReplaceBtn" style="background:transparent; border:none; color:#9BA1B0; cursor:pointer; font-size:18px;">×</button>
        </div>
        <input type="text" id="findInput" placeholder="Find..." style="width:100%; padding:8px; margin-bottom:8px; background:#13151A; border:1px solid #252930; border-radius:6px; color:#FFFFFF;">
        <input type="text" id="replaceInput" placeholder="Replace with..." style="width:100%; padding:8px; margin-bottom:12px; background:#13151A; border:1px solid #252930; border-radius:6px; color:#FFFFFF;">
        <div style="display:flex; gap:8px;">
            <button id="findNextBtn" style="flex:1; padding:8px; background:#4B9EFF; color:#FFFFFF; border:none; border-radius:6px; cursor:pointer; font-size:13px;">Find Next</button>
            <button id="replaceOneBtn" style="flex:1; padding:8px; background:#252930; color:#FFFFFF; border:none; border-radius:6px; cursor:pointer; font-size:13px;">Replace</button>
            <button id="replaceAllBtn" style="flex:1; padding:8px; background:#252930; color:#FFFFFF; border:none; border-radius:6px; cursor:pointer; font-size:13px;">Replace All</button>
        </div>
        <div id="findResults" style="margin-top:8px; font-size:12px; color:#9BA1B0;"></div>
    </div>
  `,
    []
  );

  const outlineHtml = useMemo(
    () => `
    <div id="outlineSidebar" style="position:fixed; right:0; top:140px; width:280px; max-height:calc(100vh - 200px); background:#1A1D24; border:1px solid #252930; border-radius:8px 0 0 8px; padding:16px; overflow-y:auto; z-index:998; display: none;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <h4 style="color:#FFFFFF; margin:0; font-size:14px;">Document Outline</h4>
            <button id="toggleOutlineBtn" style="background:transparent; border:none; color:#9BA1B0; cursor:pointer;">◀</button>
        </div>
        <div id="outlineContent"></div>
    </div>
  `,
    []
  );

  const commentsHtml = useMemo(
    () => `
    <div id="commentsPanel" style="position:fixed; right:0; top:140px; width:360px; max-height:calc(100vh - 200px); background:#1A1D24; border:1px solid #252930; border-radius:8px 0 0 8px; padding:16px; overflow-y:auto; z-index:997; display:none;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid #252930;">
            <h4 style="color:#FFFFFF; margin:0; font-size:14px;">💬 Comments</h4>
            <button id="toggleCommentsBtn" style="background:transparent; border:none; color:#9BA1B0; cursor:pointer; font-size:18px;">×</button>
        </div>
        <div id="commentsList"></div>
    </div>
  `,
    []
  );

  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;

    let allClauses = [...clauses];
    let filteredClauses = [...clauses];
    let savedRange: Range | null = null;
    let currentMatchIndex = -1;
    let matchElements: HTMLElement[] = [];
    
    // CRITICAL: Load comments from window object (passed from Python/Streamlit)
    let comments: Comment[] = [];

    const loadCommentsFromWindow = () => {
      console.log("🔄 Loading comments from window object...");
      
      if ((window as any).streamlitComments) {
        comments = (window as any).streamlitComments;
        console.log(`📥 Loaded ${comments.length} comments from Streamlit`);
        console.log("Comments data:", comments);
        
        // Wait for editor to be fully loaded before applying highlights
        setTimeout(() => {
          applyCommentHighlights();
          renderComments();
        }, 100);
      } else {
        console.warn("⚠️ No comments found in window.streamlitComments");
      }
    };

    const applyCommentHighlights = () => {
      if (!editorRef.current) return;
      
      console.log(`🎨 Applying highlights for ${comments.length} comments`);
      
      comments.forEach(comment => {
        const commentSpan = editorRef.current!.querySelector(`[data-comment-id="${comment.id}"]`) as HTMLElement;
        
        if (commentSpan) {
          console.log(`✅ Found span for comment ${comment.id}`);
          
          if (!comment.resolved) {
            commentSpan.style.cssText = 'background-color: rgba(250, 204, 21, 0.2); border-bottom: 2px dotted #F59E0B; cursor: help; position: relative;';
            
            commentSpan.onclick = (e) => {
              e.stopPropagation();
              console.log(`👆 Clicked on comment ${comment.id}`);
              showCommentPopup(comment.id);
            };
            
            commentSpan.onmouseenter = () => {
              commentSpan.style.backgroundColor = 'rgba(250, 204, 21, 0.35)';
            };
            
            commentSpan.onmouseleave = () => {
              commentSpan.style.backgroundColor = 'rgba(250, 204, 21, 0.2)';
            };
          } else {
            commentSpan.style.cssText = 'border-bottom: 2px dotted #6B7280; background-color: rgba(107, 114, 128, 0.1); cursor: help;';
            
            commentSpan.onclick = (e) => {
              e.stopPropagation();
              showCommentPopup(comment.id);
            };
          }
        } else {
          console.warn(`⚠️ No span found for comment ${comment.id} - comment may have been added in a different session`);
        }
      });
    };

    // Load comments on mount and when they change
    loadCommentsFromWindow();

    // Reload comments when window updates
    (window as any).reloadComments = () => {
      console.log("🔄 Reloading comments triggered from Python");
      loadCommentsFromWindow();
    };

    // Get user info and version ID from window
    const getUserInfo = () => {
      return {
        email: (window as any).streamlitUserEmail || 'Unknown User',
        name: (window as any).streamlitUserName || 'Unknown User'
      };
    };
    
    const getVersionId = () => {
      // Prefer the versionId passed into the hook if provided, otherwise fall back to the window value
      if (versionId && versionId.trim() !== "") {
        return versionId;
      }
      return (window as any).streamlitVersionId || null;
    };

    // Send comment action to Streamlit/Python
    const sendCommentAction = (action: any) => {
      console.log("📤 Sending comment action to Streamlit:", action);
      
      // Method 1: Use Streamlit's setComponentValue (PRIMARY)
      if ((window as any).Streamlit && (window as any).Streamlit.setComponentValue) {
        console.log("✅ Using Streamlit.setComponentValue");
        (window as any).Streamlit.setComponentValue({
          type: 'comment_action',
          action: action
        });
      }
      
      // Method 2: Use global handler function (FALLBACK)
      if ((window as any).handleCommentAction) {
        console.log("✅ Using window.handleCommentAction");
        (window as any).handleCommentAction(action);
      }
      
      // Method 3: Post message to parent (BACKUP)
      if (window.parent) {
        console.log("✅ Using window.parent.postMessage");
        window.parent.postMessage({
          type: 'streamlit:setComponentValue',
          value: {
            type: 'comment_action',
            action: action
          }
        }, '*');
      }
    };

    const execCmd = (command: string, value: string | null = null) => {
      (document as any).execCommand(command, false, value);
      editor.focus();
    };

    const handleToolbarClick = (e: Event) => {
      const target = (e.target as HTMLElement).closest(
        "button[data-command], select[data-command]"
      ) as HTMLElement | null;
      if (!target) return;

      if ((target as HTMLButtonElement | HTMLSelectElement).disabled) {
        return;
      }

      const command = target.getAttribute("data-command");
      if (!command) return;

      // Handle special commands
      if (command === "addComment") {
        addCommentToSelection();
        return;
      }

      if (target.tagName === "SELECT") {
        const value = (target as HTMLSelectElement).value;
        if (value) {
          execCmd(command, value);
          (target as HTMLSelectElement).value = "";
        }
      } else {
        execCmd(command);
      }
    };

    const toolbar = document.querySelector(".toolbar") as HTMLElement | null;
    toolbar?.addEventListener("click", handleToolbarClick);

    const updateStats = () => {
      const wordCountEl = document.getElementById("wordCount");
      const charCountEl = document.getElementById("charCount");

      let text = "";
      const clonedEditor = editor.cloneNode(true) as HTMLElement;
      text = clonedEditor.textContent || "";
      
      const words = text.trim().split(/\s+/).filter((w) => w.length > 0);
      
      if (wordCountEl) wordCountEl.textContent = `Words: ${words.length}`;
      if (charCountEl) charCountEl.textContent = `Characters: ${text.length}`;
    };

    editor.addEventListener("input", updateStats);
    updateStats();

    const saveSelection = () => {
      const selection = window.getSelection();
      if (selection && selection.rangeCount > 0) {
        savedRange = selection.getRangeAt(0).cloneRange();
        
        // CRITICAL: Also save a marker element for absolute position tracking
        const marker = document.createElement('span');
        marker.id = 'cursor-position-marker';
        marker.style.display = 'none';
        
        try {
          const range = savedRange.cloneRange();
          range.insertNode(marker);
          range.setStartAfter(marker);
          range.setEndAfter(marker);
          savedRange = range;
          console.log("💾 Saved cursor position with marker element");
        } catch (e) {
          console.warn("⚠️ Could not insert marker, using range only", e);
        }
      } else {
        // No selection - create range at end
        const range = document.createRange();
        range.selectNodeContents(editor);
        range.collapse(false);
        savedRange = range;
        console.log("💾 No selection - saved end position");
      }
      
      // CRITICAL: Save scroll position
      if (editor) {
        (window as any).savedEditorScrollTop = editor.scrollTop;
        console.log(`💾 Saved scroll position: ${editor.scrollTop}px`);
      }
    };


    const restoreSelection = () => {
      // Find and use the marker if it exists
      const marker = editor.querySelector('#cursor-position-marker') as HTMLElement;
      
      if (marker) {
        console.log("✅ Found cursor position marker");
        const range = document.createRange();
        range.setStartAfter(marker);
        range.setEndAfter(marker);
        
        const selection = window.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(range);
        
        // Remove marker after using it
        marker.remove();
        
        savedRange = range;
        return true;
      } else if (savedRange) {
        console.log("✅ Using saved range");
        const selection = window.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(savedRange);
        return true;
      }
      
      console.warn("⚠️ No saved cursor position found");
      return false;
    };

    // ========================================================================
    // COMMENTS FUNCTIONALITY
    // ========================================================================

    const addCommentToSelection = () => {
      const sel = window.getSelection();
      if (!sel || sel.rangeCount === 0 || sel.isCollapsed) {
        alert('Please select text to comment on');
        return;
      }

      const commentText = prompt('Enter your comment:');
      if (!commentText || !commentText.trim()) {
        return;
      }

      const range = sel.getRangeAt(0);
      const commentId = 'comment-' + Date.now();
      
      const span = document.createElement('span');
      span.className = 'has-comment';
      span.setAttribute('data-comment-id', commentId);
      span.style.cssText = 'background-color: rgba(250, 204, 21, 0.2); border-bottom: 2px dotted #F59E0B; cursor: help; position: relative;';
      
      try {
        range.surroundContents(span);
      } catch(e) {
        alert('Cannot add comment to selection spanning multiple elements. Please select text within a single paragraph.');
        return;
      }
      
      const userInfo = getUserInfo();
      const versionId = getVersionId();
      
      const comment: Comment = {
        id: commentId,
        text: commentText.trim(),
        selectedText: sel.toString(),
        timestamp: new Date().toISOString(),
        author: userInfo.name,
        authorEmail: userInfo.email,
        resolved: false
      };
      
      comments.push(comment);
      
      span.onclick = (e) => {
        e.stopPropagation();
        showCommentPopup(commentId);
      };
      
      span.onmouseenter = () => {
        span.style.backgroundColor = 'rgba(250, 204, 21, 0.35)';
      };
      span.onmouseleave = () => {
        span.style.backgroundColor = 'rgba(250, 204, 21, 0.2)';
      };
      
      // Send to backend to save to database
      sendCommentAction({
        type: 'create',
        comment: {
          id: commentId,
          text: comment.text,
          selectedText: comment.selectedText,
          timestamp: comment.timestamp,
          author: comment.author,
          authorEmail: comment.authorEmail,
          resolved: false
        }
      });
      
      console.log("✅ Comment created and sent to backend");
      
      renderComments();
      toggleCommentsPanel(true);
      
      // Trigger update to Streamlit to save HTML with comment markup
      if ((window as any).updateEditorContentImmediate) {
        console.log("📝 Updating editor content with new comment markup");
        (window as any).updateEditorContentImmediate(editor.innerHTML);
      }
      
      updateStats();
    };

    const showCommentPopup = (commentId: string) => {
      console.log(`🎯 Showing comment popup for ${commentId}`);
      
      const comment = comments.find(c => c.id === commentId);
      if (!comment) {
        console.error(`❌ Comment ${commentId} not found in comments array`);
        console.log("Available comments:", comments.map(c => c.id));
        return;
      }
      
      // Open the comments panel
      toggleCommentsPanel(true);
      
      // Scroll to the specific comment after a brief delay
      setTimeout(() => {
        const commentCard = document.getElementById(commentId);
        if (commentCard) {
          commentCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          // Add a pulse animation
          commentCard.style.animation = 'none';
          setTimeout(() => {
            commentCard.style.animation = 'pulse 0.5s';
          }, 10);
          console.log(`✅ Scrolled to comment ${commentId}`);
        } else {
          console.error(`❌ Comment card element ${commentId} not found in DOM`);
        }
      }, 150);
    };

    const renderComments = () => {
      const list = document.getElementById('commentsList');
      if (!list) return;
      
      list.innerHTML = '';
      
      if (comments.length === 0) {
        list.innerHTML = '<p style="color:#6B7280; font-size:13px; text-align:center; padding:20px;">No comments yet. Select text and click the 💬 button to add a comment.</p>';
        return;
      }
      
      // Sort: unresolved first, then by timestamp
      const sorted = [...comments].sort((a, b) => {
        if (a.resolved !== b.resolved) {
          return a.resolved ? 1 : -1;
        }
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      });
      
      sorted.forEach(comment => {
        const div = document.createElement('div');
        div.id = comment.id;
        div.style.cssText = `
          padding: 14px;
          margin: 0 0 12px 0;
          background: ${comment.resolved ? 'rgba(255, 255, 255, 0.02)' : '#13151A'};
          border-radius: 8px;
          border-left: 3px solid ${comment.resolved ? '#6B7280' : '#F59E0B'};
          opacity: ${comment.resolved ? '0.6' : '1'};
          transition: all 0.2s;
        `;
        
        const timeAgo = getTimeAgo(new Date(comment.timestamp));
        const initials = comment.author.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        
        div.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <div style="width: 28px; height: 28px; border-radius: 50%; background: linear-gradient(135deg, #4B9EFF, #7DB8FF); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: white;">
                ${initials}
              </div>
              <div>
                <div style="color: #FFFFFF; font-size: 13px; font-weight: 600;">${comment.author}</div>
                <div style="color: #6B7280; font-size: 11px;">${timeAgo}</div>
              </div>
            </div>
            <div style="display: flex; gap: 4px;">
              ${!comment.resolved ? `
                <button data-action="resolve" data-comment-id="${comment.id}" 
                        style="background: rgba(74, 222, 128, 0.12); border: none; color: #4ADE80; cursor: pointer; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;"
                        title="Resolve comment">
                  ✓ Resolve
                </button>
              ` : `
                <span style="background: rgba(107, 114, 128, 0.12); color: #9BA1B0; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">
                  ✓ Resolved
                </span>
              `}
              <button data-action="delete" data-comment-id="${comment.id}" 
                      style="background: transparent; border: none; color: #9BA1B0; cursor: pointer; font-size: 16px; padding: 0 4px;"
                      title="Delete comment">
                ×
              </button>
            </div>
          </div>
          
          <div style="color: #9BA1B0; font-size: 12px; margin-bottom: 10px; padding: 8px; background: rgba(255, 255, 255, 0.03); border-radius: 4px; font-style: italic;">
            "${comment.selectedText.length > 60 ? comment.selectedText.substring(0, 60) + '...' : comment.selectedText}"
          </div>
          
          <div style="color: #FFFFFF; font-size: 13px; line-height: 1.5;">
            ${comment.text}
          </div>
        `;
        
        div.onmouseenter = () => {
          if (!comment.resolved) {
            div.style.background = '#1F2937';
          }
          // Highlight the commented text
          const commentSpan = editor.querySelector(`[data-comment-id="${comment.id}"]`) as HTMLElement;
          if (commentSpan) {
            commentSpan.style.backgroundColor = 'rgba(250, 204, 21, 0.4)';
          }
        };
        
        div.onmouseleave = () => {
          if (!comment.resolved) {
            div.style.background = '#13151A';
          }
          const commentSpan = editor.querySelector(`[data-comment-id="${comment.id}"]`) as HTMLElement;
          if (commentSpan && !comment.resolved) {
            commentSpan.style.backgroundColor = 'rgba(250, 204, 21, 0.2)';
          }
        };
        
        list.appendChild(div);
      });
      
      // Add click handlers for buttons
      list.querySelectorAll('button[data-action]').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const action = (btn as HTMLElement).getAttribute('data-action');
          const commentId = (btn as HTMLElement).getAttribute('data-comment-id');
          
          if (action === 'resolve' && commentId) {
            resolveComment(commentId);
          } else if (action === 'delete' && commentId) {
            deleteComment(commentId);
          }
        });
      });
    };

    const resolveComment = (commentId: string) => {
      const comment = comments.find(c => c.id === commentId);
      if (!comment) {
        console.error("❌ Comment not found:", commentId);
        return;
      }
      
      console.log("🔧 Resolving comment:", commentId);
      comment.resolved = true;
      
      const commentSpan = editor.querySelector(`[data-comment-id="${commentId}"]`) as HTMLElement;
      if (commentSpan) {
        commentSpan.style.borderBottom = '2px dotted #6B7280';
        commentSpan.style.backgroundColor = 'rgba(107, 114, 128, 0.1)';
      }
      
      // Send to backend
      sendCommentAction({
        type: 'resolve',
        commentId: commentId
      });
      
      console.log("✅ Comment resolved successfully");
      
      renderComments();
      
      // Trigger update to Streamlit
      if ((window as any).updateEditorContentImmediate) {
        (window as any).updateEditorContentImmediate(editor.innerHTML);
      }
    };

    const deleteComment = (commentId: string) => {
      if (!window.confirm('Are you sure you want to delete this comment?')) {
        return;
      }
      
      console.log("🗑️ Deleting comment:", commentId);
      
      comments = comments.filter(c => c.id !== commentId);
      
      const spans = editor.querySelectorAll(`[data-comment-id="${commentId}"]`);
      spans.forEach(span => {
        const parent = span.parentNode;
        if (parent) {
          while (span.firstChild) {
            parent.insertBefore(span.firstChild, span);
          }
          parent.removeChild(span);
          parent.normalize();
        }
      });
      
      // Send to backend
      sendCommentAction({
        type: 'delete',
        commentId: commentId
      });
      
      console.log("✅ Comment deleted successfully");
      
      renderComments();
      
      // Trigger update to Streamlit
      if ((window as any).updateEditorContentImmediate) {
        (window as any).updateEditorContentImmediate(editor.innerHTML);
      }
      
      updateStats();
    };

    const toggleCommentsPanel = (show?: boolean) => {
      const panel = document.getElementById('commentsPanel');
      if (!panel) return;
      
      if (show !== undefined) {
        panel.style.display = show ? 'block' : 'none';
      } else {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      }
      
      if (panel.style.display === 'block') {
        renderComments();
      }
    };

    const getTimeAgo = (date: Date): string => {
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const seconds = Math.floor(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);
      
      if (days > 0) return `${days}d ago`;
      if (hours > 0) return `${hours}h ago`;
      if (minutes > 0) return `${minutes}m ago`;
      return 'Just now';
    };

    // ========================================================================
    // END COMMENTS FUNCTIONALITY
    // ========================================================================

    // ========================================================================
    // FIND & REPLACE FUNCTIONALITY
    // ========================================================================

    const clearHighlights = () => {
      const highlights = editor.querySelectorAll('.search-highlight');
      highlights.forEach((highlight) => {
        const parent = highlight.parentNode;
        if (parent) {
          while (highlight.firstChild) {
            parent.insertBefore(highlight.firstChild, highlight);
          }
          parent.removeChild(highlight);
          parent.normalize();
        }
      });
      matchElements = [];
      currentMatchIndex = -1;
    };

    const escapeRegExp = (str: string): string => {
      return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    };

    const highlightMatches = (searchTerm: string): number => {
      if (!searchTerm) return 0;

      clearHighlights();
      
      const escapedTerm = escapeRegExp(searchTerm);
      const regex = new RegExp(`(${escapedTerm})`, 'gi');
      let matchCount = 0;

      const highlightTextNode = (node: Node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          const text = node.textContent || '';
          if (regex.test(text)) {
            const parent = node.parentNode;
            if (parent && parent !== editor) {
              const span = document.createElement('span');
              span.innerHTML = text.replace(regex, (match) => {
                matchCount++;
                return `<span class="search-highlight" style="background-color: #F59E0B; color: #000000; padding: 2px 4px; border-radius: 2px;">${match}</span>`;
              });
              
              parent.insertBefore(span, node);
              parent.removeChild(node);
              
              while (span.firstChild) {
                parent.insertBefore(span.firstChild, span);
              }
              parent.removeChild(span);
            }
          }
        } else if (node.nodeType === Node.ELEMENT_NODE && node.nodeName !== 'SCRIPT' && node.nodeName !== 'STYLE') {
          const childNodes = Array.from(node.childNodes);
          childNodes.forEach(child => highlightTextNode(child));
        }
      };

      highlightTextNode(editor);
      matchElements = Array.from(editor.querySelectorAll('.search-highlight'));
      
      return matchCount;
    };

    const findNext = () => {
      const findInput = document.getElementById('findInput') as HTMLInputElement;
      const resultsDiv = document.getElementById('findResults');
      
      if (!findInput || !resultsDiv) return;
      
      const searchTerm = findInput.value.trim();
      
      if (!searchTerm) {
        resultsDiv.textContent = 'Please enter search text';
        return;
      }

      if (matchElements.length === 0) {
        const count = highlightMatches(searchTerm);
        if (count === 0) {
          resultsDiv.textContent = 'No matches found';
          return;
        }
        resultsDiv.textContent = `Found ${count} match${count !== 1 ? 'es' : ''}`;
        currentMatchIndex = 0;
      } else {
        currentMatchIndex = (currentMatchIndex + 1) % matchElements.length;
      }

      editor.querySelectorAll('.search-highlight-active').forEach(el => {
        el.classList.remove('search-highlight-active');
        (el as HTMLElement).style.backgroundColor = '#F59E0B';
      });

      if (matchElements[currentMatchIndex]) {
        const currentMatch = matchElements[currentMatchIndex];
        currentMatch.classList.add('search-highlight-active');
        currentMatch.style.backgroundColor = '#EF4444';
        currentMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        resultsDiv.textContent = `Match ${currentMatchIndex + 1} of ${matchElements.length}`;
      }
    };

    const replaceOne = () => {
      const findInput = document.getElementById('findInput') as HTMLInputElement;
      const replaceInput = document.getElementById('replaceInput') as HTMLInputElement;
      const resultsDiv = document.getElementById('findResults');
      
      if (!findInput || !replaceInput || !resultsDiv) return;
      
      const searchTerm = findInput.value.trim();
      const replaceTerm = replaceInput.value;
      
      if (!searchTerm) {
        resultsDiv.textContent = 'Please enter search text';
        return;
      }

      if (matchElements.length === 0) {
        highlightMatches(searchTerm);
      }

      if (matchElements.length === 0) {
        resultsDiv.textContent = 'No matches to replace';
        return;
      }

      const currentMatch = matchElements[currentMatchIndex];
      if (currentMatch) {
        const textNode = document.createTextNode(replaceTerm);
        currentMatch.parentNode?.replaceChild(textNode, currentMatch);
        
        if ((window as any).updateEditorContentImmediate) {
          (window as any).updateEditorContentImmediate(editor.innerHTML);
        }
        
        const newCount = highlightMatches(searchTerm);
        if (newCount === 0) {
          resultsDiv.textContent = 'No more matches';
          clearHighlights();
        } else {
          resultsDiv.textContent = `Replaced 1. ${newCount} match${newCount !== 1 ? 'es' : ''} remaining`;
          currentMatchIndex = Math.min(currentMatchIndex, matchElements.length - 1);
        }
        
        updateStats();
      }
    };

    const replaceAll = () => {
      const findInput = document.getElementById('findInput') as HTMLInputElement;
      const replaceInput = document.getElementById('replaceInput') as HTMLInputElement;
      const resultsDiv = document.getElementById('findResults');
      
      if (!findInput || !replaceInput || !resultsDiv) return;
      
      const searchTerm = findInput.value.trim();
      const replaceTerm = replaceInput.value;
      
      if (!searchTerm) {
        resultsDiv.textContent = 'Please enter search text';
        return;
      }

      const tempCount = highlightMatches(searchTerm);
      
      if (tempCount === 0) {
        resultsDiv.textContent = 'No matches to replace';
        clearHighlights();
        return;
      }

      const escapedTerm = escapeRegExp(searchTerm);
      const regex = new RegExp(escapedTerm, 'gi');
      
      const replaceInText = (node: Node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          const text = node.textContent || '';
          if (regex.test(text)) {
            node.textContent = text.replace(regex, replaceTerm);
          }
        } else if (node.nodeType === Node.ELEMENT_NODE && node.nodeName !== 'SCRIPT' && node.nodeName !== 'STYLE') {
          Array.from(node.childNodes).forEach(child => replaceInText(child));
        }
      };

      clearHighlights();
      replaceInText(editor);
      
      if ((window as any).updateEditorContentImmediate) {
        (window as any).updateEditorContentImmediate(editor.innerHTML);
      }
      
      resultsDiv.textContent = `Replaced ${tempCount} occurrence${tempCount !== 1 ? 's' : ''}`;
      updateStats();
    };

    // ========================================================================
    // CLAUSE LIBRARY FUNCTIONALITY
    // ========================================================================

    const renderClauseList = () => {
      const list = document.getElementById("clauseList") as HTMLDivElement;
      const statsDiv = document.getElementById("clauseStats") as HTMLDivElement;
      if (!list) return;

      list.innerHTML = "";

      const pinnedCount = filteredClauses.filter((c) => c.is_pinned).length;
      if (statsDiv) {
        statsDiv.innerHTML = `📚 <strong>${filteredClauses.length}</strong> clauses available • 📌 <strong>${pinnedCount}</strong> pinned`;
      }

      if (filteredClauses.length === 0) {
        list.innerHTML =
          '<div style="padding:20px; text-align:center; color:#9BA1B0;">No clauses found. Try adjusting your filters or add clauses in the Clause Library page.</div>';
        return;
      }

      const sorted = [...filteredClauses].sort((a, b) => {
        if (a.is_pinned && !b.is_pinned) return -1;
        if (!a.is_pinned && b.is_pinned) return 1;
        return (b.usage_count || 0) - (a.usage_count || 0);
      });

      sorted.forEach((clause) => {
        const div = document.createElement("div");
        div.style.cssText =
          "padding:14px; margin:8px 0; background:#13151A; border:1px solid #252930; border-radius:8px; cursor:pointer; transition: all 0.2s;";

        const badgeColors: { [key: string]: string } = {
          Boilerplate: "#4B9EFF",
          Protection: "#10B981",
          Warranties: "#F59E0B",
          Definitions: "#8B5CF6",
          "Payment Terms": "#EC4899",
          Termination: "#EF4444",
          Other: "#6B7280",
        };

        const badgeColor = badgeColors[clause.category] || "#6B7280";
        const pinBadge = clause.is_pinned
          ? '<span style="margin-left:8px;">📌</span>'
          : "";
        const systemBadge = clause.is_system
          ? '<span style="margin-left:8px; color:#4B9EFF; font-size:11px;">🔒</span>'
          : "";

        const tagsHtml = clause.tags
          .map(
            (tag: string) =>
              `<span style="background:#252930; padding:2px 8px; border-radius:4px; font-size:11px; color:#9BA1B0;">${tag}</span>`
          )
          .join(" ");

        const preview = clause.content.replace(/<[^>]*>/g, "").substring(0, 150);

        div.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:8px;">
            <strong style="color:#FFFFFF; font-size:14px;">${clause.title}${pinBadge}${systemBadge}</strong>
            <span style="background:${badgeColor}; color:#FFFFFF; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:600;">${clause.category}</span>
          </div>
          <div style="color:#9BA1B0; font-size:12px; margin-bottom:8px; line-height:1.5;">${preview}...</div>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; gap:4px; flex-wrap:wrap;">${tagsHtml}</div>
            <span style="color:#6B7280; font-size:11px;">📊 Used ${clause.usage_count} times</span>
          </div>
        `;

        div.onmouseenter = () => {
          div.style.background = "#1F2937";
          div.style.borderColor = "#4B9EFF";
        };

        div.onmouseleave = () => {
          div.style.background = "#13151A";
          div.style.borderColor = "#252930";
        };

        div.onclick = () => {
          insertClauseAtCursor(clause.content);
          closeClauseModal();
        };

        list.appendChild(div);
      });
    };

    const filterClauses = () => {
      const searchInput =
        (document.getElementById("clauseSearchInput") as HTMLInputElement)
          ?.value.toLowerCase() || "";
      const categoryFilter =
        (document.getElementById("clauseCategoryFilter") as HTMLSelectElement)
          ?.value || "";

      filteredClauses = allClauses.filter((clause) => {
        const matchesSearch =
          !searchInput ||
          clause.title.toLowerCase().includes(searchInput) ||
          clause.content.toLowerCase().includes(searchInput) ||
          clause.tags.some((tag: string) =>
            tag.toLowerCase().includes(searchInput)
          );

        const matchesCategory = !categoryFilter || clause.category === categoryFilter;

        return matchesSearch && matchesCategory;
      });

      renderClauseList();
    };

    const insertClauseAtCursor = (clauseContent: string) => {
      console.log("🚀 Starting clause insertion...");
      
      // CRITICAL: Store current scroll position FIRST
      const currentScrollTop = editor.scrollTop;
      console.log(`📍 Current scroll position: ${currentScrollTop}px`);
      
      // Restore the saved selection/cursor position
      const hasValidPosition = restoreSelection();
      
      if (!hasValidPosition) {
        console.error("❌ No valid cursor position - aborting insertion");
        alert("Please click in the document to place your cursor, then try inserting the clause again.");
        closeClauseModal();
        return;
      }
      
      editor.focus();
      
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0) {
        console.error("❌ No selection available after restore");
        return;
      }
      
      const range = selection.getRangeAt(0);
      
      // CRITICAL: Create a wrapper for the inserted content to track its position
      const insertionWrapper = document.createElement('div');
      insertionWrapper.id = 'temp-insertion-wrapper-' + Date.now();
      insertionWrapper.style.display = 'contents'; // Doesn't affect layout
      
      // Parse clause HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = clauseContent.trim();
      
      try {
        // Insert spacing before
        const spaceBefore = document.createElement('p');
        spaceBefore.innerHTML = '<br>';
        range.insertNode(spaceBefore);
        
        // Move range after space
        range.setStartAfter(spaceBefore);
        range.collapse(true);
        
        // Move clause content into wrapper
        while (tempDiv.firstChild) {
          insertionWrapper.appendChild(tempDiv.firstChild);
        }
        
        // Insert the wrapper
        range.insertNode(insertionWrapper);
        range.setStartAfter(insertionWrapper);
        range.collapse(true);
        
        // Insert spacing after
        const spaceAfter = document.createElement('p');
        spaceAfter.innerHTML = '<br>';
        range.insertNode(spaceAfter);
        
        // Position cursor after inserted content
        range.setStartAfter(spaceAfter);
        range.setEndAfter(spaceAfter);
        selection.removeAllRanges();
        selection.addRange(range);
        
        console.log("✅ Clause content inserted into DOM");
        
        // CRITICAL: Get the new content BEFORE any scroll manipulation
        const newContent = editor.innerHTML;
        
        // CRITICAL: Restore scroll position IMMEDIATELY using multiple methods
        const restoreScroll = () => {
          editor.scrollTop = currentScrollTop;
        };
        
        // Method 1: Immediate
        restoreScroll();
        
        // Method 2: After current call stack
        setTimeout(restoreScroll, 0);
        
        // Method 3: After next paint
        requestAnimationFrame(() => {
          restoreScroll();
          console.log(`📍 Restored scroll to ${currentScrollTop}px`);
          
          // Method 4: Double-check after another frame
          requestAnimationFrame(() => {
            restoreScroll();
            
            // Now gently scroll the cursor into view if needed
            setTimeout(() => {
              spaceAfter.scrollIntoView({ 
                behavior: "smooth", 
                block: "nearest",
                inline: "nearest"
              });
            }, 50);
          });
        });
        
        // Unwrap the insertion wrapper (make content native to editor)
        setTimeout(() => {
          const wrapper = document.getElementById(insertionWrapper.id);
          if (wrapper && wrapper.parentNode) {
            while (wrapper.firstChild) {
              wrapper.parentNode.insertBefore(wrapper.firstChild, wrapper);
            }
            wrapper.remove();
            console.log("✅ Unwrapped insertion content");
          }
        }, 100);
        
        // Send update to Streamlit
        if ((window as any).updateEditorContentImmediate) {
          console.log("📡 Sending update to Streamlit...");
          (window as any).updateEditorContentImmediate(newContent);
        } else {
          console.error("❌ updateEditorContentImmediate not available!");
        }
        
        updateStats();
        console.log("✅ Clause insertion complete");
        
      } catch (error) {
        console.error("❌ Error during clause insertion:", error);
        alert("Failed to insert clause. Please try again.");
      }
    };

    const openClauseModal = () => {
      console.log("🔓 Opening clause modal...");
      
      // CRITICAL: Save selection and scroll position BEFORE opening modal
      saveSelection();

      const modal = document.getElementById("clauseModal") as HTMLDivElement;
      if (!modal) return;

      const searchInput = document.getElementById(
        "clauseSearchInput"
      ) as HTMLInputElement;
      const categoryFilter = document.getElementById(
        "clauseCategoryFilter"
      ) as HTMLSelectElement;
      if (searchInput) searchInput.value = "";
      if (categoryFilter) categoryFilter.value = "";

      allClauses = [...clauses];
      filteredClauses = [...clauses];
      renderClauseList();
      modal.style.display = "block";

      setTimeout(() => searchInput?.focus(), 100);
    };

    const closeClauseModal = () => {
      const modal = document.getElementById("clauseModal") as HTMLDivElement;
      if (modal) modal.style.display = "none";
      
      // CRITICAL: Restore scroll position when closing without insertion
      const savedScroll = (window as any).savedEditorScrollTop;
      if (savedScroll !== undefined && editor) {
        requestAnimationFrame(() => {
          editor.scrollTop = savedScroll;
          console.log(`📍 Restored scroll position: ${savedScroll}px`);
        });
      }
      
      // Clean up any leftover markers
      const marker = editor.querySelector('#cursor-position-marker');
      if (marker) {
        marker.remove();
      }
      
      editor.focus();
};
    const openFindReplace = () => {
      const bar = document.getElementById("findReplaceBar") as HTMLDivElement;
      if (bar) {
        bar.style.display = "block";
        const findInput = document.getElementById("findInput") as HTMLInputElement;
        setTimeout(() => findInput?.focus(), 100);
      }
    };

    const closeFindReplace = () => {
      clearHighlights();
      const bar = document.getElementById("findReplaceBar") as HTMLDivElement;
      if (bar) bar.style.display = "none";
      editor.focus();
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key.toLowerCase()) {
          case "f":
            e.preventDefault();
            openFindReplace();
            break;
          case "k":
            e.preventDefault();
            openClauseModal();
            break;
        }
      }
      if (e.key === "Escape") {
        closeFindReplace();
        closeClauseModal();
        const commentsPanel = document.getElementById('commentsPanel');
        if (commentsPanel && commentsPanel.style.display !== 'none') {
          toggleCommentsPanel(false);
        }
      }
    };

    // Event Listeners
    document
      .getElementById("btn-insert-clause")
      ?.addEventListener("click", openClauseModal);
    document
      .getElementById("closeClauseModalBtn")
      ?.addEventListener("click", closeClauseModal);
    document
      .getElementById("cancelClauseBtn")
      ?.addEventListener("click", closeClauseModal);

    const searchInput = document.getElementById("clauseSearchInput");
    const categoryFilter = document.getElementById("clauseCategoryFilter");

    searchInput?.addEventListener("input", filterClauses);
    categoryFilter?.addEventListener("change", filterClauses);

    document.getElementById("clauseModal")?.addEventListener("click", (e) => {
      if ((e.target as HTMLElement).id === "clauseModal") {
        closeClauseModal();
      }
    });

    document
      .getElementById("btn-find-replace")
      ?.addEventListener("click", openFindReplace);
    document
      .getElementById("closeFindReplaceBtn")
      ?.addEventListener("click", closeFindReplace);
    
    document
      .getElementById("findNextBtn")
      ?.addEventListener("click", findNext);
    document
      .getElementById("replaceOneBtn")
      ?.addEventListener("click", replaceOne);
    document
      .getElementById("replaceAllBtn")
      ?.addEventListener("click", replaceAll);

    const findInputElement = document.getElementById("findInput");
    findInputElement?.addEventListener("keypress", (e: Event) => {
      if ((e as KeyboardEvent).key === "Enter") {
        e.preventDefault();
        findNext();
      }
    });

    document
      .getElementById("toggleCommentsBtn")
      ?.addEventListener("click", () => toggleCommentsPanel(false));

    editor.addEventListener("keydown", handleKeyDown);

    return () => {
      toolbar?.removeEventListener("click", handleToolbarClick);
      editor.removeEventListener("input", updateStats);
      editor.removeEventListener("keydown", handleKeyDown);
      document
        .getElementById("btn-insert-clause")
        ?.removeEventListener("click", openClauseModal);
      document
        .getElementById("closeClauseModalBtn")
        ?.removeEventListener("click", closeClauseModal);
      document
        .getElementById("cancelClauseBtn")
        ?.removeEventListener("click", closeClauseModal);
      document
        .getElementById("btn-find-replace")
        ?.removeEventListener("click", openFindReplace);
      document
        .getElementById("closeFindReplaceBtn")
        ?.removeEventListener("click", closeFindReplace);
      document
        .getElementById("findNextBtn")
        ?.removeEventListener("click", findNext);
      document
        .getElementById("replaceOneBtn")
        ?.removeEventListener("click", replaceOne);
      document
        .getElementById("replaceAllBtn")
        ?.removeEventListener("click", replaceAll);
      document
        .getElementById("toggleCommentsBtn")
        ?.removeEventListener("click", () => toggleCommentsPanel(false));
      searchInput?.removeEventListener("input", filterClauses);
      categoryFilter?.removeEventListener("change", filterClauses);
      findInputElement?.removeEventListener("keypress", () => {});
      
      // Clean up comment reload function
      delete (window as any).reloadComments;
    };
  }, [editorRef, clauses]);

  return { clauseModalHtml, findReplaceHtml, outlineHtml, commentsHtml };
};
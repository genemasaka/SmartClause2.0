import React, { useEffect, useRef, useState } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import { useDebouncedCallback } from "use-debounce";
import "./EditorStyles.css";

import { useEditorLogic } from "./useEditorLogic";

const StreamlitDocEditor = (props: any) => {
  const { args = {} } = props;
  const {
    initialContent = "",
    clauses = [] as Array<Record<string, any>>,
    comments = [] as Array<Record<string, any>>,
    debounce = 1000,
    versionId = "",
  } = args;

  const lastStreamlitContent = useRef<string>("");
  const isFirstRender = useRef(true);
  const editorRef = useRef<HTMLDivElement>(null);
  const lastSentContent = useRef<string>(initialContent);
  const isApplyingExternalUpdate = useRef(false);
  const userIsEditing = useRef(false);
  
  const { clauseModalHtml, findReplaceHtml, outlineHtml, commentsHtml } =
    useEditorLogic(editorRef, clauses, versionId);

  // CRITICAL: Separate debounced function for sending to Python
  // This does NOT affect local display
  const sendUpdateToStreamlit = useDebouncedCallback((newContent: string) => {
    console.log(`📤 Background sync to Python (${newContent.length} chars)`);
    lastSentContent.current = newContent;
    Streamlit.setComponentValue(newContent);
  }, debounce);

  // Expose immediate update function for clause insertions and comments
  useEffect(() => {
    (window as any).updateEditorContentImmediate = (newContent: string) => {
      console.log(`⚡ Immediate content update from clause/comment (${newContent.length} chars)`);
      
      if (editorRef.current) {
        editorRef.current.innerHTML = newContent;
      }
      
      lastSentContent.current = newContent;
      lastStreamlitContent.current = newContent;
      
      // Send immediately (no debounce) for clause insertions
      Streamlit.setComponentValue(newContent);
    };
    
    (window as any).streamlitComments = comments;
    (window as any).streamlitVersionId = versionId;
    console.log(`🔥 Loaded ${comments.length} comments into window`);

    (window as any).sendCommentActionToStreamlit = (action: any) => {
      console.log(`💾 Sending comment action to Streamlit:`, action);
      
      Streamlit.setComponentValue({
        type: 'comment_action',
        action: action,
        content: editorRef.current?.innerHTML || "",
        timestamp: Date.now()
      });
    };

    return () => {
      delete (window as any).updateEditorContentImmediate;
      delete (window as any).streamlitComments;
      delete (window as any).streamlitVersionId;
      delete (window as any).sendCommentActionToStreamlit;
    };
  }, [comments, versionId]);

  // Set initial content ONCE
  useEffect(() => {
    if (isFirstRender.current && editorRef.current) {
      console.log(`🎬 Initial render with ${initialContent.length} chars`);
      editorRef.current.innerHTML = initialContent;
      lastStreamlitContent.current = initialContent;
      lastSentContent.current = initialContent;
      isFirstRender.current = false;
    }
  }, []);

  // CRITICAL: Only respond to SIGNIFICANT external changes (version switches)
  // Ignore autosave echo-backs
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || isFirstRender.current || isApplyingExternalUpdate.current) return;

    const currentEditorContent = editor.innerHTML;
    
    // CRITICAL: Ignore if user is actively editing
    if (userIsEditing.current) {
      console.log(`⏭️ User is editing - ignoring Streamlit update`);
      lastStreamlitContent.current = initialContent;
      return;
    }
    
    // CRITICAL: Ignore if this is echo of our own content
    const isSameContent = initialContent === lastSentContent.current;
    if (isSameContent) {
      console.log(`✅ Echo of our own content - ignoring`);
      lastStreamlitContent.current = initialContent;
      return;
    }
    
    // Only apply MAJOR external changes (version switches, etc)
    const sizeDiff = Math.abs(initialContent.length - currentEditorContent.length);
    const isVersionSwitch = sizeDiff > 500; // More than 500 chars difference
    
    if (isVersionSwitch) {
      console.log(`🔥 MAJOR external change detected (${sizeDiff} chars diff) - updating editor`);
      isApplyingExternalUpdate.current = true;
      
      editor.innerHTML = initialContent;
      lastStreamlitContent.current = initialContent;
      lastSentContent.current = initialContent;
      
      setTimeout(() => {
        isApplyingExternalUpdate.current = false;
      }, 500);
      
      if ((window as any).reloadComments) {
        setTimeout(() => {
          (window as any).reloadComments();
        }, 100);
      }
    } else {
      // Minor difference - just track it, don't update editor
      console.log(`⭐ Minor update (${sizeDiff} chars) - tracking only`);
      lastStreamlitContent.current = initialContent;
    }
  }, [initialContent]);

  // Main input handler - CRITICAL: All edits stay local, only sync in background
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor) return;

    const handleInput = () => {
      if (isApplyingExternalUpdate.current) {
        console.log("⏭️ Skipping - external update in progress");
        return;
      }
      
      // Mark that user is editing
      userIsEditing.current = true;
      
      const newContent = editor.innerHTML;
      console.log(`✏️ User edit detected (${newContent.length} chars)`);
      
      // Content is already displayed correctly in the editor
      // Just sync to Python in the background (debounced)
      sendUpdateToStreamlit(newContent);
      
      // Clear editing flag after a delay
      setTimeout(() => {
        userIsEditing.current = false;
      }, 2000);
    };

    const handlePaste = (e: ClipboardEvent) => {
      // Let the paste happen, then process
      setTimeout(() => {
        handleInput();
      }, 100);
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      // Mark as editing on any key press
      userIsEditing.current = true;
    };

    editor.addEventListener("input", handleInput);
    editor.addEventListener("paste", handlePaste as any);
    editor.addEventListener("keydown", handleKeyDown);

    return () => {
      editor.removeEventListener("input", handleInput);
      editor.removeEventListener("paste", handlePaste as any);
      editor.removeEventListener("keydown", handleKeyDown);
    };
  }, [sendUpdateToStreamlit]);

  // Notify Streamlit of height changes
  useEffect(() => {
    Streamlit.setFrameHeight();
  });
  useEffect(() => {
  const editor = editorRef.current;
  if (!editor) return;
  
  // Lock scroll position during updates
  const handleBeforeInput = () => {
    (window as any).lastScrollBeforeEdit = editor.scrollTop;
  };
  
  editor.addEventListener('beforeinput', handleBeforeInput);
  
  return () => {
    editor.removeEventListener('beforeinput', handleBeforeInput);
  };
}, []);
  return (
    <>
      <div dangerouslySetInnerHTML={{ __html: clauseModalHtml }} />
      <div dangerouslySetInnerHTML={{ __html: findReplaceHtml }} />
      <div dangerouslySetInnerHTML={{ __html: outlineHtml }} />
      <div dangerouslySetInnerHTML={{ __html: commentsHtml }} />

      <div className="editor-container" style={{ height: "700px" }}>
        <div className="toolbar">
          <div className="toolbar-group">
            <button
              className="toolbar-btn"
              data-command="undo"
              title="Undo (Ctrl+Z)"
            >
              ↶
            </button>
            <button
              className="toolbar-btn"
              data-command="redo"
              title="Redo (Ctrl+Y)"
            >
              ↷
            </button>
          </div>

          <div className="toolbar-group">
            <select 
              className="toolbar-select" 
              data-command="formatBlock"
              title="Style"
            >
              <option value="">Style</option>
              <option value="p">Normal</option>
              <option value="h1">Heading 1</option>
              <option value="h2">Heading 2</option>
              <option value="h3">Heading 3</option>
              <option value="h4">Heading 4</option>
            </select>
          </div>

          <div className="toolbar-group">
            <button
              className="toolbar-btn"
              data-command="bold"
              title="Bold (Ctrl+B)"
            >
              <b>B</b>
            </button>
            <button
              className="toolbar-btn"
              data-command="italic"
              title="Italic (Ctrl+I)"
            >
              <i>I</i>
            </button>
            <button
              className="toolbar-btn"
              data-command="underline"
              title="Underline (Ctrl+U)"
            >
              <u>U</u>
            </button>
            <button
              className="toolbar-btn"
              data-command="strikeThrough"
              title="Strikethrough"
            >
              <s>S</s>
            </button>
          </div>

          <div className="toolbar-group">
            <button className="toolbar-btn" data-command="insertOrderedList" title="Numbered List">
              1.
            </button>
            <button className="toolbar-btn" data-command="insertUnorderedList" title="Bulleted List">
              •
            </button>
            <button className="toolbar-btn" data-command="indent" title="Indent">
              ↦
            </button>
            <button className="toolbar-btn" data-command="outdent" title="Outdent">
              ↤
            </button>
          </div>

          <div className="toolbar-group">
            <button className="toolbar-btn" data-command="justifyLeft" title="Align Left">
              ⟸
            </button>
            <button className="toolbar-btn" data-command="justifyCenter" title="Center">
              ⟷
            </button>
            <button className="toolbar-btn" data-command="justifyRight" title="Align Right">
              ⟹
            </button>
            <button className="toolbar-btn" data-command="justifyFull" title="Justify">
              ≡
            </button>
          </div>

          <div className="toolbar-group">
            <button
              className="toolbar-btn"
              id="btn-insert-clause"
              title="Insert Clause (Ctrl+K)"
            >
              📚
            </button>
            <button
              className="toolbar-btn"
              id="btn-find-replace"
              title="Find (Ctrl+F)"
            >
              🔍
            </button>
            <button
              className="toolbar-btn"
              data-command="addComment"
              title="Add Comment - Select text first"
            >
              💬
            </button>
          </div>

          <div className="toolbar-group">
            <button className="toolbar-btn" data-command="removeFormat" title="Clear Formatting">
              ⌫
            </button>
          </div>
        </div>

        <div className="editor-wrapper">
          <div className="editor-canvas">
            <div
              id="editor"
              className="editor-content"
              contentEditable={true}
              ref={editorRef}
            ></div>
          </div>
        </div>

        <div className="status-bar">
          <div className="status-left">
            <span id="wordCount">Words: 0</span>
            <span id="charCount">Characters: 0</span>
          </div>
          <div className="status-right">
            <span id="autoSave">Ready</span>
          </div>
        </div>
      </div>
    </>
  );
};

export default withStreamlitConnection(StreamlitDocEditor);
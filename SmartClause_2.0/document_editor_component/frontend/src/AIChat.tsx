import React, { useState, useEffect, useRef, useCallback } from 'react';
import './AIChatStyles.css';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: any;
}

interface AIChatProps {
  documentContent: string;
  documentMetadata: {
    type: string;
    subtype?: string;
    title: string;
  };
  matterMetadata: {
    name: string;
    client_name: string;
    jurisdiction: string;
  };
  versionId: string;
  sessionId: string;
  onSendMessage: (message: string) => void;
  onApplyEdit: (edit: any) => void;
  isStreaming: boolean;
  messages: Message[];
}

const QuickAction: React.FC<{
  label: string;
  icon: string;
  onClick: () => void;
}> = ({ label, icon, onClick }) => (
  <button className="quick-action-btn" onClick={onClick} title={label}>
    <span className="quick-action-icon">{icon}</span>
    <span className="quick-action-label">{label}</span>
  </button>
);

const MessageBubble: React.FC<{
  message: Message;
  onApplyEdit?: (edit: any) => void;
}> = ({ message, onApplyEdit }) => {
  const isUser = message.role === 'user';
  const hasEdits = message.metadata?.edits && message.metadata.edits.length > 0;

  return (
    <div className={`message-bubble ${isUser ? 'user-message' : 'ai-message'}`}>
      <div className="message-header">
        <span className="message-role">
          {isUser ? '👤 You' : '🤖 AI Assistant'}
        </span>
        <span className="message-time">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </span>
      </div>
      <div className="message-content">
        {message.content}
      </div>
      {hasEdits && (
        <div className="message-edits">
          <div className="edits-header">💡 Suggested Edits:</div>
          {message.metadata.edits.map((edit: any, idx: number) => (
            <div key={idx} className="edit-suggestion">
              <div className="edit-reason">{edit.reason}</div>
              <div className="edit-preview">
                <div className="edit-target">
                  <strong>Find:</strong> {edit.target.substring(0, 100)}...
                </div>
                <div className="edit-replacement">
                  <strong>Replace with:</strong> {edit.replacement.substring(0, 100)}...
                </div>
              </div>
              <button
                className="apply-edit-btn"
                onClick={() => onApplyEdit && onApplyEdit(edit)}
              >
                Apply This Edit
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export const AIChat: React.FC<AIChatProps> = ({
  documentContent,
  documentMetadata,
  matterMetadata,
  versionId,
  sessionId,
  onSendMessage,
  onApplyEdit,
  isStreaming,
  messages
}) => {
  const [inputValue, setInputValue] = useState('');
  const [isExpanded, setIsExpanded] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const quickActions = [
    { label: 'Summarize', icon: '📄', prompt: 'Provide a brief summary of this document.' },
    { label: 'Formalize', icon: '⚖️', prompt: 'Make this document more formal.' },
    {label: 'Citations', icon: '📚', prompt: 'Add relevant Kenyan legal citations.' },
    { label: 'Check', icon: '✓', prompt: 'Review for compliance with Kenyan law.' },
    { label: 'Clarity', icon: '💡', prompt: 'Suggest improvements for clarity.' },
    { label: 'Missing Info', icon: '🔍', prompt: 'Find placeholders or missing information.' }
  ];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  const handleSend = useCallback(() => {
    if (inputValue.trim() && !isStreaming) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  }, [inputValue, isStreaming, onSendMessage]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleQuickAction = useCallback(
    (prompt: string) => {
      if (!isStreaming) {
        onSendMessage(prompt);
      }
    },
    [isStreaming, onSendMessage]
  );

  return (
    <div className={`ai-chat-panel ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div className="chat-header">
        <div className="chat-title">
          <span className="chat-icon">💬</span>
          <span>AI Assistant</span>
        </div>
        <div className="chat-controls">
          <button
            className="chat-control-btn"
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? '❯' : '❮'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <>
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">👋</div>
                <h3>Hi! I'm your AI legal assistant</h3>
                <p>
                  I can help you edit this document, answer questions, and ensure compliance
                  with Kenyan law.
                </p>
                <p className="quick-start">Try one of the quick actions below to get started!</p>
              </div>
            ) : (
              <>
                {messages.map((msg, idx) => (
                  msg.role !== 'system' && (
                    <MessageBubble
                      key={idx}
                      message={msg}
                      onApplyEdit={onApplyEdit}
                    />
                  )
                ))}
              </>
            )}
            {isStreaming && (
              <div className="streaming-indicator">
                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="quick-actions">
            {quickActions.map((action, idx) => (
              <QuickAction
                key={idx}
                label={action.label}
                icon={action.icon}
                onClick={() => handleQuickAction(action.prompt)}
              />
            ))}
          </div>

          <div className="chat-input-container">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Ask a question or request an edit..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming}
              rows={1}
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={!inputValue.trim() || isStreaming}
              title="Send message"
            >
              {isStreaming ? '⏸' : '➤'}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default AIChat;

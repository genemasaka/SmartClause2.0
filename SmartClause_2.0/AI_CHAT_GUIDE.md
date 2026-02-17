# AI Chat Interface - Usage Guide

## Overview

The AI Chat interface is an integrated feature in the SmartClause document editor that allows users to:
- Ask questions about their documents
- Request specific edits with AI assistance
- Check legal compliance
- Improve document quality in real-time

## Features

### Quick Actions
- **Summarize**: Get a quick summary of the document
- **Formalize**: Make the language more formal and professional
- **Citations**: Add relevant Kenyan legal citations
- **Check**: Review for Kenyan law compliance
- **Clarity**: Improve readability and clarity
- **Missing Info**: Find placeholders or missing information

### Chat Capabilities
1. **Contextual Understanding**: AI has access to full document content and metadata
2. **Streaming Responses**: Real-time response as AI generates answers
3. **Edit Suggestions**: AI can suggest specific edits with before/after previews
4. **Conversation History**: Maintains context across multiple messages
5. **Session Persistence**: Chat history is saved with the document version

## Using the Chat Interface

### Opening the Chat
1. Navigate to any document in the editor
2. Look for the chat icon (💬) in the top-right area
3. Click to expand the chat panel

### Asking Questions
Simply type your question in the input box at the bottom. Examples:
- "What is the main purpose of this agreement?"
- "Are all required KRA PIN fields included?"
- "Does this comply with the Employment Act 2007?"

### Requesting Edits
Use natural language to describe the edit you want:
- "Change the first paragraph to be more formal"
- "Add a clause about data protection compliance"
- "Fix grammatical errors in section 3"

### Applying Suggested Edits
1. AI will suggest edits with a preview showing what will change
2. Review the "Find" and "Replace with" sections
3. Click "Apply This Edit" to make the change
4. The document updates automatically

### Using Quick Actions
Click any quick action button for instant AI assistance with common tasks. The AI will process your document and provide relevant feedback or suggestions.

## Technical Details

### Architecture
- **Backend**: `ai_chat_service.py` handles AI interactions
- **Frontend**: React component (`AIChat.tsx`) with Material-like design
- **Database**: `chat_messages` table stores conversation history
- **Integration**: Seamless connection with TipTap document editor

### Performance
- **Response Time**: < 2 seconds to first token
- **Streaming**: Real-time word-by-word response
- **Bundle Size**: < 100 KB additional load
- **Context Window**: Supports documents up to 3,000 words efficiently

### Session Management
- Each document version has its own chat sessions
-  Chat history persists across browser sessions
- Sessions can be cleared via the header controls
- Maximum 50 messages per session (auto-cleanup)

## Troubleshooting

### Chat Not Responding
1. Check internet connection
2. Verify OpenAI API key is set in `.env`
3. Check browser console for errors
4. Refresh the page and try again

### Edits Not Applying
1. Ensure you clicked "Apply This Edit"
2. Check that the target text still exists in the document
3. Try rephrasing your edit request to be more specific
4. Manual edits may be needed for complex changes

### Performance Issues
1. For very long documents (>5,000 words), responses may be slower
2. Clear old chat sessions if you have many messages
3. Use specific sections rather than whole document for targeted help

## Best Practices

1. **Be Specific**: "Change paragraph 2 to add liability limits" works better than "make it better"
2. **Use Context**: Reference specific sections, clauses, or parties
3. **Review Edits**: Always review AI suggestions before applying
4. **Iterative Approach**: Make one change at a time for better control
5. **Legal Review**: AI suggestions should be reviewed by qualified legal professionals

## Security & Privacy

- All chat messages are encrypted in transit and at rest
- Messages are only accessible by the document owner 
- No data is shared with third parties beyond OpenAI API
- Chat history can be deleted at any time
- Complies with data protection regulations

## Supported Languages

- Primary: English
- Legal Context: Kenyan law and jurisdiction
- Document Types: All SmartClause document types supported

## Keyboard Shortcuts

- `Enter`: Send message
- `Shift + Enter`: New line in message
- `Esc`: Minimize chat panel (when active)

## Limitations

1. AI suggestions should be reviewed by legal professionals
2. Very complex legal analysis may require human expertise
3. Historical or archived matters may have limited context
4. Edit suggestions work best with clear, specific requests
5. Not a substitute for legal advice or professional judgment

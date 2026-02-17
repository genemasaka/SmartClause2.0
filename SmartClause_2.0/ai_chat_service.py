"""
AI Chat Service for Document Editor
Handles AI-powered chat interactions with document context awareness.
"""

import os
import json
import logging
from typing import Dict, Any, List, Generator, Optional, Tuple
from datetime import datetime
import openai
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class AIChatService:
    """Manages AI chat interactions with document context."""
    
    def __init__(self, api_key: str = None):
        """Initialize the AI chat service with OpenAI client."""
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.max_context_tokens = 8000  # Reserve space for response
        
    def extract_document_context(
        self,
        document: Dict[str, Any],
        matter: Dict[str, Any],
        current_content: str,
        max_words: int = 3000
    ) -> str:
        """
        Extract and format document context for AI.
        
        Args:
            document: Document metadata
            matter: Matter metadata
            current_content: Current document HTML content
            max_words: Maximum words to include from document
            
        Returns:
            Formatted context string
        """
        try:
            # Extract plain text from HTML
            soup = BeautifulSoup(current_content, 'html.parser')
            plain_text = soup.get_text(separator='\n', strip=True)
            
            # Truncate if too long
            words = plain_text.split()
            if len(words) > max_words:
                plain_text = ' '.join(words[:max_words]) + '\n...[Document truncated for length]'
            
            # Build context
            context = f"""DOCUMENT CONTEXT:

Document Type: {document.get('document_type', 'Unknown')}
Document Subtype: {document.get('document_subtype', 'N/A')}
Title: {document.get('title', 'Untitled')}

Matter: {matter.get('name', 'Unknown')}
Client: {matter.get('client_name', 'Unknown')}
Jurisdiction: {matter.get('jurisdiction', 'Kenya')}

CURRENT DOCUMENT CONTENT:
{plain_text}

---

You are an AI assistant helping a legal professional edit and analyze this document. You have access to the full document content above. You can:
1. Answer questions about the document
2. Suggest specific edits (be precise about what to change and how)
3. Analyze legal compliance
4. Improve drafting quality

When suggesting edits, use this format:
EDIT: [specific location or text to find]
REPLACE WITH: [new text]
REASON: [brief explanation]
"""
            return context
            
        except Exception as e:
            logger.error(f"Error extracting document context: {e}")
            return "Error: Could not extract document context"
    
    def format_conversation_history(
        self,
        messages: List[Dict[str, Any]],
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """
        Format conversation history for OpenAI API.
        
        Args:
            messages: List of chat messages from database
            max_messages: Maximum number of messages to include
            
        Returns:
            List of formatted messages for OpenAI
        """
        try:
            # Take only recent messages
            recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
            
            # Format for OpenAI
            formatted = []
            for msg in recent_messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                # Skip system messages from history (context is added separately)
                if role == 'system':
                    continue
                    
                formatted.append({
                    'role': role,
                    'content': content
                })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting conversation history: {e}")
            return []
    
    def stream_chat_response(
        self,
        user_message: str,
        document_context: str,
        conversation_history: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.3
    ) -> Generator[str, None, None]:
        """
        Stream AI chat response with document context.
        
        Args:
            user_message: User's message
            document_context: Formatted document context
            conversation_history: Previous conversation messages
            model: OpenAI model to use
            temperature: Response randomness (0-1)
            
        Yields:
            Response chunks as they arrive
        """
        try:
            # Build messages for API
            messages = [
                {
                    'role': 'system',
                    'content': document_context
                }
            ]
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # Add current user message
            messages.append({
                'role': 'user',
                'content': user_message
            })
            
            logger.info(f"Streaming chat response with {len(messages)} messages, model: {model}")
            
            # Stream response
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=temperature,
                max_tokens=2000
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming chat response: {e}")
            yield f"\n\n[Error: {str(e)}]"
    
    def parse_edit_suggestions(self, ai_response: str) -> List[Dict[str, str]]:
        """
        Parse edit suggestions from AI response.
        
        Args:
            ai_response: Full AI response text
            
        Returns:
            List of edit suggestions with structure:
            {
                'target': 'text to find or location',
                'replacement': 'new text',
                'reason': 'explanation'
            }
        """
        try:
            edits = []
            
            # Pattern to match EDIT: ... REPLACE WITH: ... REASON: ...
            pattern = r'EDIT:\s*(.+?)\s*REPLACE WITH:\s*(.+?)\s*REASON:\s*(.+?)(?=EDIT:|$)'
            matches = re.finditer(pattern, ai_response, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                target = match.group(1).strip()
                replacement = match.group(2).strip()
                reason = match.group(3).strip()
                
                edits.append({
                    'target': target,
                    'replacement': replacement,
                    'reason': reason
                })
            
            logger.info(f"Parsed {len(edits)} edit suggestions from AI response")
            return edits
            
        except Exception as e:
            logger.error(f"Error parsing edit suggestions: {e}")
            return []
    
    def apply_edit_to_content(
        self,
        content: str,
        edit: Dict[str, str]
    ) -> Tuple[str, bool]:
        """
        Apply a single edit to document content.
        
        Args:
            content: Current document HTML content
            edit: Edit specification with 'target' and 'replacement'
            
        Returns:
            Tuple of (modified_content, success)
        """
        try:
            target = edit.get('target', '')
            replacement = edit.get('replacement', '')
            
            if not target:
                return content, False
            
            # Try to find and replace the target text
            if target in content:
                modified_content = content.replace(target, replacement, 1)
                return modified_content, True
            
            # Try case-insensitive match
            pattern = re.compile(re.escape(target), re.IGNORECASE)
            if pattern.search(content):
                modified_content = pattern.sub(replacement, content, count=1)
                return modified_content, True
            
            # Try fuzzy match (remove extra whitespace)
            normalized_target = ' '.join(target.split())
            normalized_content = ' '.join(content.split())
            
            if normalized_target in normalized_content:
                # Find position in normalized, apply to original
                # This is a simplified approach
                return content, False
            
            logger.warning(f"Could not find target text for edit: {target[:50]}...")
            return content, False
            
        except Exception as e:
            logger.error(f"Error applying edit: {e}")
            return content, False
    
    def generate_edit_preview(
        self,
        original: str,
        modified: str,
        context_chars: int = 100
    ) -> Dict[str, Any]:
        """
        Generate a preview showing the difference between original and modified content.
        
        Args:
            original: Original content
            modified: Modified content
            context_chars: Characters of context to show around changes
            
        Returns:
            Dictionary with preview information
        """
        try:
            # Find first difference
            min_len = min(len(original), len(modified))
            first_diff = 0
            
            for i in range(min_len):
                if original[i] != modified[i]:
                    first_diff = i
                    break
            
            # Extract context around the change
            start = max(0, first_diff - context_chars)
            end = min(len(modified), first_diff + context_chars)
            
            return {
                'has_changes': original != modified,
                'original_snippet': original[start:start + context_chars * 2],
                'modified_snippet': modified[start:end],
                'change_position': first_diff
            }
            
        except Exception as e:
            logger.error(f"Error generating edit preview: {e}")
            return {
                'has_changes': False,
                'error': str(e)
            }
    
    def get_quick_actions(self) -> List[Dict[str, str]]:
        """
        Get list of quick action prompts for common tasks.
        
        Returns:
            List of quick action definitions
        """
        return [
            {
                'label': 'Summarize',
                'prompt': 'Provide a brief summary of this document in 2-3 sentences.',
                'icon': '📄'
            },
            {
                'label': 'Make More Formal',
                'prompt': 'Rewrite the document to use more formal legal language while preserving all key information.',
                'icon': '⚖️'
            },
            {
                'label': 'Add Legal Citations',
                'prompt': 'Review the document and suggest where to add relevant Kenyan legal citations and statutory references.',
                'icon': '📚'
            },
            {
                'label': 'Check Compliance',
                'prompt': 'Review this document for compliance with Kenyan law and highlight any potential issues.',
                'icon': '✓'
            },
            {
                'label': 'Improve Clarity',
                'prompt': 'Identify sections that could be clearer and suggest improvements for better readability.',
                'icon': '💡'
            },
            {
                'label': 'Find Missing Info',
                'prompt': 'Identify any placeholders or missing information that needs to be filled in.',
                'icon': '🔍'
            }
        ]

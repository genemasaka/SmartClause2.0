"""
Database layer for SmartClause using Supabase PostgreSQL
Handles all database operations with proper error handling and connection pooling
"""

import os
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, date  # Added date import
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle date/datetime objects
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

 

class DatabaseManager:
    """Manages all database operations for SmartClause."""
    
    def __init__(self):
        """Initialize Supabase client with sanitization."""
        # Fetch and strip whitespace
        supabase_url = os.getenv("SUPABASE_URL", "").strip()
        supabase_anon_key = (os.getenv("SUPABASE_ANON_KEY") or "").strip()
        
        if not supabase_url or not supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")

        # Auto-correct missing protocol
        if not supabase_url.startswith("https://") and not supabase_url.startswith("http://"):
            supabase_url = f"https://{supabase_url}"

        self.client: Client = create_client(supabase_url, supabase_anon_key)
        self.user_id: Optional[str] = None
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with email and password.
        Returns the session data including access token.
        """
        try:
            auth_response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                self.user_id = auth_response.user.id
                logger.info(f"User authenticated: {auth_response.user.email}")
                
                return {
                    "success": True,
                    "user": auth_response.user,
                    "session": auth_response.session,
                    "access_token": auth_response.session.access_token if auth_response.session else None
                }
            else:
                return {"success": False, "error": "Authentication failed"}
        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": str(e)}
    
    def sign_up_user(self, email: str, password: str, user_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a new user account.
        """
        try:
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata or {}
                }
            })
            
            if auth_response.user:
                self.user_id = auth_response.user.id
                logger.info(f"User created: {auth_response.user.email}")
                
                # Create default user settings
                self.update_user_settings(self._default_settings())
                
                return {
                    "success": True,
                    "user": auth_response.user,
                    "session": auth_response.session
                }
            else:
                return {"success": False, "error": "Sign up failed"}
        
        except Exception as e:
            logger.error(f"Sign up error: {e}")
            return {"success": False, "error": str(e)}
    
    def set_session(self, access_token: str, refresh_token: str):
        """
        Set an existing session (e.g., from stored tokens).
        This automatically sets auth.uid() for RLS policies.
        """
        try:
            session_response = self.client.auth.set_session(access_token, refresh_token)
            
            if session_response.user:
                self.user_id = session_response.user.id
                logger.info(f"Session set for user: {session_response.user.email}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Set session error: {e}")
            return False
    
    def sign_out(self):
        """Sign out the current user."""
        try:
            self.client.auth.sign_out()
            self.user_id = None
            logger.info("User signed out")
        except Exception as e:
            logger.error(f"Sign out error: {e}")
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently authenticated user."""
        try:
            user = self.client.auth.get_user()
            if user and user.user:
                self.user_id = user.user.id
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "metadata": user.user.user_metadata
                }
            return None
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    def refresh_session(self) -> bool:
        """Refresh the current session."""
        try:
            session = self.client.auth.refresh_session()
            if session and session.user:
                self.user_id = session.user.id
                return True
            return False
        except Exception as e:
            logger.error(f"Refresh session error: {e}")
            return False
    
    def set_user(self, user_id: str):
        """
        Set the current user ID for database operations.
        Note: This should only be used when you have a valid authenticated session.
        """
        self.user_id = user_id
    
    # =========================================================================
    # MATTER OPERATIONS
    # =========================================================================
    
    def create_matter(
        self,
        name: str,
        client_name: str,
        counterparty: Optional[str] = None,
        internal_reference: Optional[str] = None,
        matter_type: Optional[str] = None,
        jurisdiction: str = "Kenya"
    ) -> Dict[str, Any]:
        """Create a new matter."""
        try:
            data = {
                "user_id": self.user_id,
                "name": name,
                "client_name": client_name,
                "counterparty": counterparty,
                "internal_reference": internal_reference,
                "matter_type": matter_type,
                "jurisdiction": jurisdiction,
                "status": "active"
            }
            
            result = self.client.table("matters").insert(data).execute()
            
            # Log activity
            self._log_activity(
                "created_matter",
                "matter",
                result.data[0]["id"],
                f"Created matter: {name}"
            )
            
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating matter: {e}")
            raise
    
    def get_matters(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all matters for the current user."""
        try:
            query = self.client.table("matters").select("*").eq("user_id", self.user_id).is_("deleted_at", None)
            
            if status:
                query = query.eq("status", status)
            
            query = query.order("updated_at", desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching matters: {e}")
            return []
    
    def get_matter(self, matter_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific matter by ID."""
        try:
            result = self.client.table("matters").select("*").eq("id", matter_id).eq("user_id", self.user_id).is_("deleted_at", None).single().execute()
            
            # Update last accessed
            self.client.table("matters").update({"last_accessed_at": datetime.now().isoformat()}).eq("id", matter_id).execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching matter {matter_id}: {e}")
            return None
    
    def update_matter(
        self,
        matter_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a matter."""
        try:
            result = self.client.table("matters").update(updates).eq("id", matter_id).eq("user_id", self.user_id).execute()
            
            self._log_activity(
                "updated_matter",
                "matter",
                matter_id,
                f"Updated matter fields: {', '.join(updates.keys())}"
            )
            
            return result.data[0] if result.data else None
        
        except Exception as e:
            logger.error(f"Error updating matter {matter_id}: {e}")
            return None
    
    def delete_matter(self, matter_id: str, hard_delete: bool = False) -> bool:
        """Delete a matter (soft delete by default)."""
        try:
            if hard_delete:
                self.client.table("matters").delete().eq("id", matter_id).eq("user_id", self.user_id).execute()
            else:
                self.client.table("matters").update({"deleted_at": datetime.now().isoformat()}).eq("id", matter_id).eq("user_id", self.user_id).execute()
            
            self._log_activity(
                "deleted_matter",
                "matter",
                matter_id,
                "Hard deleted" if hard_delete else "Soft deleted"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting matter {matter_id}: {e}")
            return False
    
    def search_matters(self, query: str) -> List[Dict[str, Any]]:
        """Full-text search across matters."""
        try:
            result = self.client.table("matters").select("*").eq("user_id", self.user_id).is_("deleted_at", None).text_search("search_vector", query).execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error searching matters: {e}")
            return []

    def get_document_counts_for_matters(self, matter_ids: List[str]) -> Dict[str, int]:
        """
        Batch fetch document counts for multiple matters.
        Returns a dictionary mapping matter_id -> count.
        """
        try:
            if not matter_ids:
                return {}
                
            # Fetch only matter_id for documents belonging to these matters
            # Using CSV format for in_ filter as requested by Supabase PostgREST 
            result = self.client.table("documents").select("matter_id").in_("matter_id", matter_ids).is_("deleted_at", None).execute()
            
            # Count manually in Python (PostgREST doesn't support easy GROUP BY count yet)
            counts = {mid: 0 for mid in matter_ids}
            for doc in result.data:
                mid = doc.get("matter_id")
                if mid in counts:
                    counts[mid] += 1
            
            return counts
            
        except Exception as e:
            logger.error(f"Error fetching document counts: {e}")
            return {mid: 0 for mid in matter_ids}
    
    # =========================================================================
    # DOCUMENT OPERATIONS
    # =========================================================================
    def _sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize a payload dictionary to ensure JSON serializability.
        Converts date/datetime objects to ISO format strings.
        """
        if payload is None:
            return None
    
        sanitized = {}
        for key, value in payload.items():
            if isinstance(value, (datetime, date)):
                sanitized[key] = value.isoformat()
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_payload(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    item.isoformat() if isinstance(item, (datetime, date)) 
                    else self._sanitize_payload(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized

    def create_document(
        self,
        matter_id: str,
        title: str,
        document_type: str,
        document_subtype: Optional[str] = None,
        generation_payload: Optional[Dict[str, Any]] = None,
        base_template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new document."""
        try:
            data = {
                "matter_id": matter_id,
                "title": title,
                "document_type": document_type,
                "document_subtype": document_subtype,
                "generation_payload": json.dumps(self._sanitize_payload(generation_payload)) if generation_payload else None,
                "base_template_id": base_template_id,
                "status": "generating"
            }
            
            result = self.client.table("documents").insert(data).execute()
            
            self._log_activity(
                "created_document",
                "document",
                result.data[0]["id"],
                f"Created document: {title}"
            )
            
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    def get_documents(self, matter_id: str, include_content: bool = False) -> List[Dict[str, Any]]:
        """
        Get all documents for a matter.
        OPTIMIZATION: By default, excludes large content fields.
        """
        try:
            if include_content:
                query = self.client.table("documents").select("*")
            else:
                # Select only light metadata fields
                query = self.client.table("documents").select("id,matter_id,title,document_type,document_subtype,status,created_at,updated_at,current_version_id")
                
            result = query.eq("matter_id", matter_id).is_("deleted_at", None).order("created_at", desc=True).execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching documents for matter {matter_id}: {e}")
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document."""
        try:
            result = self.client.table("documents").select("*").eq("id", document_id).is_("deleted_at", None).single().execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching document {document_id}: {e}")
            return None
    
    def update_document_status(
        self,
        document_id: str,
        status: str
    ) -> Optional[Dict[str, Any]]:
        """Update document status."""
        try:
            result = self.client.table("documents").update({
                "status": status,
                "last_edited_at": datetime.now().isoformat()
            }).eq("id", document_id).execute()
            
            return result.data[0] if result.data else None
        
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            return None
    

    def create_comment(
        self,
        version_id: str,
        comment_text: str,
        selected_text: Optional[str] = None,
        position_start: Optional[int] = None,
        position_end: Optional[int] = None,
        parent_comment_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new comment."""
        try:
            if not self.user_id:
                logger.error("Cannot create comment: No user_id set")
                raise ValueError("User ID must be set to create a comment")
            
            data = {
                "version_id": version_id,
                "comment_text": comment_text,
                "selected_text": selected_text,
                "position_start": position_start,
                "position_end": position_end,
                "parent_comment_id": parent_comment_id,
                "thread_id": thread_id or (parent_comment_id if parent_comment_id else None),
                "created_by": self.user_id,
                "is_resolved": False  # CRITICAL: Explicitly set to false
            }
            
            logger.info(f"Creating comment for version {version_id} by user {self.user_id}")
            logger.debug(f"Comment data: {data}")
            
            result = self.client.table("comments").insert(data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"✅ Comment created successfully: {result.data[0]['id']}")
                
                # Log the activity
                self._log_activity(
                    "created_comment",
                    "comment",
                    result.data[0]["id"],
                    f"Added comment: {comment_text[:50]}..."
                )
                
                return result.data[0]
            else:
                logger.error("Comment creation returned no data")
                raise Exception("Comment creation failed: No data returned")
        
        except Exception as e:
            logger.error(f"Error creating comment: {e}")
            logger.error(f"Version ID: {version_id}, User ID: {self.user_id}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    # =========================================================================
    # DOCUMENT VERSION OPERATIONS
    # =========================================================================
    
    def create_version(
        self,
        document_id: str,
        content: str,
        content_plain: str,
        label: Optional[str] = None,
        is_major_version: bool = False,
        change_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new document version."""
        try:
            # Get next version number
            versions = self.get_versions(document_id)
            next_version = len(versions) + 1
            
            # Count words
            word_count = len(content_plain.split())
            
            data = {
                "document_id": document_id,
                "version_number": next_version,
                "label": label or f"Version {next_version}",
                "content": content,
                "content_plain": content_plain,
                "word_count": word_count,
                "created_by": self.user_id,
                "is_major_version": is_major_version,
                "change_summary": change_summary
            }
            
            result = self.client.table("document_versions").insert(data).execute()
            version_id = result.data[0]["id"]
            
            # Update document's current_version_id
            self.client.table("documents").update({
                "current_version_id": version_id,
                "last_edited_at": datetime.now().isoformat()
            }).eq("id", document_id).execute()
            
            self._log_activity(
                "created_version",
                "document_version",
                version_id,
                f"Created version {next_version}"
            )
            
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating version: {e}")
            raise
    
    def get_versions(
        self,
        document_id: str,
        limit: Optional[int] = None,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all versions for a document."""
        try:
            # Select only metadata fields by default, exclude large content fields
            if include_content:
                fields = "*"
            else:
                fields = "id,document_id,version_number,label,word_count,created_by,created_at,is_major_version,change_summary"
            
            query = self.client.table("document_versions").select(fields).eq("document_id", document_id).order("version_number", desc=True)
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching versions: {e}")
            return []
    
    def get_latest_version(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest version of a document."""
        try:
            result = self.client.table("document_versions").select("*").eq("document_id", document_id).order("version_number", desc=True).limit(1).execute()
            
            return result.data[0] if result.data else None
        
        except Exception as e:
            logger.error(f"Error fetching latest version: {e}")
            return None
    
    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific version by ID with full content."""
        try:
            result = self.client.table("document_versions").select("*").eq("id", version_id).single().execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching version {version_id}: {e}")
            return None
    def update_version_content(
        self,
        version_id: str,
        content: str,
        content_plain: str
    ) -> Optional[Dict[str, Any]]:
        """
        Updates the content of an existing version (for autosave).
        Does not create a new version row.
        """
        try:
            word_count = len(content_plain.split())
            
            result = self.client.table("document_versions").update({
                "content": content,
                "content_plain": content_plain,
                "word_count": word_count,
            }).eq("id", version_id).execute()
            
            return result.data[0] if result.data else None
        
        except Exception as e:
            logger.error(f"Error updating version content for {version_id}: {e}")
            return None    
    # =========================================================================
    # CLAUSE LIBRARY OPERATIONS
    # =========================================================================
    
    def create_clause(
        self,
        title: str,
        category: str,
        content: str,
        content_plain: str,
        preview: Optional[str] = None,
        tags: Optional[List[str]] = None,
        document_types: Optional[List[str]] = None,
        is_system: bool = False
    ) -> Dict[str, Any]:
        """Create a new clause in the library."""
        try:
            data = {
                "user_id": None if is_system else self.user_id,
                "title": title,
                "category": category,
                "content": content,
                "content_plain": content_plain,
                "preview": preview or content_plain[:200],
                "tags": tags or [],
                "document_types": document_types or [],
                "is_system": is_system
            }
            
            result = self.client.table("clauses").insert(data).execute()
            
            self._log_activity(
                "created_clause",
                "clause",
                result.data[0]["id"],
                f"Created clause: {title}"
            )
            
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating clause: {e}")
            raise
    
    def get_clauses(
        self,
        category: Optional[str] = None,
        pinned_only: bool = False,
        include_system: bool = True,
        light_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Get clauses from the library.
        
        Args:
            category: Filter by category
            pinned_only: Only return pinned clauses
            include_system: Include system clauses
            light_mode: If True, exclude large content fields for faster loading
        """
        try:
            if light_mode:
                # Select only metadata fields (exclude content, content_plain)
                query = self.client.table("clauses").select(
                    "id,title,category,tags,usage_count,is_pinned,is_system,preview"
                ).is_("deleted_at", None)
            else:
                # Select all fields including content
                query = self.client.table("clauses").select("*").is_("deleted_at", None)
            
            # Filter by user or system clauses
            if include_system:
                query = query.or_(f"user_id.eq.{self.user_id},is_system.eq.true")
            else:
                query = query.eq("user_id", self.user_id)
            
            if category:
                query = query.eq("category", category)
            
            if pinned_only:
                query = query.eq("is_pinned", True)
            
            query = query.order("is_pinned", desc=True).order("usage_count", desc=True)
            
            result = query.execute()
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching clauses: {e}")
            return []
    
    def get_clause(self, clause_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific clause."""
        try:
            result = self.client.table("clauses").select("*").eq("id", clause_id).is_("deleted_at", None).single().execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching clause {clause_id}: {e}")
            return None
    
    def update_clause(
        self,
        clause_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a clause."""
        try:
            result = self.client.table("clauses").update(updates).eq("id", clause_id).execute()
            
            return result.data[0] if result.data else None
        
        except Exception as e:
            logger.error(f"Error updating clause: {e}")
            return None
    
    def toggle_clause_pin(self, clause_id: str) -> bool:
        """Toggle the pinned status of a clause."""
        try:
            clause = self.get_clause(clause_id)
            if not clause:
                return False
            
            new_pinned_status = not clause.get("is_pinned", False)
            self.client.table("clauses").update({"is_pinned": new_pinned_status}).eq("id", clause_id).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error toggling clause pin: {e}")
            return False
    
    def increment_clause_usage(self, clause_id: str):
        """Increment usage count when a clause is inserted."""
        try:
            self.client.rpc("increment_clause_usage", {"clause_id": clause_id}).execute()
        except Exception as e:
            logger.error(f"Error incrementing clause usage: {e}")
    
    def search_clauses(self, query: str) -> List[Dict[str, Any]]:
        """Full-text search across clauses."""
        try:
            result = self.client.table("clauses").select("*").is_("deleted_at", None).or_(f"user_id.eq.{self.user_id},is_system.eq.true").text_search("search_vector", query).execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error searching clauses: {e}")
            return []
    
    # =========================================================================
    # COMMENT OPERATIONS
    # =========================================================================
    
   
    
    def get_comments(
        self,
        version_id: str,
        thread_id: Optional[str] = None,
        include_resolved: bool = False
    ) -> List[Dict[str, Any]]:
        """Get comments for a version."""
        try:
            query = self.client.table("comments").select("*").eq("version_id", version_id).is_("deleted_at", None)
            
            if thread_id:
                query = query.eq("thread_id", thread_id)
            
            if not include_resolved:
                query = query.eq("is_resolved", False)
            
            query = query.order("created_at", desc=False)
            
            result = query.execute()
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            return []
    
    def resolve_comment(self, comment_id: str) -> bool:
        """Mark a comment as resolved."""
        try:
            self.client.table("comments").update({
                "is_resolved": True,
                "resolved_by": self.user_id,
                "resolved_at": datetime.now().isoformat()
            }).eq("id", comment_id).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error resolving comment: {e}")
            return False
    
    def delete_comment(self, comment_id: str, hard_delete: bool = False) -> bool:
        """Delete a comment."""
        try:
            if hard_delete:
                self.client.table("comments").delete().eq("id", comment_id).execute()
            else:
                self.client.table("comments").update({"deleted_at": datetime.now().isoformat()}).eq("id", comment_id).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting comment: {e}")
            return False
    
    # =========================================================================
    # TRACKED CHANGES OPERATIONS
    # =========================================================================
    
    def create_tracked_change(
        self,
        version_id: str,
        change_type: str,
        original_text: Optional[str] = None,
        new_text: Optional[str] = None,
        position_start: Optional[int] = None,
        position_end: Optional[int] = None
    ) -> Dict[str, Any]:
        """Record a tracked change."""
        try:
            data = {
                "version_id": version_id,
                "change_type": change_type,
                "original_text": original_text,
                "new_text": new_text,
                "position_start": position_start,
                "position_end": position_end,
                "created_by": self.user_id,
                "status": "pending"
            }
            
            result = self.client.table("tracked_changes").insert(data).execute()
            
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating tracked change: {e}")
            raise
    
    def get_tracked_changes(
        self,
        version_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tracked changes for a version."""
        try:
            query = self.client.table("tracked_changes").select("*").eq("version_id", version_id)
            
            if status:
                query = query.eq("status", status)
            
            query = query.order("created_at", desc=False)
            
            result = query.execute()
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching tracked changes: {e}")
            return []
    
    def accept_change(self, change_id: str) -> bool:
        """Accept a tracked change."""
        try:
            self.client.table("tracked_changes").update({
                "status": "accepted",
                "reviewed_by": self.user_id,
                "reviewed_at": datetime.now().isoformat()
            }).eq("id", change_id).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error accepting change: {e}")
            return False
    
    def reject_change(self, change_id: str) -> bool:
        """Reject a tracked change."""
        try:
            self.client.table("tracked_changes").update({
                "status": "rejected",
                "reviewed_by": self.user_id,
                "reviewed_at": datetime.now().isoformat()
            }).eq("id", change_id).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error rejecting change: {e}")
            return False
    
    def batch_create_tracked_changes(self, changes: List[Dict[str, Any]]):
        """
        Batch upsert tracked changes.
        Ensures all fields are properly formatted for the database.
        """
        if not changes:
            return
        
        try:
            # Process each change to ensure proper formatting
            processed_changes = []
            for change in changes:
                processed_change = {
                    "id": change.get("id"),  # Client-generated UUID
                    "version_id": change.get("version_id"),
                    "change_type": change.get("change_type", "addition"),
                    "original_text": change.get("original_text"),
                    "new_text": change.get("new_text"),
                    "position_start": change.get("position_start"),
                    "position_end": change.get("position_end"),
                    "created_by": self.user_id,
                    "status": change.get("status", "pending"),
                    "created_at": change.get("created_at", datetime.now().isoformat())
                }
                
                # Remove None values to let database defaults work
                processed_change = {k: v for k, v in processed_change.items() if v is not None}
                processed_changes.append(processed_change)
            
            # Use upsert with on_conflict parameter
            result = self.client.table("tracked_changes").upsert(
                processed_changes,
                on_conflict="id"  # Specify the conflict column
            ).execute()
            
            if result.data:
                logger.info(f"Successfully upserted {len(result.data)} tracked changes.")
            else:
                logger.warning("Upsert executed but no data returned.")
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error batch upserting tracked changes: {e}")
            logger.error(f"Changes data: {changes}")
            raise
    
    # =========================================================================
    # EXPORT OPERATIONS
    # =========================================================================
    
    def create_export(
        self,
        version_id: str,
        export_type: str,
        file_name: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        export_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an export record."""
        try:
            expires_at = datetime.now() + timedelta(days=7)  # Expire after 7 days
            
            data = {
                "version_id": version_id,
                "user_id": self.user_id,
                "export_type": export_type,
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "export_options": json.dumps(export_options, cls=DateEncoder) if export_options else None,  # Updated with cls=
                "status": "processing",
                "expires_at": expires_at.isoformat()
            }
            
            result = self.client.table("exports").insert(data).execute()
            
            self._log_activity(
                "created_export",
                "export",
                result.data[0]["id"],
                f"Created {export_type} export"
            )
            
            return result.data[0]
        
        except Exception as e:
            logger.error(f"Error creating export: {e}")
            raise
    
    def update_export_status(
        self,
        export_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Update export status."""
        try:
            data = {"status": status}
            if error_message:
                data["error_message"] = error_message
            
            self.client.table("exports").update(data).eq("id", export_id).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating export status: {e}")
            return False
    
    def get_exports(
        self,
        version_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get export records."""
        try:
            query = self.client.table("exports").select("*").eq("user_id", self.user_id)
            
            if version_id:
                query = query.eq("version_id", version_id)
            
            query = query.order("created_at", desc=True).limit(limit)
            
            result = query.execute()
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching exports: {e}")
            return []
    
    def increment_download_count(self, export_id: str):
        """Increment download count for an export."""
        try:
            self.client.table("exports").update({
                "downloaded_at": datetime.now().isoformat()
            }).eq("id", export_id).execute()
            
            # Use RPC to increment atomically
            self.client.rpc("increment_export_downloads", {"export_id": export_id}).execute()
        
        except Exception as e:
            logger.error(f"Error incrementing download count: {e}")
    
    # =========================================================================
    # USER SETTINGS OPERATIONS
    # =========================================================================
    
    def get_user_settings(self) -> Optional[Dict[str, Any]]:
        """Get user settings."""
        try:
            result = self.client.table("user_settings").select("*").eq("user_id", self.user_id).single().execute()
            
            return result.data
        
        except Exception as e:
            # If no settings exist, return defaults
            return self._default_settings()
    
    def update_user_settings(self, settings: Dict[str, Any]) -> bool:
        """Update user settings."""
        try:
            # Upsert (insert or update)
            data = {
                "user_id": self.user_id,
                **settings
            }
            
            self.client.table("user_settings").upsert(data).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False
    
    def _default_settings(self) -> Dict[str, Any]:
        """Return default user settings."""
        return {
            "firm_name": "SmartClause Legal",
            "firm_address": "Nairobi, Kenya",
            "default_jurisdiction": "Kenya",
            "default_font": "Times New Roman",
            "default_font_size": "12pt",
            "default_line_spacing": "Single",
            "auto_save_enabled": True,
            "track_changes_by_default": False,
            "scrub_pii_on_export": False
        }
    
    # =========================================================================
    # ACTIVITY LOG
    # =========================================================================
    
    def _log_activity(
        self,
        activity_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Internal method to log user activities."""
        try:
            data = {
                "user_id": self.user_id,
                "activity_type": activity_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "description": description,
                "metadata": json.dumps(metadata, cls=DateEncoder) if metadata else None  # Updated with cls=
            }
            
            self.client.table("activity_log").insert(data).execute()
        
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    def get_activity_log(
        self,
        limit: int = 50,
        offset: int = 0,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get activity log for current user."""
        try:
            query = self.client.table("activity_log").select("*").eq("user_id", self.user_id)
            
            if entity_type:
                query = query.eq("entity_type", entity_type)
            
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching activity log: {e}")
            return []
    
    # =========================================================================
    # ANALYTICS & STATISTICS
    # =========================================================================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get statistics for dashboard."""
        try:
            stats = {}
            
            # Total matters
            matters_result = self.client.table("matters").select("id", count="exact").eq("user_id", self.user_id).is_("deleted_at", None).execute()
            stats["total_matters"] = matters_result.count
            
            # Active matters
            active_matters = self.client.table("matters").select("id", count="exact").eq("user_id", self.user_id).eq("status", "active").is_("deleted_at", None).execute()
            stats["active_matters"] = active_matters.count
            
            # Total documents
            # Get all matters first
            user_matters = self.get_matters()
            matter_ids = [m["id"] for m in user_matters]
            
            if matter_ids:
                docs_result = self.client.table("documents").select("id", count="exact").in_("matter_id", matter_ids).is_("deleted_at", None).execute()
                stats["total_documents"] = docs_result.count
            else:
                stats["total_documents"] = 0
            
            # Total clauses
            clauses_result = self.client.table("clauses").select("id", count="exact").eq("user_id", self.user_id).is_("deleted_at", None).execute()
            stats["total_clauses"] = clauses_result.count
            
            # Recent activity count
            recent_activity = self.client.table("activity_log").select("id", count="exact").eq("user_id", self.user_id).gte("created_at", (datetime.now() - timedelta(days=7)).isoformat()).execute()
            stats["recent_activity_count"] = recent_activity.count
            
            return stats
        
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            return {}
    
    # =========================================================================
    # SUBSCRIPTION & PAYMENT OPERATIONS
    # =========================================================================

    def create_subscription(
        self,
        user_id: str,
        tier: str,
        credits: int = 0,
        end_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create or update a user subscription."""
        try:
            data = {
                "user_id": user_id,
                "subscription_tier": tier,
                "credits_remaining": credits,
                "credits_total": credits,
                "subscription_start_date": datetime.now().isoformat(),
                "subscription_end_date": end_date,  # Expecting ISO format string or None
                "status": "active",
                "auto_renew": False
            }
            
            # Upsert checks for conflict on user_id
            result = self.client.table("user_subscriptions").upsert(data, on_conflict="user_id").execute()
            
            self._log_activity(
                "created_subscription",
                "subscription",
                result.data[0]["id"] if result.data else "unknown",
                f"Created/Updated {tier} subscription"
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return None

    def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details for a user."""
        try:
            result = self.client.table("user_subscriptions").select("*").eq("user_id", user_id).single().execute()
            return result.data
        except Exception as e:
            # Silence error as it's common for new users to not have one yet
            return None

    def update_subscription_credits(self, user_id: str, credits_delta: int) -> Optional[Dict[str, Any]]:
        """
        Update credit balance (add or subtract).
        Returns the updated subscription record.
        """
        try:
            # Fetch current subscription to calculate new balance
            # START TRANSACTION equivalent (Optimistic locking logic or RPC preferred)
            # For now using python logic, assuming low concurrency for individual user
            sub = self.get_user_subscription(user_id)
            if not sub:
                return None
            
            current_credits = sub.get("credits_remaining") or 0
            new_credits = max(0, current_credits + credits_delta)
            
            result = self.client.table("user_subscriptions").update({
                "credits_remaining": new_credits,
                "updated_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating credits: {e}")
            return None

    def check_subscription_active(self, user_id: str) -> bool:
        """Check if user has an active subscription (DB level check)."""
        sub = self.get_user_subscription(user_id)
        if not sub:
            return False
            
        if sub.get("status") != "active":
            return False
            
        # Check expiry if standard
        if sub.get("subscription_tier") == "standard":
             end_date_str = sub.get("subscription_end_date")
             if end_date_str:
                expiry = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                # Handle timezone naive vs aware
                now = datetime.now(expiry.tzinfo) if expiry.tzinfo else datetime.now()
                if expiry < now:
                    return False
        
        return True

    def expire_subscription(self, user_id: str) -> bool:
        """Mark subscription as expired."""
        try:
            self.client.table("user_subscriptions").update({
                "status": "expired",
                "updated_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error expiring subscription: {e}")
            return False

    def create_payment_transaction(
        self, 
        user_id: str, 
        amount: float, 
        transaction_type: str, 
        checkout_request_id: str,
        phone_number_hash: str,
        credits_purchased: int = 0,
        organization_id: Optional[str] = None,
        seats: Optional[int] = None,
        tier: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Record a new payment transaction."""
        try:
            data = {
                "user_id": user_id,
                "amount": amount,
                "transaction_type": transaction_type,
                "checkout_request_id": checkout_request_id,
                "phone_number_hash": phone_number_hash,
                "credits_purchased": credits_purchased,
                "payment_status": "pending",
                "payment_method": "mpesa",
                "transaction_date": datetime.now().isoformat(),
                "verification_attempts": 0,
                # Store additional metadata if provided
                "metadata": {
                    "organization_id": organization_id,
                    "seats": seats,
                    "tier": tier
                }
            }
            result = self.client.table("payment_transactions").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None

    def update_payment_status(self, checkout_request_id: str, status: str, receipt_number: Optional[str] = None) -> Dict[str, Any]:
        """Update status of a payment transaction."""
        try:
            updates = {
                "payment_status": status
                # "updated_at": datetime.now().isoformat()  # Column not in schema
            }
            if receipt_number:
                updates["mpesa_receipt_number"] = receipt_number
                
            self.client.table("payment_transactions").update(updates).eq("checkout_request_id", checkout_request_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
            return False

    def get_user_payment_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get payment history for a user."""
        try:
            result = self.client.table("payment_transactions").select("*").eq("user_id", user_id).order("transaction_date", desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching payment history: {e}")
            return []

    def log_document_generation(self, user_id: str, document_id: str, credits_used: int, tier: str) -> bool:
        """Log document generation for auditing/usage tracking."""
        try:
            data = {
                "user_id": user_id,
                "document_id": document_id,
                "credits_used": credits_used,
                "subscription_tier": tier,
                "generated_at": datetime.now().isoformat()
            }
            self.client.table("document_generation_logs").insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error logging generation: {e}")
            return False

    def get_user_generation_count(self, user_id: str) -> int:
        """Get total documents generated by user."""
        try:
            # Returning count using exact=True
            result = self.client.table("document_generation_logs").select("id", count="exact").eq("user_id", user_id).execute()
            return result.count
        except Exception as e:
            logger.error(f"Error counting generations: {e}")
            return 0

    def get_payment_transaction_by_checkout_id(self, checkout_request_id: str) -> Optional[Dict[str, Any]]:
        """Get payment transaction by checkout request ID."""
        try:
            result = self.client.table("payment_transactions").select("*").eq("checkout_request_id", checkout_request_id).single().execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching transaction by checkout ID: {e}")
            return None

    def update_subscription_end_date(self, user_id: str, end_date: str) -> bool:
        """Update subscription end date (for renewals)."""
        try:
            self.client.table("user_subscriptions").update({
                "subscription_end_date": end_date,
                "updated_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating subscription end date: {e}")
            return False

    # =========================================================================
    # ORGANIZATION AND SUBSCRIPTION OPERATIONS
    # =========================================================================
    
    def create_organization(
        self,
        name: str,
        email_domain: Optional[str],
        admin_user_id: str,
        subscription_tier: str,
        billing_email: str
    ) -> List[Dict[str, Any]]:
        """Create a new organization."""
        try:
            data = {
                "name": name,
                "email_domain": email_domain,
                "admin_user_id": admin_user_id,
                "subscription_tier": subscription_tier,
                "billing_email": billing_email,
                "is_verified": True if email_domain else False
            }
            
            result = self.client.table("organizations").insert(data).execute()
            
            logger.info(f"Organization created: {name}")
            return result.data
        
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise
    
    def get_organization_by_domain(self, email_domain: str) -> Optional[Dict[str, Any]]:
        """Find organization by email domain."""
        try:
            result = self.client.table("organizations")\
                .select("*")\
                .eq("email_domain", email_domain)\
                .eq("is_verified", True)\
                .single()\
                .execute()
            
            return result.data
        
        except Exception as e:
            logger.debug(f"No organization found for domain {email_domain}: {e}")
            return None
    
    def get_user_organization(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's organization."""
        try:
            result = self.client.table("organizations")\
                .select("*, organization_members!inner(role, status)")\
                .eq("organization_members.user_id", user_id)\
                .eq("organization_members.status", "active")\
                .single()\
                .execute()
            
            return result.data
        
        except Exception as e:
            logger.debug(f"No organization found for user {user_id}: {e}")
            return None
    
    def create_organization_subscription(
        self,
        organization_id: str,
        subscription_tier: str,
        seats_purchased: int,
        price_per_seat: int
    ) -> List[Dict[str, Any]]:
        """Create organization subscription."""
        try:
            period_start = datetime.now()
            period_end = period_start + timedelta(days=30)
            
            data = {
                "organization_id": organization_id,
                "subscription_tier": subscription_tier,
                "status": "active",
                "seats_purchased": seats_purchased,
                "seats_used": 0,
                "price_per_seat": price_per_seat,
                "current_period_start": period_start.isoformat(),
                "current_period_end": period_end.isoformat(),
                "next_billing_date": period_end.isoformat()
            }
            
            result = self.client.table("organization_subscriptions").insert(data).execute()
            
            logger.info(f"Subscription created for organization {organization_id}")
            return result.data
        
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            raise
    
    def get_organization_subscription(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get organization's active subscription."""
        try:
            result = self.client.table("organization_subscriptions")\
                .select("*")\
                .eq("organization_id", organization_id)\
                .eq("status", "active")\
                .single()\
                .execute()
            
            return result.data
        
        except Exception as e:
            logger.debug(f"No active subscription found for organization {organization_id}: {e}")
            return None
    
    def add_organization_member(
        self,
        organization_id: str,
        user_id: str,
        role: str = 'member',
        invited_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Add member to organization."""
        try:
            data = {
                "organization_id": organization_id,
                "user_id": user_id,
                "role": role,
                "status": "active",
                "invited_by": invited_by
            }
            
            result = self.client.table("organization_members")\
                .upsert(data, on_conflict="organization_id,user_id")\
                .execute()
            
            logger.info(f"Added user {user_id} to organization {organization_id}")
            return result.data
        
        except Exception as e:
            logger.error(f"Error adding organization member: {e}")
            raise
    
    def get_organization_members(
        self,
        organization_id: str,
        include_suspended: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all members of an organization."""
        try:
            query = self.client.table("organization_members")\
                .select("*, users:user_id(*)")\
                .eq("organization_id", organization_id)
            
            if not include_suspended:
                query = query.eq("status", "active")
            
            result = query.execute()
            return result.data
        
        except Exception as e:
            logger.error(f"Error fetching organization members: {e}")
            return []
    
    def record_document_usage(
        self,
        user_id: str,
        organization_id: str,
        document_type: str,
        billing_period_start: datetime,
        billing_period_end: datetime
    ) -> bool:
        """Record document creation for usage tracking."""
        try:
            data = {
                "user_id": user_id,
                "organization_id": organization_id,
                "document_type": document_type,
                "billing_period_start": billing_period_start.isoformat(),
                "billing_period_end": billing_period_end.isoformat()
            }
            
            self.client.table("document_usage").insert(data).execute()
            
            logger.info(f"Recorded document usage for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error recording document usage: {e}")
            return False
    
    def get_user_document_usage(
        self,
        user_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> int:
        """Get user's document usage count for a period."""
        try:
            result = self.client.table("document_usage")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", period_start.isoformat())\
                .lt("created_at", period_end.isoformat())\
                .execute()
            
            return result.count or 0
        
        except Exception as e:
            logger.error(f"Error getting document usage: {e}")
            return 0
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query using Supabase RPC.
        Note: This requires creating a custom RPC function in Supabase.
        For now, this is a placeholder for compatibility with organization_manager.
        """
        logger.warning("execute_query called but not fully implemented. Use specific methods instead.")
        return []
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def cleanup_expired_exports(self):
        """Delete expired exports (run as scheduled job)."""
        try:
            now = datetime.now().isoformat()
            result = self.client.table("exports").delete().lt("expires_at", now).eq("status", "ready").execute()
            
            logger.info(f"Cleaned up {len(result.data)} expired exports")
        
        except Exception as e:
            logger.error(f"Error cleaning up exports: {e}")
    
    def batch_delete_old_versions(self, document_id: str, keep_count: int = 10):
        """Delete old versions, keeping only the most recent N versions."""
        try:
            versions = self.get_versions(document_id)
            
            if len(versions) > keep_count:
                old_versions = versions[keep_count:]
                old_version_ids = [v["id"] for v in old_versions if not v.get("is_major_version")]
                
                if old_version_ids:
                    self.client.table("document_versions").delete().in_("id", old_version_ids).execute()
                    logger.info(f"Deleted {len(old_version_ids)} old versions for document {document_id}")
        
        except Exception as e:
            logger.error(f"Error batch deleting versions: {e}")

    # =============================================================================
    # CASE MANAGEMENT OPERATIONS
    # =============================================================================
    
    def create_case(
        self,
        matter_id: str,
        user_id: str,
        organization_id: Optional[str],
        **case_data
    ) -> Optional[Dict[str, Any]]:
        """Create a new case."""
        try:
            data = {
                "matter_id": matter_id,
                "user_id": user_id,
                "organization_id": organization_id,
                **case_data
            }
            
            result = self.client.table("cases").insert(data).execute()
            logger.info(f"Case created for matter {matter_id}")
            return result.data[0] if result.data else None
        
        except Exception as e:
            logger.error(f"Error creating case: {e}")
            return None
    
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get case by ID."""
        try:
            result = self.client.table("cases").select("*").eq("id", case_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting case: {e}")
            return None
    
    def update_case(self, case_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update case details."""
        try:
            result = self.client.table("cases").update(updates).eq("id", case_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating case: {e}")
            return None
    
    def get_cases_by_matter(self, matter_id: str) -> List[Dict[str, Any]]:
        """Get all cases for a matter."""
        try:
            result = self.client.table("cases").select("*").eq("matter_id", matter_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting cases: {e}")
            return []
    
    def delete_case(self, case_id: str) -> bool:
        """Delete a case (cascades to events, tasks, etc.)."""
        try:
            self.client.table("cases").delete().eq("id", case_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting case: {e}")
            return False
    
    # Case Events
    
    def create_case_event(self, case_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a case event."""
        try:
            data = {"case_id": case_id, **event_data}
            result = self.client.table("case_events").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating case event: {e}")
            return None
    
    def get_case_events(self, case_id: str) -> List[Dict[str, Any]]:
        """Get all events for a case, ordered by date."""
        try:
            result = (
                self.client.table("case_events")
                .select("*")
                .eq("case_id", case_id)
                .order("event_date", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting case events: {e}")
            return []
    
    def update_case_event(self, event_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a case event."""
        try:
            result = self.client.table("case_events").update(updates).eq("id", event_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating case event: {e}")
            return None
    
    def delete_case_event(self, event_id: str) -> bool:
        """Delete a case event."""
        try:
            self.client.table("case_events").delete().eq("id", event_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting case event: {e}")
            return False
    
    # Case Tasks
    
    def create_case_task(self, case_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a case task."""
        try:
            data = {"case_id": case_id, **task_data}
            logger.info(f"Creating case task with data: {data}")
            
            result = self.client.table("case_tasks").insert(data).execute()
            
            logger.info(f"Task creation result: {result.data if result and result.data else 'No data returned'}")
            
            if result and result.data:
                logger.info(f"Task created successfully: {result.data[0].get('id')}")
                return result.data[0]
            else:
                logger.warning("Task creation returned no data")
                return None
                
        except Exception as e:
            logger.error(f"Error creating case task: {e}", exc_info=True)
            logger.error(f"Task data that failed: {data}")
            return None
    
    def get_case_tasks(self, case_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks for a case, optionally filtered by status."""
        try:
            logger.info(f"Fetching tasks for case_id: {case_id}, status: {status}")
            
            query = self.client.table("case_tasks").select("*").eq("case_id", case_id)
            
            if status:
                query = query.eq("status", status)
            
            result = query.order("due_date", desc=False).execute()
            
            logger.info(f"Found {len(result.data) if result.data else 0} tasks for case {case_id}")
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting case tasks: {e}", exc_info=True)
            return []
    
    def update_case_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a case task."""
        try:
            result = self.client.table("case_tasks").update(updates).eq("id", task_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating case task: {e}")
            return None
    
    def delete_case_task(self, task_id: str) -> bool:
        """Delete a case task."""
        try:
            self.client.table("case_tasks").delete().eq("id", task_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting case task: {e}")
            return False
    
    # Case Documents
    
    def link_document_to_case(
        self,
        case_id: str,
        document_id: str,
        link_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Link a document to a case."""
        try:
            data = {
                "case_id": case_id,
                "document_id": document_id,
                **link_data
            }
            result = self.client.table("case_documents").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error linking document to case: {e}")
            return None
    
    def get_case_documents(self, case_id: str) -> List[Dict[str, Any]]:
        """Get all documents linked to a case."""
        try:
            result = (
                self.client.table("case_documents")
                .select("*, documents(*)")
                .eq("case_id", case_id)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting case documents: {e}")
            return []
    
    def unlink_document_from_case(self, case_id: str, document_id: str) -> bool:
        """Unlink a document from a case."""
        try:
            self.client.table("case_documents").delete().eq("case_id", case_id).eq("document_id", document_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error unlinking document from case: {e}")
            return False
    
    # Case Notes
    
    def create_case_note(self, case_id: str, note_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a case note."""
        try:
            data = {"case_id": case_id, **note_data}
            result = self.client.table("case_notes").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating case note: {e}")
            return None
    
    def get_case_notes(
        self,
        case_id: str,
        note_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get notes for a case, optionally filtered by type."""
        try:
            query = self.client.table("case_notes").select("*").eq("case_id", case_id)
            
            if note_type:
                query = query.eq("note_type", note_type)
            
            result = query.order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting case notes: {e}")
            return []
    
    def update_case_note(self, note_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a case note."""
        try:
            result = self.client.table("case_notes").update(updates).eq("id", note_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating case note: {e}")
            return None
    
    def delete_case_note(self, note_id: str) -> bool:
        """Delete a case note."""
        try:
            self.client.table("case_notes").delete().eq("id", note_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting case note: {e}")
            return False


# =============================================================================
# HELPER FUNCTIONS FOR RPC CALLS (Add these to Supabase)
# =============================================================================

"""
-- SQL Functions to add to Supabase

-- Increment clause usage
CREATE OR REPLACE FUNCTION increment_clause_usage(clause_id UUID)
RETURNS void AS $
BEGIN
    UPDATE clauses 
    SET usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE id = clause_id;
END;
$ LANGUAGE plpgsql;

-- Increment export downloads
CREATE OR REPLACE FUNCTION increment_export_downloads(export_id UUID)
RETURNS void AS $
BEGIN
    UPDATE exports 
    SET download_count = download_count + 1
    WHERE id = export_id;
END;
$ LANGUAGE plpgsql;
"""
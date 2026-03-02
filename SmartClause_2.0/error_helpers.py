"""
Error Helpers for SmartClause
Provides user-friendly error messages by classifying exceptions.
Raw details are logged for developers; users see clear guidance.
"""

import logging
import traceback as tb
import streamlit as st

logger = logging.getLogger(__name__)


# ============================================================================
# ERROR CLASSIFICATION
# ============================================================================

def _classify(e: Exception) -> str:
    """Classify an exception into a user-friendly category."""
    msg = str(e).lower()

    # Network / connectivity
    if any(kw in msg for kw in [
        "connection", "timeout", "timed out", "network",
        "unreachable", "dns", "socket", "ssl", "eof",
        "connection reset", "broken pipe",
    ]):
        return "network"

    # Authentication / session
    if any(kw in msg for kw in [
        "unauthorized", "401", "403", "forbidden",
        "session", "expired", "invalid login",
        "invalid credentials", "jwt", "token",
    ]):
        return "auth"

    # Database
    if any(kw in msg for kw in [
        "pgrst", "postgres", "supabase", "duplicate key",
        "unique constraint", "foreign key", "violates",
        "relation", "column", "row-level security",
        "42", "23",  # common PG error code prefixes
    ]):
        return "database"

    # OpenAI / API
    if any(kw in msg for kw in [
        "openai", "api key", "rate limit", "quota",
        "insufficient_quota", "model", "429", "500",
        "502", "503", "bad gateway", "service unavailable",
    ]):
        return "api"

    # Validation (usually already handled, but just in case)
    if any(kw in msg for kw in [
        "required", "missing", "invalid", "too short",
        "too long", "format", "must be",
    ]):
        return "validation"

    return "unknown"


# ============================================================================
# USER-FACING MESSAGES
# ============================================================================

_MESSAGES = {
    "network": {
        "matter": ("Unable to reach the server.", "Please check your internet connection and try again."),
        "search": ("Search is temporarily unavailable.", "Please check your connection and try again."),
        "chat":   ("Couldn't connect to the assistant.", "Please check your connection and try again."),
        "document": ("Couldn't load the document.", "Please check your connection and try again."),
        "default": ("Connection issue.", "Please check your internet and try again."),
    },
    "auth": {
        "login":  ("Login failed.", "Please double-check your email and password. If the problem persists, try resetting your password."),
        "signup": ("Sign-up failed.", "This email may already be registered — try logging in instead."),
        "default": ("Your session has expired.", "Please log in again to continue."),
    },
    "database": {
        "matter":  ("We couldn't save your changes.", "Please try again. If the problem persists, contact support."),
        "clause":  ("We couldn't save the clause.", "Please try again. If the problem persists, contact support."),
        "case":    ("We couldn't update the case.", "Please try again. If the problem persists, contact support."),
        "document": ("We couldn't save the document.", "Please try again. If the problem persists, contact support."),
        "default": ("A data error occurred.", "Please try again. If the problem persists, contact support."),
    },
    "api": {
        "document": ("We couldn't generate your document right now.", "Please try again in a moment. If you keep seeing this, check your API settings."),
        "chat":     ("The assistant is temporarily unavailable.", "Please try again in a moment."),
        "default":  ("The service is temporarily unavailable.", "Please try again in a moment."),
    },
    "validation": {
        "default": ("Please check your input and try again.", ""),
    },
    "unknown": {
        "matter":   ("Something went wrong while processing the matter.", "Please try again. If the problem persists, contact support."),
        "document": ("Something went wrong with the document.", "Please try again. If the problem persists, contact support."),
        "clause":   ("Something went wrong with the clause.", "Please try again. If the problem persists, contact support."),
        "case":     ("Something went wrong with the case.", "Please try again. If the problem persists, contact support."),
        "chat":     ("Something went wrong with the assistant.", "Please try again."),
        "search":   ("Search encountered an issue.", "Please try again."),
        "default":  ("Something went wrong.", "Please try again. If the problem persists, contact support."),
    },
}


def friendly_error(e: Exception, context: str = "default") -> tuple:
    """
    Classify an exception and return (user_message, recovery_hint).
    
    Args:
        e: The caught exception.
        context: A short label for what was happening, e.g. "matter",
                 "document", "chat", "login", "signup", "search", "clause", "case".
    
    Returns:
        (message: str, hint: str)
    """
    category = _classify(e)
    bucket = _MESSAGES.get(category, _MESSAGES["unknown"])
    message, hint = bucket.get(context, bucket["default"])
    return message, hint


def show_error(e: Exception, context: str = "default") -> None:
    """
    Log the exception for developers, then show a user-friendly
    error message with optional recovery guidance.
    """
    # Developer-only logging
    logger.error(
        f"[{context}] {type(e).__name__}: {e}",
        exc_info=True,
    )

    # User-facing
    message, hint = friendly_error(e, context)
    st.error(f"⚠️ {message}")
    if hint:
        st.info(f"💡 {hint}")

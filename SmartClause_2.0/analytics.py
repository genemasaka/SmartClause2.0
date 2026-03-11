import os
import traceback
import uuid
import streamlit as st
from posthog import Posthog
from dotenv import load_dotenv

load_dotenv()


@st.cache_resource
def get_posthog_client():
    api_key = os.environ.get("POSTHOG_API_KEY")
    host = os.environ.get("POSTHOG_HOST", "https://eu.i.posthog.com")

    if not api_key:
        print("[Analytics] WARNING: POSTHOG_API_KEY is not set. Analytics disabled.")
        return None

    client = Posthog(
        project_api_key=api_key,
        host=host,
        sync_mode=True,  # Required for Streamlit — prevents events being dropped on rerun
    )
    return client


def _get_session_id():
    if "_analytics_session_id" not in st.session_state:
        st.session_state["_analytics_session_id"] = str(uuid.uuid4())
    return st.session_state["_analytics_session_id"]


def _get_distinct_id():
    """Use real user ID if authenticated, otherwise fall back to session UUID."""
    if st.session_state.get("user_id"):
        return str(st.session_state["user_id"])
    return _get_session_id()


class Analytics:
    """
    Analytics tracker for SmartClause.
    Uses sync_mode for Streamlit reliability. Call identify() once after login.

    NOTE on PostHog Python SDK:
    - The Posthog instance does NOT have an identify() method in newer SDK versions.
    - Use client.set() to attach properties to a user (replaces identify).
    - Use client.alias() to link anonymous session ID to real user ID.
    - client.capture_exception() DOES exist and can be used for error tracking.
    """

    def __init__(self):
        self.client = get_posthog_client()
        self.session_id = _get_session_id()

    def _should_skip(self):
        return self.client is None

    def capture(self, event: str, properties: dict = None):
        """Send an event to PostHog."""
        if self._should_skip():
            return

        distinct_id = _get_distinct_id()
        base_props = {
            "session_id": self.session_id,
            "view": st.session_state.get("view", st.query_params.get("view", "unknown")),
        }
        if properties:
            base_props.update(properties)

        self.client.capture(
            distinct_id=distinct_id,
            event=event,
            properties=base_props,
        )
        self.client.flush()

    def identify(self, user_id: str, email: str = None, name: str = None):
        """
        Link the current anonymous session to a real user after login.

        Uses client.set() (the correct SDK method) to attach user properties,
        and client.alias() to merge the pre-login anonymous session into the
        real user profile so earlier events are not lost.
        """
        if self._should_skip():
            return

        user_id = str(user_id)
        session_id = _get_session_id()

        # Build user properties
        properties = {}
        if email:
            properties["email"] = email
        if name:
            properties["name"] = name

        # client.set() is the correct replacement for client.identify() in newer SDK versions
        if properties:
            self.client.set(distinct_id=user_id, properties=properties)

        # Alias the anonymous session to the real user so pre-auth events are merged
        if session_id != user_id:
            self.client.alias(previous_id=session_id, distinct_id=user_id)

        self.client.flush()

    def track_page_visit(self, page_name: str):
        self.capture("$pageview", {"page_name": page_name})

    def track_event(self, event_name: str, properties: dict = None):
        self.capture(event_name, properties)

    def track_error(self, error: Exception, context: str = ""):
        """Capture an error event using PostHog's built-in exception capture."""
        if self._should_skip():
            return

        self.client.capture_exception(
            error,
            distinct_id=_get_distinct_id(),
            properties={
                "context": context,
                "session_id": self.session_id,
                "traceback": traceback.format_exc(),
            },
        )
        self.client.flush()
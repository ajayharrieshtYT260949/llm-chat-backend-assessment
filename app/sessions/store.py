
import uuid
from datetime import datetime, timezone
from typing import Any


class SessionStore:
    """
    In-memory storage for conversation sessions.

    Each session contains:
    - A unique session ID
    - Creation timestamp
    - Conversation messages
    """

    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}

    def create_session(self) -> dict:
        session_id = str(uuid.uuid4())

        session = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
        }

        self.sessions[session_id] = session

        return {
            "session_id": session_id,
            "created_at": session["created_at"],
        }

    def get_session(self, session_id: str) -> dict | None:
        return self.sessions.get(session_id)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> dict:
        session = self.get_session(session_id)

        if session is None:
            raise KeyError(f"Session {session_id} not found.")

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        session["messages"].append(message)

        return message

    def get_messages(self, session_id: str) -> list[dict] | None:
        session = self.get_session(session_id)

        if session is None:
            return None

        return [
            message.copy()
            for message in session["messages"]
        ]

    def delete_session(self, session_id: str) -> bool:
        return self.sessions.pop(session_id, None) is not None


session_store = SessionStore()

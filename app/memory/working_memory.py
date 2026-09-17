import json
import time
from typing import List, Dict, Any, Optional
import tiktoken
from app.core.config import settings
from app.core.logger import logger
from app.schemas.chat import AmbientContext

class WorkingMemoryManager:
    """
    Tier 1: Working Memory (In-Memory + Redis Support)
    Maintains the active conversation context, sliding window buffer, and ambient state.
    """
    def __init__(self):
        self._local_sessions: Dict[str, Dict[str, Any]] = {}
        self._redis = None
        self._tokenizer = None
        self._init_tokenizer()
        self._init_redis()

    def _init_tokenizer(self):
        try:
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._tokenizer = None

    def _init_redis(self):
        if settings.REDIS_URL and not settings.USE_IN_MEMORY_REDIS_FALLBACK:
            try:
                import redis
                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
                logger.info("Connected to Redis for Working Memory.")
            except Exception as e:
                logger.warning(f"Redis unavailable, falling back to In-Memory store: {e}")
                self._redis = None

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        return len(text.split()) * 2

    def get_or_create_session(self, session_id: str, user_id: str = "user-dev-01", tenant_id: str = "tenant-default") -> Dict[str, Any]:
        if session_id in self._local_sessions:
            return self._local_sessions[session_id]

        new_session = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "messages": [],
            "ambient_context": AmbientContext().model_dump(),
            "active_attachments": [],
            "created_at": time.time(),
            "last_active": time.time(),
            "is_consolidated": False
        }
        self._local_sessions[session_id] = new_session
        return new_session

    def update_ambient_context(self, session_id: str, context: AmbientContext):
        session = self.get_or_create_session(session_id)
        session["ambient_context"] = context.model_dump()
        session["last_active"] = time.time()

    def add_message_turn(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        session = self.get_or_create_session(session_id)
        msg = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "tokens": self.count_tokens(content)
        }
        session["messages"].append(msg)
        session["last_active"] = time.time()
        self._trim_buffer(session)

    def _trim_buffer(self, session: Dict[str, Any]):
        """Enforce sliding window turn and token budget bounds."""
        msgs = session["messages"]
        
        # 1. Cap by max turns
        max_msgs = settings.WORKING_MEMORY_MAX_TURNS * 2  # user + assistant turns
        if len(msgs) > max_msgs:
            session["messages"] = msgs[-max_msgs:]
            msgs = session["messages"]

        # 2. Cap by token budget
        total_tokens = sum(m.get("tokens", self.count_tokens(m["content"])) for m in msgs)
        while total_tokens > settings.WORKING_MEMORY_TOKEN_BUDGET and len(msgs) > 2:
            removed = session["messages"].pop(0)
            total_tokens -= removed.get("tokens", self.count_tokens(removed["content"]))

    def get_active_context(self, session_id: str) -> Dict[str, Any]:
        session = self.get_or_create_session(session_id)
        return {
            "messages": session["messages"],
            "ambient_context": session["ambient_context"],
            "active_attachments": session.get("active_attachments", []),
            "total_turns": len(session["messages"]) // 2
        }

    def clear_session(self, session_id: str):
        if session_id in self._local_sessions:
            del self._local_sessions[session_id]

working_memory = WorkingMemoryManager()

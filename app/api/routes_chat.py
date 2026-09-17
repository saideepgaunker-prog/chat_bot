import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.schemas.chat import ChatRequest, ChatSessionDto
from app.llm.router import chat_router
from app.memory.working_memory import working_memory
from app.memory.consolidation_worker import consolidation_worker
from app.core.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/message")
async def chat_message_stream(req: ChatRequest):
    """
    Server-Sent Events (SSE) Streaming Endpoint for Developer Control Tower Assistant.
    Emits events: metadata, token, action_card, sources, suggested_chips, done.
    """
    async def event_generator():
        try:
            async for ev in chat_router.route_and_stream(req):
                yield {
                    "event": ev["event"],
                    "data": json.dumps(ev["data"])
                }
        except Exception as e:
            logger.error(f"Chat stream exception: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())

@router.get("/sessions/{session_id}")
async def get_session_details(session_id: str):
    ctx = working_memory.get_active_context(session_id)
    return {
        "session_id": session_id,
        "context": ctx
    }

@router.post("/sessions/{session_id}/consolidate")
async def consolidate_session(session_id: str, user_id: str = "user-dev-01", tenant_id: str = "tenant-default"):
    """Manually trigger distillation & consolidation of working memory into episodic memory."""
    memories = consolidation_worker.consolidate_session(session_id, user_id=user_id, tenant_id=tenant_id)
    return {
        "status": "success",
        "consolidated_memories_count": len(memories),
        "memories": memories
    }

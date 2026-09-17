from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.schemas.memory import EpisodicMemoryDto, MemoryCreateDto, MemoryFeedbackDto
from app.memory.episodic_memory import episodic_memory_service
from app.core.logger import logger

router = APIRouter(prefix="/memories", tags=["Episodic Memory"])

@router.get("", response_model=List[EpisodicMemoryDto])
async def list_user_memories(user_id: str = "user-dev-01", db: Session = Depends(get_db)):
    """Retrieve all distilled episodic memories for a developer."""
    return episodic_memory_service.list_user_memories(db, user_id)

@router.post("", response_model=EpisodicMemoryDto)
async def create_user_memory(req: MemoryCreateDto, db: Session = Depends(get_db)):
    """Manually record a user fact or preference into episodic memory."""
    return episodic_memory_service.store_memory(
        db=db,
        user_id=req.user_id,
        tenant_id=req.tenant_id,
        fact_text=req.fact_text,
        memory_type=req.memory_type,
        importance_score=req.importance_score,
        source_session_id=req.source_session_id
    )

@router.delete("/{memory_id}")
async def delete_user_memory(memory_id: str, user_id: str = "user-dev-01", db: Session = Depends(get_db)):
    """Delete a specific episodic memory."""
    deleted = episodic_memory_service.delete_memory(db, memory_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "success", "deleted_id": memory_id}

@router.delete("")
async def clear_all_memories(user_id: str = "user-dev-01", db: Session = Depends(get_db)):
    """Purge all memories for a user."""
    count = episodic_memory_service.clear_all_user_memories(db, user_id)
    return {"status": "success", "deleted_count": count}

@router.post("/feedback")
async def memory_feedback(feedback: MemoryFeedbackDto):
    """Record user relevance feedback for memory tuning."""
    logger.info(f"Received feedback for memory {feedback.memory_id}: {feedback.rating}")
    return {"status": "success", "rating": feedback.rating}

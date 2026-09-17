from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import datetime

class EpisodicMemoryDto(BaseModel):
    id: str
    user_id: str
    tenant_id: str
    memory_type: str  # preference, fact, session_summary, past_resolution
    fact_text: str
    importance_score: float
    decay_factor: float
    access_count: int
    created_at: datetime.datetime
    last_accessed_at: datetime.datetime
    source_session_id: Optional[str] = None

class MemoryCreateDto(BaseModel):
    user_id: str = "user-dev-01"
    tenant_id: str = "tenant-default"
    memory_type: str = "preference"
    fact_text: str
    importance_score: float = 1.0
    source_session_id: Optional[str] = None

class MemoryFeedbackDto(BaseModel):
    memory_id: str
    rating: int  # 1 for positive, -1 for negative
    comment: Optional[str] = None

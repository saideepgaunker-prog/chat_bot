import json
import math
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.db_models import EpisodicMemory, User
from app.models.database import SessionLocal
from app.schemas.memory import EpisodicMemoryDto, MemoryCreateDto
from app.rag.embedding import embedding_service
from app.core.config import settings
from app.core.logger import logger

class EpisodicMemoryService:
    """
    Tier 2: Episodic Memory Service
    Manages distilled cross-session developer facts, preferences, and session summaries.
    Executes semantic recall with exponential time decay and importance scoring.
    """
    def __init__(self, decay_rate: float = settings.EPISODIC_DECAY_RATE):
        self.decay_rate = decay_rate

    def store_memory(
        self,
        db: Session,
        user_id: str,
        fact_text: str,
        memory_type: str = "preference",
        importance_score: float = 1.0,
        source_session_id: Optional[str] = None,
        tenant_id: str = "tenant-default"
    ) -> EpisodicMemoryDto:
        embedding = embedding_service.embed_text(fact_text)
        
        # Conflict check & deduplication: If a memory with highly similar text or same topic exists, update it
        existing = db.query(EpisodicMemory).filter(
            EpisodicMemory.user_id == user_id,
            EpisodicMemory.memory_type == memory_type
        ).all()

        for mem in existing:
            mem_emb = json.loads(mem.embedding_json or "[]")
            sim = embedding_service.cosine_similarity(embedding, mem_emb)
            if sim > 0.85 or (memory_type == "preference" and self._is_same_preference_topic(fact_text, mem.fact_text)):
                # Update existing memory with fresh fact
                mem.fact_text = fact_text
                mem.importance_score = max(mem.importance_score, importance_score)
                mem.embedding_json = json.dumps(embedding)
                mem.last_accessed_at = datetime.datetime.utcnow()
                mem.access_count += 1
                db.commit()
                db.refresh(mem)
                logger.info(f"Updated existing episodic memory {mem.id}: {fact_text}")
                return self._to_dto(mem)

        # Create new episodic memory
        mem = EpisodicMemory(
            user_id=user_id,
            tenant_id=tenant_id,
            memory_type=memory_type,
            fact_text=fact_text,
            importance_score=importance_score,
            embedding_json=json.dumps(embedding),
            source_session_id=source_session_id,
            decay_factor=1.0,
            access_count=1,
            created_at=datetime.datetime.utcnow(),
            last_accessed_at=datetime.datetime.utcnow()
        )
        db.add(mem)
        db.commit()
        db.refresh(mem)
        logger.info(f"Stored new episodic memory for user {user_id}: {fact_text}")
        return self._to_dto(mem)

    def _is_same_preference_topic(self, text_a: str, text_b: str) -> bool:
        topics = ["repo", "language", "typescript", "python", "notification", "slack", "branch", "role"]
        a_lower = text_a.lower()
        b_lower = text_b.lower()
        for t in topics:
            if t in a_lower and t in b_lower:
                return True
        return False

    def recall_memories(
        self,
        db: Session,
        user_id: str,
        query: str,
        top_k: int = 5,
        alpha: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Semantic recall using combined Similarity + Importance + Exponential Time Decay.
        Score = (alpha * Sim + (1 - alpha) * Importance) * exp(-lambda * delta_days)
        """
        memories = db.query(EpisodicMemory).filter(EpisodicMemory.user_id == user_id).all()
        if not memories:
            return []

        query_emb = embedding_service.embed_text(query)
        now = datetime.datetime.utcnow()
        scored_memories = []

        for mem in memories:
            mem_emb = json.loads(mem.embedding_json or "[]")
            sim = embedding_service.cosine_similarity(query_emb, mem_emb)
            
            # Days since last access
            delta_days = max(0.0, (now - (mem.last_accessed_at or mem.created_at)).total_seconds() / 86400.0)
            decay = math.exp(-self.decay_rate * delta_days)

            # Combined ranking score
            base_score = (alpha * sim) + ((1.0 - alpha) * mem.importance_score)
            final_score = base_score * decay

            scored_memories.append({
                "memory": self._to_dto(mem),
                "similarity": sim,
                "importance": mem.importance_score,
                "decay": decay,
                "score": final_score
            })

            # Bump access count
            mem.last_accessed_at = now
            mem.access_count += 1

        db.commit()
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        return scored_memories[:top_k]

    def list_user_memories(self, db: Session, user_id: str) -> List[EpisodicMemoryDto]:
        memories = db.query(EpisodicMemory).filter(
            EpisodicMemory.user_id == user_id
        ).order_by(EpisodicMemory.created_at.desc()).all()
        return [self._to_dto(m) for m in memories]

    def delete_memory(self, db: Session, memory_id: str, user_id: str) -> bool:
        mem = db.query(EpisodicMemory).filter(
            EpisodicMemory.id == memory_id,
            EpisodicMemory.user_id == user_id
        ).first()
        if mem:
            db.delete(mem)
            db.commit()
            return True
        return False

    def clear_all_user_memories(self, db: Session, user_id: str) -> int:
        count = db.query(EpisodicMemory).filter(EpisodicMemory.user_id == user_id).delete()
        db.commit()
        return count

    def _to_dto(self, mem: EpisodicMemory) -> EpisodicMemoryDto:
        return EpisodicMemoryDto(
            id=mem.id,
            user_id=mem.user_id,
            tenant_id=mem.tenant_id,
            memory_type=mem.memory_type,
            fact_text=mem.fact_text,
            importance_score=mem.importance_score,
            decay_factor=mem.decay_factor,
            access_count=mem.access_count,
            created_at=mem.created_at,
            last_accessed_at=mem.last_accessed_at,
            source_session_id=mem.source_session_id
        )

episodic_memory_service = EpisodicMemoryService()

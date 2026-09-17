import pytest
from app.memory.working_memory import working_memory
from app.memory.consolidation_worker import consolidation_worker
from app.models.database import SessionLocal, init_db
from app.memory.episodic_memory import episodic_memory_service

def test_consolidation_distillation():
    init_db()
    session_id = "test-sess-consolidate-01"
    user_id = "test-dev-worker-01"
    
    # Simulate user expressing preferences in conversation
    working_memory.add_message_turn(session_id, "user", "Hi, I primarily work on repo-analytics and prefer TypeScript examples.")
    working_memory.add_message_turn(session_id, "assistant", "Got it! I will remember your repo and language preferences.")
    working_memory.add_message_turn(session_id, "user", "Where can I find branch protection settings?")
    working_memory.add_message_turn(session_id, "assistant", "You can find them under Repositories > Settings > Branch Rules.")
    
    # Run consolidation worker
    distilled = consolidation_worker.consolidate_session(session_id, user_id=user_id)
    assert len(distilled) >= 1
    
    # Check episodic memory
    db = SessionLocal()
    memories = episodic_memory_service.list_user_memories(db, user_id=user_id)
    db.close()
    
    assert any("repo-analytics" in m.fact_text or "TypeScript" in m.fact_text for m in memories)

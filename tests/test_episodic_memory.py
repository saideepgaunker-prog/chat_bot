import pytest
import datetime
from app.models.database import SessionLocal, init_db
from app.memory.episodic_memory import EpisodicMemoryService

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()

def test_store_and_recall_memory():
    db = SessionLocal()
    ems = EpisodicMemoryService()
    user_id = "test-dev-user-01"
    
    # Store preference
    ems.store_memory(
        db=db,
        user_id=user_id,
        fact_text="User prefers TypeScript for writing custom agent hooks and scripts.",
        memory_type="preference",
        importance_score=0.9
    )
    
    # Recall with query
    recalled = ems.recall_memories(db, user_id=user_id, query="How do I write an agent hook in TypeScript?", top_k=3)
    assert len(recalled) >= 1
    assert "TypeScript" in recalled[0]["memory"].fact_text
    assert recalled[0]["score"] > 0.3
    db.close()

def test_conflict_resolution_preference_update():
    db = SessionLocal()
    ems = EpisodicMemoryService()
    user_id = "test-dev-user-conflict"
    
    # Store initial repo preference
    ems.store_memory(db, user_id, "User primarily works on repo-auth", memory_type="preference")
    
    # Update to new repo
    ems.store_memory(db, user_id, "User primarily works on repo-analytics", memory_type="preference")
    
    memories = ems.list_user_memories(db, user_id)
    pref_memories = [m for m in memories if m.memory_type == "preference"]
    # Should update in place or deduplicate rather than spamming
    assert any("repo-analytics" in m.fact_text for m in pref_memories)
    db.close()

def test_memory_deletion():
    db = SessionLocal()
    ems = EpisodicMemoryService()
    user_id = "test-dev-del"
    
    mem = ems.store_memory(db, user_id, "Temporary test fact", memory_type="fact")
    deleted = ems.delete_memory(db, mem.id, user_id)
    assert deleted is True
    
    remaining = ems.list_user_memories(db, user_id)
    assert len(remaining) == 0
    db.close()

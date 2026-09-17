import pytest
from app.memory.working_memory import WorkingMemoryManager
from app.schemas.chat import AmbientContext

def test_working_memory_turn_capping():
    wm = WorkingMemoryManager()
    session_id = "test-session-01"
    
    # Add 40 message turns
    for i in range(40):
        wm.add_message_turn(session_id, "user", f"Question {i}")
        wm.add_message_turn(session_id, "assistant", f"Answer {i}")
        
    ctx = wm.get_active_context(session_id)
    # Max turns is 12, so max 24 messages
    assert len(ctx["messages"]) <= 24
    assert ctx["messages"][-1]["content"] == "Answer 39"

def test_working_memory_token_budget():
    wm = WorkingMemoryManager()
    session_id = "test-session-tokens"
    
    # Add long text
    long_text = "lorem ipsum dolor sit amet " * 200
    for i in range(10):
        wm.add_message_turn(session_id, "user", f"Turn {i} " + long_text)
        wm.add_message_turn(session_id, "assistant", f"Reply {i} " + long_text)

    ctx = wm.get_active_context(session_id)
    total_tokens = sum(wm.count_tokens(m["content"]) for m in ctx["messages"])
    assert total_tokens <= 3500

def test_ambient_context_update():
    wm = WorkingMemoryManager()
    session_id = "test-session-ambient"
    ambient = AmbientContext(current_route="/repos/core-backend/settings/branches", repo_id="core-backend")
    wm.update_ambient_context(session_id, ambient)
    
    ctx = wm.get_active_context(session_id)
    assert ctx["ambient_context"]["current_route"] == "/repos/core-backend/settings/branches"
    assert ctx["ambient_context"]["repo_id"] == "core-backend"

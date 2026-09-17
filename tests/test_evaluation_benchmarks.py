import pytest
import asyncio
from app.llm.router import chat_router
from app.schemas.chat import ChatRequest, AmbientContext
from app.models.database import SessionLocal, init_db
from app.memory.episodic_memory import episodic_memory_service

@pytest.fixture(scope="module", autouse=True)
def setup_env():
    init_db()

def test_benchmark_feature_navigation_grounding():
    async def _run():
        queries = [
            ("Where do I configure Slack alerts?", "/settings/integrations/webhooks/slack"),
            ("Where are branch protection rules?", "/repos/repo-payments/settings/branches"),
            ("Where can I find preview environments?", "/repos/repo-payments/deployments/previews"),
            ("Where is agent orchestration configured?", "/agents/orchestration/config"),
            ("Where are auto rollback policies?", "/pipelines/rollback-policies")
        ]
        
        correct_matches = 0
        for q, expected_route in queries:
            req = ChatRequest(
                session_id=f"bench-nav-{hash(q)}",
                message=q,
                ambient_context=AmbientContext(current_route="/", repo_id="repo-payments")
            )
            action_card = None
            async for ev in chat_router.route_and_stream(req):
                if ev["event"] == "action_card":
                    action_card = ev["data"]
            
            if action_card and action_card.get("route") == expected_route:
                correct_matches += 1
                
        accuracy = correct_matches / len(queries)
        print(f"\n[BENCHMARK] Feature Navigation Accuracy: {accuracy * 100:.1f}%")
        assert accuracy >= 0.90
    asyncio.run(_run())

def test_benchmark_cross_session_preference_recall():
    async def _run():
        db = SessionLocal()
        user_id = "eval-user-cross-session"
        episodic_memory_service.store_memory(
            db=db,
            user_id=user_id,
            fact_text="User works on repo-analytics and prefers TypeScript code hooks.",
            memory_type="preference"
        )
        db.close()
        
        req = ChatRequest(
            session_id="eval-sess-recalled-01",
            user_id=user_id,
            message="How do I write a custom agent hook?"
        )
        
        accumulated_tokens = []
        async for ev in chat_router.route_and_stream(req):
            if ev["event"] == "token":
                accumulated_tokens.append(ev["data"].get("delta", ""))
                
        full_text = "".join(accumulated_tokens)
        assert "TypeScript" in full_text
        assert "repo-analytics" in full_text or "preferences" in full_text.lower()
    asyncio.run(_run())

import json
import re
import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.core.config import settings
from app.core.logger import logger
from app.schemas.chat import ChatRequest, AmbientContext, ActionCard
from app.memory.working_memory import working_memory
from app.memory.episodic_memory import episodic_memory_service
from app.rag.feature_registry import feature_registry_service
from app.rag.document_store import document_store
from app.telemetry.agent_connectors import telemetry_service
from app.models.database import SessionLocal
from app.llm.gemini_client import GeminiClient
from app.llm.mock_engine import MockContextualEngine

class ChatRouter:
    def __init__(self):
        self.gemini = GeminiClient()
        self.mock_engine = MockContextualEngine()

    def classify_intent(self, message: str, ambient: AmbientContext, past_messages: List[Dict[str, Any]]) -> str:
        msg = message.lower()
        
        # 1. Telemetry / status queries
        if any(w in msg for w in ["status", "what happened", "agent find", "pr review", "telemetry", "build failed", "tests", "cve", "finished deployment", "health"]):
            return "project_telemetry"

        # 2. In-situ explainer queries
        if any(w in msg for w in ["what does", "explain", "how does this work", "what is this", "what does this switch do", "what is this switch", "threshold do"]):
            return "feature_explainer"

        # 3. Feature locator / where is queries
        if any(w in msg for w in ["where", "how do i find", "locate", "how to configure", "where can i set up", "where is", "route for", "navigate to"]):
            return "feature_locator"

        # 4. Cross-session code/hook queries with recalled preference
        if any(w in msg for w in ["custom agent hook", "custom hook", "write a hook", "my preferences", "remember"]):
            return "cross_session_memory"

        return "general"

    def rewrite_query(self, message: str, past_messages: List[Dict[str, Any]], ambient: AmbientContext) -> str:
        """Resolve anaphoric pronouns ('it', 'this', 'that') using active working memory turns."""
        msg = message
        if re.search(r'\b(it|this|that|the feature)\b', msg, re.I) and past_messages:
            last_user = next((m["content"] for m in reversed(past_messages) if m.get("role") == "user"), "")
            if last_user and len(last_user.split()) > 2:
                msg = f"{message} (Referring to prior context: {last_user})"
        return msg

    async def route_and_stream(self, req: ChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        session_id = req.session_id or f"sess-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        user_id = req.user_id or "user-dev-01"
        tenant_id = req.tenant_id or "tenant-default"
        ambient = req.ambient_context or AmbientContext()

        # Update working memory ambient context
        working_memory.update_ambient_context(session_id, ambient)
        working_mem = working_memory.get_active_context(session_id)
        past_msgs = working_mem.get("messages", [])

        # 1. Rewrite query if needed
        clean_query = self.rewrite_query(req.message, past_msgs, ambient)

        # 2. Classify intent
        intent = self.classify_intent(req.message, ambient, past_msgs)

        # 3. Recall episodic memories (Tier 2)
        db = SessionLocal()
        recalled_memories_data = []
        try:
            recalled_memories = episodic_memory_service.recall_memories(
                db=db,
                user_id=user_id,
                query=clean_query,
                top_k=settings.EPISODIC_RECALL_TOP_K
            )
            recalled_memories_data = [
                {
                    "fact_text": item["memory"].fact_text,
                    "memory_type": item["memory"].memory_type,
                    "score": item["score"]
                }
                for item in recalled_memories
            ]
        finally:
            db.close()

        # 4. Hybrid Search / RAG (Tier 3)
        matched_feature = None
        matched_doc = None
        action_card: Optional[ActionCard] = None
        sources = []
        suggested_chips = []

        # Find target repo from ambient context or query
        target_repo = ambient.repo_id
        if not target_repo or target_repo == "":
            match_repo = re.search(r'repo-[a-zA-Z0-9_-]+|core-backend|web-frontend', req.message)
            if match_repo:
                target_repo = match_repo.group(0)
            else:
                # Check user memories for preferred repo
                for m in recalled_memories_data:
                    m_repo = re.search(r'repo-[a-zA-Z0-9_-]+', m["fact_text"])
                    if m_repo:
                        target_repo = m_repo.group(0)
                        break
        target_repo = target_repo or "repo-payments"

        if intent in ["feature_locator", "general"]:
            search_res = feature_registry_service.search_features(clean_query, top_k=3)
            if search_res.best_match:
                feat_dict = search_res.best_match.model_dump()
                matched_feature = feat_dict
                action_card = feature_registry_service.resolve_deep_link(feat_dict, repo_id=target_repo)
                sources.append({
                    "title": feat_dict["name"],
                    "url": action_card.route,
                    "type": "feature_registry"
                })
                suggested_chips = [
                    f"Explain {feat_dict['name']}",
                    f"What permissions are needed for {feat_dict['name']}?",
                    f"Status of {target_repo}"
                ]

        if intent in ["feature_explainer", "feature_locator"]:
            doc_matches = document_store.search_docs(clean_query, top_k=2)
            if doc_matches:
                matched_doc = doc_matches[0]
                sources.append({
                    "title": matched_doc["title"],
                    "file": matched_doc["file"],
                    "type": "documentation"
                })
            # Also find by active route if user asked "What does this switch do?"
            if ambient.current_route and ambient.current_route != "/":
                route_feat = feature_registry_service.find_by_route(ambient.current_route)
                if route_feat and not matched_feature:
                    matched_feature = route_feat
                    action_card = feature_registry_service.resolve_deep_link(route_feat, repo_id=target_repo)

        telemetry_data = None
        if intent == "project_telemetry":
            t_obj = telemetry_service.get_repo_telemetry(target_repo)
            if t_obj:
                telemetry_data = t_obj.model_dump()
                action_card = ActionCard(
                    type="status_card",
                    title=f"Telemetry: {t_obj.name}",
                    route=f"/repos/{target_repo}",
                    breadcrumbs=["Repositories", target_repo, "Dashboard"],
                    action_label="Open Repo Dashboard",
                    status="Healthy" if t_obj.health_score > 90 else "Attention Required",
                    metadata={"health_score": t_obj.health_score, "active_branch": t_obj.active_branch}
                )
                suggested_chips = [
                    f"Show build logs for {target_repo}",
                    f"Where are branch rules for {target_repo}?",
                    "Show PR review details"
                ]

        if intent == "cross_session_memory":
            suggested_chips = [
                "Configure Slack notifications",
                "Show my remembered preferences",
                "Where do I set up webhooks?"
            ]

        # 5. Emit Initial Metadata Event
        yield {
            "event": "metadata",
            "data": {
                "session_id": session_id,
                "intent": intent,
                "recalled_memories_count": len(recalled_memories_data),
                "ambient_repo": target_repo
            }
        }

        # Context bundle for LLM engine
        llm_context = {
            "intent": intent,
            "matched_feature": matched_feature,
            "matched_doc": matched_doc,
            "telemetry": telemetry_data,
            "recalled_memories": recalled_memories_data,
            "action_card": action_card.model_dump() if action_card else None,
            "suggested_chips": suggested_chips,
            "sources": sources,
            "ambient_repo": target_repo
        }

        # 6. Stream tokens
        full_response_text = []
        
        # We use MockContextualEngine or GeminiClient if configured
        stream_generator = self.mock_engine.generate_stream(
            prompt=clean_query,
            context_data=llm_context
        )

        async for chunk in stream_generator:
            if chunk.get("type") == "token":
                delta = chunk.get("delta", "")
                full_response_text.append(delta)
                yield {
                    "event": "token",
                    "data": {"delta": delta}
                }
            elif chunk.get("type") == "error":
                yield {
                    "event": "error",
                    "data": {"error": chunk.get("message")}
                }

        complete_response = "".join(full_response_text)

        # 7. Emit Action Card Event if generated
        if action_card:
            yield {
                "event": "action_card",
                "data": action_card.model_dump()
            }

        # 8. Emit Sources & Chips Events
        if sources:
            yield {
                "event": "sources",
                "data": {"sources": sources}
            }

        if suggested_chips:
            yield {
                "event": "suggested_chips",
                "data": {"chips": suggested_chips}
            }

        # 9. Emit Done Event
        total_tokens = working_memory.count_tokens(req.message) + working_memory.count_tokens(complete_response)
        yield {
            "event": "done",
            "data": {
                "session_id": session_id,
                "total_tokens": total_tokens
            }
        }

        # 10. Record turn in Working Memory (Tier 1)
        working_memory.add_message_turn(session_id, "user", req.message)
        working_memory.add_message_turn(
            session_id,
            "assistant",
            complete_response,
            metadata={
                "action_card": action_card.model_dump() if action_card else None,
                "sources": sources,
                "intent": intent
            }
        )

chat_router = ChatRouter()

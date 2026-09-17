import re
from typing import List, Dict, Any, Optional
from app.memory.working_memory import working_memory
from app.memory.episodic_memory import episodic_memory_service
from app.models.database import SessionLocal
from app.core.logger import logger

class MemoryConsolidationWorker:
    """
    Background worker that distills working memory turns into permanent episodic facts,
    preferences, and session summaries.
    """
    def consolidate_session(self, session_id: str, user_id: str = "user-dev-01", tenant_id: str = "tenant-default") -> List[Dict[str, Any]]:
        context = working_memory.get_active_context(session_id)
        messages = context.get("messages", [])
        if not messages:
            logger.info(f"No messages to consolidate for session {session_id}")
            return []

        logger.info(f"Consolidating session {session_id} ({len(messages)} messages)...")
        extracted_facts = []

        # 1. Distill explicit user preferences
        user_texts = [m["content"] for m in messages if m.get("role") == "user"]
        combined_user_text = " ".join(user_texts)

        # Rule-based and semantic extractors
        # Example: "I primarily work on repo-analytics and prefer TypeScript"
        if "repo-" in combined_user_text or "repository" in combined_user_text:
            match = re.search(r'(work on|focus on|using|maintain|primary repo(sitory)? is)\s+(repo-[a-zA-Z0-9_-]+|[a-zA-Z0-9_-]+)', combined_user_text, re.IGNORECASE)
            if match:
                repo_name = match.group(3)
                fact = f"User primarily works on repository '{repo_name}'."
                extracted_facts.append(("preference", fact, 1.0))

        if any(w in combined_user_text.lower() for w in ["typescript", "python", "go", "java", "rust"]):
            for lang in ["typescript", "python", "golang", "go", "rust", "java", "c#"]:
                if lang in combined_user_text.lower():
                    fact = f"User prefers code examples and tooling in {lang.title()}."
                    extracted_facts.append(("preference", fact, 0.9))
                    break

        if "slack" in combined_user_text.lower() and ("notify" in combined_user_text.lower() or "alert" in combined_user_text.lower()):
            extracted_facts.append(("preference", "User prefers Slack notifications for build and security alerts.", 0.8))

        # 2. Distill session summary
        turn_count = len(messages)
        topics_covered = []
        for feat in ["branch protection", "preview environment", "rollback", "code reviewer", "security scan", "webhook", "telemetry", "pipeline"]:
            if any(feat in m["content"].lower() for m in messages):
                topics_covered.append(feat)

        if topics_covered:
            topics_str = ", ".join(topics_covered)
            summary_fact = f"In previous session, user explored {topics_str} and asked {turn_count // 2} technical questions."
            extracted_facts.append(("session_summary", summary_fact, 0.7))

        # 3. Store into Episodic Memory via DB session
        db = SessionLocal()
        saved = []
        try:
            for mem_type, fact_text, imp in extracted_facts:
                dto = episodic_memory_service.store_memory(
                    db=db,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    fact_text=fact_text,
                    memory_type=mem_type,
                    importance_score=imp,
                    source_session_id=session_id
                )
                saved.append(dto.model_dump())
        finally:
            db.close()

        logger.info(f"Consolidation complete for session {session_id}: distilled {len(saved)} memories.")
        return saved

consolidation_worker = MemoryConsolidationWorker()

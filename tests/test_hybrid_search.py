import pytest
from app.rag.hybrid_search import HybridSearchEngine

def test_hybrid_search_rrf():
    engine = HybridSearchEngine()
    docs = [
        {"id": "doc1", "title": "Branch Protection Rules", "text": "Configure required approvals, branch protection, and merge requirements for git branches."},
        {"id": "doc2", "title": "Slack Webhook Notifications", "text": "Set up incoming webhooks and Slack channel alerts for build failures and security alerts."},
        {"id": "doc3", "title": "Preview Environments", "text": "Ephemeral staging preview environments created for Pull Requests."},
        {"id": "doc4", "title": "Auto-Rollback Thresholds", "text": "Configure automated rollback thresholds and error rate triggers for deployments."}
    ]
    engine.index(docs, text_field="text")
    
    results = engine.search("Where can I configure Slack alerts?", top_k=2)
    assert len(results) >= 1
    assert results[0]["id"] == "doc2"
    assert "Slack" in results[0]["title"]

import pytest
from app.telemetry.agent_connectors import telemetry_service

def test_get_repo_telemetry():
    res = telemetry_service.get_repo_telemetry("repo-payments")
    assert res is not None
    assert res.health_score == 94
    assert res.active_branch == "main"
    assert "code_reviewer" in res.agents_summary
    assert len(res.recent_events) >= 1

def test_telemetry_summaries():
    all_sums = telemetry_service.get_all_summaries()
    assert len(all_sums) >= 3
    repo_ids = [s["repo_id"] for s in all_sums]
    assert "repo-payments" in repo_ids
    assert "core-backend" in repo_ids

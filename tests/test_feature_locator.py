import pytest
from app.rag.feature_registry import feature_registry_service

def test_locate_slack_webhooks():
    query = "Where do I configure Slack notifications for build failures?"
    res = feature_registry_service.search_features(query, top_k=2)
    assert res.best_match is not None
    assert res.best_match.id == "feat_webhooks_slack"
    assert "/settings/integrations/webhooks/slack" in res.best_match.route_pattern

def test_locate_branch_protection():
    query = "Where are branch rules and merge policies?"
    res = feature_registry_service.search_features(query, top_k=2)
    assert res.best_match is not None
    assert res.best_match.id == "feat_branch_protection"

def test_resolve_deep_link():
    feat = feature_registry_service.features[2]  # branch protection
    card = feature_registry_service.resolve_deep_link(feat, repo_id="repo-payments")
    assert card.route == "/repos/repo-payments/settings/branches"
    assert "repo-payments" in card.breadcrumbs
    assert card.action_label == "Go to Branch Protection Rules"

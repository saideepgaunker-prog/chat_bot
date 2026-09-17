import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_stream_sse_feature_locator():
    payload = {
        "session_id": "test-sse-sess-01",
        "user_id": "test-dev-01",
        "message": "Where can I set up Slack notifications?",
        "ambient_context": {
            "current_route": "/",
            "repo_id": "repo-payments"
        }
    }
    
    with client.stream("POST", "/api/v1/chat/message", json=payload) as response:
        assert response.status_code == 200
        events_received = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                events_received.append(line.replace("event:", "").strip())
        
        assert "metadata" in events_received
        assert "token" in events_received
        assert "action_card" in events_received
        assert "done" in events_received

def test_chat_stream_sse_telemetry():
    payload = {
        "session_id": "test-sse-sess-02",
        "user_id": "test-dev-01",
        "message": "Give me a status update on repo-payments",
        "ambient_context": {
            "current_route": "/repos/repo-payments",
            "repo_id": "repo-payments"
        }
    }
    
    with client.stream("POST", "/api/v1/chat/message", json=payload) as response:
        assert response.status_code == 200
        events_received = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                events_received.append(line.replace("event:", "").strip())
        
        assert "metadata" in events_received
        assert "token" in events_received
        assert "action_card" in events_received
        assert "done" in events_received

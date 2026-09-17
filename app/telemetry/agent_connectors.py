import os
import json
from typing import Dict, Any, List, Optional
from app.schemas.telemetry import RepoTelemetry, AgentEvent
from app.core.logger import logger

class MultiAgentTelemetryService:
    """
    Connects to and aggregates telemetry from Control Tower background AI agents:
    - Code Reviewer Agent
    - CI/CD Orchestrator Agent
    - Security Scanner Agent
    - Release Summarizer Agent
    """
    def __init__(self, data_path: str = "app/data/sample_telemetry.json"):
        self.data_path = data_path
        self._data: Dict[str, Any] = {}
        self.load_telemetry()

    def load_telemetry(self):
        if not os.path.exists(self.data_path):
            logger.warning(f"Telemetry file not found at {self.data_path}")
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info(f"Loaded telemetry for {len(self._data)} repositories.")
        except Exception as e:
            logger.error(f"Failed to load telemetry data: {e}")

    def get_repo_telemetry(self, repo_id: str) -> Optional[RepoTelemetry]:
        raw = self._data.get(repo_id)
        if not raw:
            # Check partial match
            for k, v in self._data.items():
                if repo_id.lower() in k.lower():
                    raw = v
                    break
        
        if not raw:
            return None

        events = [AgentEvent(**ev) for ev in raw.get("recent_events", [])]
        return RepoTelemetry(
            repo_id=raw["repo_id"],
            name=raw["name"],
            health_score=raw["health_score"],
            active_branch=raw["active_branch"],
            last_deployment=raw.get("last_deployment"),
            agents_summary=raw.get("agents_summary", {}),
            recent_events=events
        )

    def list_all_repos(self) -> List[str]:
        return list(self._data.keys())

    def get_all_summaries(self) -> List[Dict[str, Any]]:
        summaries = []
        for repo_id, data in self._data.items():
            summaries.append({
                "repo_id": repo_id,
                "name": data["name"],
                "health_score": data["health_score"],
                "active_branch": data["active_branch"],
                "agents_status": {k: v.get("status") for k, v in data.get("agents_summary", {}).items()}
            })
        return summaries

telemetry_service = MultiAgentTelemetryService()

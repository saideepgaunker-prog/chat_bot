from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import datetime

class AgentEvent(BaseModel):
    id: str
    repo_id: str
    agent_type: str  # code_reviewer, ci_cd_orchestrator, security_scanner, release_summarizer
    status: str      # success, warning, failed, in_progress, idle
    summary: str
    details: Optional[str] = None
    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    timestamp: str

class RepoTelemetry(BaseModel):
    repo_id: str
    name: str
    health_score: int
    active_branch: str
    last_deployment: Optional[str] = None
    agents_summary: Dict[str, Any]
    recent_events: List[AgentEvent] = []

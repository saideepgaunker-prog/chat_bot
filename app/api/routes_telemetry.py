from fastapi import APIRouter, HTTPException
from app.schemas.telemetry import RepoTelemetry
from app.telemetry.agent_connectors import telemetry_service

router = APIRouter(prefix="/telemetry", tags=["Multi-Agent Telemetry"])

@router.get("/projects")
async def list_project_telemetry():
    """Get all repository health scores and agent statuses."""
    return telemetry_service.get_all_summaries()

@router.get("/projects/{repo_id}", response_model=RepoTelemetry)
async def get_repo_telemetry(repo_id: str):
    """Get deep telemetry and recent events from background agents for a repository."""
    res = telemetry_service.get_repo_telemetry(repo_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found in telemetry store")
    return res

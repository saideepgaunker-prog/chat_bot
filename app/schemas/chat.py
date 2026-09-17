from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import datetime

class AmbientContext(BaseModel):
    current_route: str = "/"
    repo_id: Optional[str] = None
    active_branch: Optional[str] = "main"
    user_role: Optional[str] = "developer"
    active_file: Optional[str] = None

class ActionCard(BaseModel):
    type: str = "navigation"  # navigation, action_button, metric_summary, status_card
    title: str
    route: Optional[str] = None
    breadcrumbs: List[str] = []
    action_label: Optional[str] = "Open Feature"
    deep_link_params: Dict[str, Any] = {}
    status: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = "user-dev-01"
    tenant_id: Optional[str] = "tenant-default"
    message: str
    ambient_context: Optional[AmbientContext] = Field(default_factory=AmbientContext)
    active_attachments: Optional[List[str]] = []

class ChatMessageDto(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    metadata: Dict[str, Any] = {}
    created_at: datetime.datetime

class ChatSessionDto(BaseModel):
    id: str
    user_id: str
    tenant_id: str
    title: str
    active_route: str
    active_repo: Optional[str] = None
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    message_count: Optional[int] = 0

class StreamEvent(BaseModel):
    event: str
    data: Dict[str, Any]

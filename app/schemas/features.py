from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class FeatureDto(BaseModel):
    id: str
    name: str
    route_pattern: str
    description: str
    keywords: List[str] = []
    category: str = "general"
    permission_required: str = "developer"
    breadcrumbs: List[str] = []

class FeatureSearchResponse(BaseModel):
    query: str
    total_matches: int
    best_match: Optional[FeatureDto] = None
    matches: List[FeatureDto] = []

class FeatureExplainerRequest(BaseModel):
    route: str
    repo_id: Optional[str] = None
    question: Optional[str] = None

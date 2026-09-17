from typing import List
from fastapi import APIRouter, Query
from app.schemas.features import FeatureDto, FeatureSearchResponse, FeatureExplainerRequest
from app.rag.feature_registry import feature_registry_service
from app.rag.document_store import document_store

router = APIRouter(prefix="/features", tags=["Features & Navigation"])

@router.get("/search", response_model=FeatureSearchResponse)
async def search_features(q: str = Query(..., description="Natural language feature query")):
    """Search platform features using Hybrid RAG."""
    return feature_registry_service.search_features(q, top_k=4)

@router.get("/all", response_model=List[FeatureDto])
async def get_all_features():
    """Return all indexed features."""
    return [FeatureDto(**f) for f in feature_registry_service.features]

@router.post("/explain")
async def explain_feature(req: FeatureExplainerRequest):
    """In-situ feature explainer based on active route and question."""
    matched_feat = feature_registry_service.find_by_route(req.route)
    doc_results = document_store.search_docs(req.question or (matched_feat.get("name") if matched_feat else req.route), top_k=2)
    
    return {
        "route": req.route,
        "feature": matched_feat,
        "documentation": doc_results
    }

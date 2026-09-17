import os
import json
from typing import List, Dict, Any, Optional
from app.rag.hybrid_search import HybridSearchEngine
from app.schemas.features import FeatureDto, FeatureSearchResponse
from app.schemas.chat import ActionCard
from app.core.logger import logger

class FeatureRegistryService:
    def __init__(self, data_path: str = "app/data/feature_registry.json"):
        self.data_path = data_path
        self.features: List[Dict[str, Any]] = []
        self.search_engine = HybridSearchEngine()
        self.load_and_index()

    def load_and_index(self):
        if not os.path.exists(self.data_path):
            logger.warning(f"Feature registry file not found at {self.data_path}")
            return
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.features = json.load(f)
            
            # Prepare searchable text for each feature
            indexed_docs = []
            for item in self.features:
                keywords_str = " ".join(item.get("keywords", []))
                breadcrumbs_str = " > ".join(item.get("breadcrumbs", []))
                searchable_text = f"{item['name']} {item['description']} {keywords_str} {breadcrumbs_str} {item.get('category', '')}"
                doc = dict(item)
                doc["text"] = searchable_text
                indexed_docs.append(doc)

            self.search_engine.index(indexed_docs, text_field="text")
            logger.info(f"Loaded and indexed {len(self.features)} features in FeatureRegistry.")
        except Exception as e:
            logger.error(f"Error loading feature registry: {e}")

    def search_features(self, query: str, top_k: int = 4) -> FeatureSearchResponse:
        matches = self.search_engine.search(query, top_k=top_k)
        feature_dtos = []
        for m in matches:
            feature_dtos.append(FeatureDto(
                id=m["id"],
                name=m["name"],
                route_pattern=m["route_pattern"],
                description=m["description"],
                keywords=m.get("keywords", []),
                category=m.get("category", "general"),
                permission_required=m.get("permission_required", "developer"),
                breadcrumbs=m.get("breadcrumbs", [])
            ))

        best = feature_dtos[0] if feature_dtos else None
        return FeatureSearchResponse(
            query=query,
            total_matches=len(feature_dtos),
            best_match=best,
            matches=feature_dtos
        )

    def find_by_route(self, route: str) -> Optional[Dict[str, Any]]:
        """Match an active route string against feature route patterns."""
        for feat in self.features:
            pattern = feat["route_pattern"]
            # Convert /repos/:repoId/settings/branches to regex
            regex_pat = "^" + pattern.replace(":repoId", "[^/]+") + "$"
            import re
            if re.match(regex_pat, route):
                return feat
            if pattern == route:
                return feat
        return None

    def resolve_deep_link(self, feature: Dict[str, Any], repo_id: Optional[str] = None) -> ActionCard:
        route_pattern = feature["route_pattern"]
        resolved_route = route_pattern
        target_repo = repo_id or "repo-payments"
        
        if ":repoId" in route_pattern:
            resolved_route = route_pattern.replace(":repoId", target_repo)

        resolved_breadcrumbs = [
            b.replace(":repoId", target_repo) for b in feature.get("breadcrumbs", [])
        ]

        return ActionCard(
            type="navigation",
            title=feature["name"],
            route=resolved_route,
            breadcrumbs=resolved_breadcrumbs,
            action_label=f"Go to {feature['name']}",
            deep_link_params={"repo_id": target_repo, "feature_id": feature["id"]},
            status="active"
        )

feature_registry_service = FeatureRegistryService()

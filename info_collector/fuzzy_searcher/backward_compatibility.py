from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence
from fuzzy_searcher.service import OccupationService

class FuzzySearcher:
    def __init__(
        self,
        config_path: str = "config.json"
    ):
        self.service = OccupationService(
            config_path
        )

    def search(
        self,
        query: str,
        threshold: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        result = self.service.resolve(
            query,
            threshold,
            limit
        )

        if not result.get("standardized"):
            return []

        primary = {
            "preferred_label": result["standardized"],
            "uri": result["uri"],
            "isco_code": result["isco_code"],
            "definition": result["definition"],
            "similarity": result["similarity"],
            "confidence": result["confidence"],
            "status": result["status"],
            "match_type": result["match_type"],
            "matched_field": result["matched_field"],
            "matched_text": result["matched_text"],
            "weighted_score": result.get(
                "similarity",
                0.0
            )
        }

        return [
            primary,
            *result.get(
                "alternatives",
                []
            )
        ]

    def standardize(
        self,
        query: str,
        threshold: Optional[float] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.service.resolve(
            query,
            threshold,
            limit
        )

    def resolve_many(
        self,
        queries: Sequence[str],
        threshold: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self.service.resolve_many(
            queries,
            threshold,
            limit
        )

    def close(self) -> None:
        self.service.close()

    def __enter__(self) -> "FuzzySearcher":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ) -> None:
        self.close()
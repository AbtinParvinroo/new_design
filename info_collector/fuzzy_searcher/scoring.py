from __future__ import annotations
from config import ConfigManager
from rapidfuzz import fuzz, process

class ScorerRegistry:
    scorers = {
        "ratio": fuzz.ratio,
        "partial_ratio": fuzz.partial_ratio,
        "token_sort_ratio": fuzz.token_sort_ratio,
        "token_set_ratio": fuzz.token_set_ratio,
        "WRatio": fuzz.WRatio
    }

    def __init__(
        self,
        config: ConfigManager
    ):
        scorer_name = str(
            config.fuzzy().get(
                "scorer",
                "WRatio"
            )
        )

        self.scorer = self.scorers.get(
            scorer_name,
            fuzz.WRatio
        )

    def score(
        self,
        query: str,
        candidate: str
    ) -> float:
        if not query or not candidate:
            return 0.0

        return float(
            self.scorer(
                query,
                candidate
            )
        )
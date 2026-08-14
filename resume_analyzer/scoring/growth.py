from __future__ import annotations
from resume_analyzer.models.output_models import RawMetrics
from resume_analyzer.core.config import ResumeAnalyzerConfig
from resume_analyzer.core.utils import normalize_score

def calculate_growth_score(raw: RawMetrics, config: ResumeAnalyzerConfig) -> float:
    growth_score = (
        min(raw.promotion_count * config.growth_promotion_multiplier, config.max_score) * config.growth_promotion_weight
        + (raw.level_progression.growth / config.growth_level_divisor * config.max_score) * config.growth_level_weight
    )
    return normalize_score(growth_score, config)
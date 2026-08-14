from __future__ import annotations
from resume_analyzer.models.output_models import RawMetrics
from resume_analyzer.core.config import ResumeAnalyzerConfig
from resume_analyzer.core.utils import normalize_score

def calculate_seniority_score(raw: RawMetrics, config: ResumeAnalyzerConfig) -> float:
    seniority_score = (
        min((raw.total_experience_years or 0) * config.seniority_exp_multiplier, config.max_score) * config.seniority_weights[0]
        + min(raw.promotion_count * config.seniority_promotion_multiplier, config.max_score) * config.seniority_weights[1]
        + (raw.level_progression.growth / config.growth_level_divisor * config.max_score) * config.seniority_weights[2]
    )
    return normalize_score(seniority_score, config)
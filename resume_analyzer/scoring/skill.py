from __future__ import annotations
from resume_analyzer.models.output_models import RawMetrics
from resume_analyzer.core.config import ResumeAnalyzerConfig
from resume_analyzer.core.utils import normalize_score

def calculate_skill_score(raw: RawMetrics, config: ResumeAnalyzerConfig) -> float:
    if raw.total_experience_years:
        skill_growth_score = (raw.skill_event_count / raw.total_experience_years) * config.skill_velocity_multiplier
    else:
        skill_growth_score = 0.0
    return normalize_score(skill_growth_score, config)
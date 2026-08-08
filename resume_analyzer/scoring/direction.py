from __future__ import annotations
from models.domain_models import JobInterval
from core.config import ResumeAnalyzerConfig
from core.utils import normalize_score

def calculate_direction_score(jobs: list[JobInterval], config: ResumeAnalyzerConfig) -> float:
    titles = [job.event.title for job in jobs if job.event.title]
    if len(titles) > 1:
        direction_score = config.max_score - ((len(set(titles)) / len(titles)) * config.direction_unique_ratio_multiplier)
    else:
        direction_score = config.max_score
    return normalize_score(direction_score, config)
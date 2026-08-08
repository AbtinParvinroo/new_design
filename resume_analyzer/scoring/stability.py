from __future__ import annotations
from models.output_models import RawMetrics
from core.config import ResumeAnalyzerConfig
from core.utils import normalize_score

def calculate_stability_score(raw: RawMetrics, config: ResumeAnalyzerConfig) -> float:
    if raw.num_jobs == 0:
        return 0.0
    stability_score = config.max_score - min(raw.employment_gap_months, config.max_score)
    return normalize_score(stability_score, config)
from __future__ import annotations
from resume_analyzer.models.output_models import RawMetrics
from resume_analyzer.core.config import ResumeAnalyzerConfig
from resume_analyzer.core.utils import normalize_score

def calculate_stability_score(raw: RawMetrics, config: ResumeAnalyzerConfig) -> float:
    if raw.num_jobs == 0:
        return 0.0

    stability_score = config.max_score - min(raw.employment_gap_months, config.max_score)
    return normalize_score(stability_score, config)
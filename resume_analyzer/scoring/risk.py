from __future__ import annotations
from resume_analyzer.models.output_models import RawMetrics
from resume_analyzer.core.config import ResumeAnalyzerConfig

def calculate_risk_score(raw: RawMetrics, stability_score: float, skill_score: float, config: ResumeAnalyzerConfig) -> float:
    risk = 0.0
    if raw.employment_gap_months > config.risk_gap_threshold_months:
        risk += config.risk_gap_penalty
    if raw.demotion_count > 0:
        risk += config.risk_demotion_penalty
    if stability_score < config.risk_stability_threshold:
        risk += config.risk_stability_penalty
    if skill_score < config.risk_skill_threshold:
        risk += config.risk_skill_penalty
    return min(risk, config.max_score)
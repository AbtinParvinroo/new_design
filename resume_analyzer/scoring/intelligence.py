from __future__ import annotations
from models.output_models import RawMetrics, CareerIntelligence
from models.domain_models import JobInterval
from core.config import ResumeAnalyzerConfig
from .growth import calculate_growth_score
from .stability import calculate_stability_score
from .skill import calculate_skill_score
from .direction import calculate_direction_score
from .seniority import calculate_seniority_score
from .momentum import calculate_momentum_score
from .risk import calculate_risk_score

def build_career_intelligence(raw: RawMetrics, jobs: list[JobInterval], config: ResumeAnalyzerConfig) -> CareerIntelligence:
    growth_score = calculate_growth_score(raw, config)
    stability_score = calculate_stability_score(raw, config)
    skill_score = calculate_skill_score(raw, config)
    direction_score = calculate_direction_score(jobs, config)
    seniority_score = calculate_seniority_score(raw, config)
    momentum_score = calculate_momentum_score(growth_score, skill_score, seniority_score, config)
    risk_score = calculate_risk_score(raw, stability_score, skill_score, config)

    learning_velocity = raw.skill_event_count / raw.total_experience_years if raw.total_experience_years else 0.0

    return CareerIntelligence(
        career_growth_score=round(growth_score, 2),
        stability_score=round(stability_score, 2),
        skill_growth_score=round(skill_score, 2),
        career_direction_score=round(direction_score, 2),
        learning_velocity=round(learning_velocity, 2),
        seniority_confidence_score=round(seniority_score, 2),
        career_momentum_score=round(momentum_score, 2),
        career_risk_score=round(risk_score, 2)
    )
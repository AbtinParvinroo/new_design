from __future__ import annotations
from resume_analyzer.core.config import ResumeAnalyzerConfig
from resume_analyzer.core.utils import normalize_score

def calculate_momentum_score(growth_score: float, skill_score: float, seniority_score: float, config: ResumeAnalyzerConfig) -> float:
    momentum_score = (growth_score * config.momentum_weights[0]) + (skill_score * config.momentum_weights[1]) + (seniority_score * config.momentum_weights[2])
    return normalize_score(momentum_score, config)
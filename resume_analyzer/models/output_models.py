from __future__ import annotations
from typing import Optional
from pydantic import BaseModel

class LevelProgression(BaseModel):
    first_level: Optional[int]
    current_level: Optional[int]
    growth: int

class RawMetrics(BaseModel):
    total_experience_years: Optional[float]
    num_jobs: int
    avg_duration_months: Optional[float]
    min_duration_months: Optional[float]
    max_duration_months: Optional[float]
    stability_index: Optional[float]
    unique_role_count: int
    role_variety_ratio: Optional[float]
    promotion_count: int
    demotion_count: int
    employment_gap_months: float
    skill_event_count: int
    trend_slope: Optional[float]
    career_correlation: Optional[float]
    level_progression: LevelProgression

class CareerIntelligence(BaseModel):
    career_growth_score: float
    stability_score: float
    skill_growth_score: float
    career_direction_score: float
    learning_velocity: float
    seniority_confidence_score: float
    career_momentum_score: float
    career_risk_score: float

class CareerInterpretation(BaseModel):
    growth: str
    stability: str
    momentum: str
    risk: str

class ResumeAnalysisResult(BaseModel):
    raw_metrics: RawMetrics
    career_intelligence: CareerIntelligence
    interpretation: CareerInterpretation
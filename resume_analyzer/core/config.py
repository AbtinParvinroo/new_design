from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class ResumeAnalyzerConfig:
    max_input_size: int = 10 * 1024 * 1024
    days_per_month: float = 30.44
    formula_version: str = "1.0.0"
    work_types: set[str] = field(default_factory=lambda: {"work", "internship"})
    academic_types: set[str] = field(default_factory=lambda: {"education", "certificate", "project", "skill"})
    level_rank: dict[str, int] = field(
        default_factory=lambda: {
            "junior": 1, "mid": 2, "senior": 3, "lead": 4,
            "manager": 5, "director": 6, "vp": 7, "c-level": 8
        }
    )
    max_score: float = 100.0
    min_score: float = 0.0
    growth_promotion_multiplier: float = 25.0
    growth_level_divisor: float = 7.0
    growth_promotion_weight: float = 0.5
    growth_level_weight: float = 0.5
    skill_velocity_multiplier: float = 25.0
    direction_unique_ratio_multiplier: float = 40.0
    seniority_exp_multiplier: float = 8.0
    seniority_promotion_multiplier: float = 20.0
    seniority_weights: tuple[float, float, float] = (0.4, 0.3, 0.3)
    risk_gap_threshold_months: float = 12.0
    risk_gap_penalty: float = 30.0
    risk_demotion_penalty: float = 20.0
    risk_stability_threshold: float = 50.0
    risk_stability_penalty: float = 25.0
    risk_skill_threshold: float = 40.0
    risk_skill_penalty: float = 25.0
    momentum_weights: tuple[float, float, float] = (0.5, 0.3, 0.2)
    interp_growth_high: float = 75.0
    interp_growth_mid: float = 40.0
    interp_stability_high: float = 80.0
    interp_stability_mid: float = 50.0
    interp_momentum_high: float = 75.0
    interp_momentum_mid: float = 45.0
    interp_risk_low: float = 30.0
    interp_risk_mid: float = 60.0
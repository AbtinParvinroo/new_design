from __future__ import annotations
from models.output_models import CareerIntelligence, CareerInterpretation
from core.config import ResumeAnalyzerConfig

def generate_interpretation(intel: CareerIntelligence, config: ResumeAnalyzerConfig) -> CareerInterpretation:
    growth = (
        "Strong upward career progression"
        if intel.career_growth_score >= config.interp_growth_high
        else "Moderate career progression"
        if intel.career_growth_score >= config.interp_growth_mid
        else "Limited visible progression"
    )
    stability = (
        "Stable employment history"
        if intel.stability_score >= config.interp_stability_high
        else "Moderate employment stability"
        if intel.stability_score >= config.interp_stability_mid
        else "Frequent transitions detected"
    )
    momentum = (
        "Career trajectory is accelerating"
        if intel.career_momentum_score >= config.interp_momentum_high
        else "Career trajectory is steady"
        if intel.career_momentum_score >= config.interp_momentum_mid
        else "Career growth momentum is weak"
    )
    risk = (
        "Low career risk"
        if intel.career_risk_score < config.interp_risk_low
        else "Moderate career risk"
        if intel.career_risk_score < config.interp_risk_mid
        else "High career risk"
    )
    return CareerInterpretation(growth=growth, stability=stability, momentum=momentum, risk=risk)
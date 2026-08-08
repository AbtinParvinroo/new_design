from typing import Optional
from .config import ResumeAnalyzerConfig

def normalize_score(value: Optional[float], config: ResumeAnalyzerConfig) -> float:
    if value is None:
        return config.min_score
    return max(config.min_score, min(config.max_score, value))
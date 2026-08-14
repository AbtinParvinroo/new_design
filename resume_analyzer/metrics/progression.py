from __future__ import annotations
from resume_analyzer.models.domain_models import JobInterval
from resume_analyzer.models.output_models import LevelProgression
from resume_analyzer.core.config import ResumeAnalyzerConfig

def calculate_level_progression(jobs: list[JobInterval], config: ResumeAnalyzerConfig) -> LevelProgression:
    levels = [config.level_rank[job.event.level] for job in jobs if job.event.level in config.level_rank]
    if not levels:
        return LevelProgression(first_level=None, current_level=None, growth=0)

    return LevelProgression(first_level=levels[0], current_level=levels[-1], growth=levels[-1] - levels[0])
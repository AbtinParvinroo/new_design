from __future__ import annotations
from typing import Optional
import logging
from resume_analyzer.core.config import ResumeAnalyzerConfig
from resume_analyzer.models.input_models import ResumeInput
from resume_analyzer.models.domain_models import JobInterval
from resume_analyzer.models.output_models import ResumeAnalysisResult
from resume_analyzer.metrics.duration import parse_date, calculate_duration
from resume_analyzer.metrics.intervals import merge_intervals
from resume_analyzer.metrics.raw_metrics import calculate_raw_metrics
from resume_analyzer.scoring.intelligence import build_career_intelligence
from resume_analyzer.interpretation.interpreter import generate_interpretation

logger = logging.getLogger(__name__)

class ResumeAnalyzer:
    def __init__(self, config: Optional[ResumeAnalyzerConfig] = None):
        self.config = config or ResumeAnalyzerConfig()

    def analyze(self, resume: ResumeInput) -> ResumeAnalysisResult:
        work_events = [e for e in resume.events if e.type in self.config.work_types]
        academic_events = [e for e in resume.events if e.type in self.config.academic_types]

        jobs: list[JobInterval] = []
        for event in work_events:
            start_date = parse_date(event.start_date)
            end_date = parse_date(event.end_date)
            duration = calculate_duration(start_date, end_date, self.config)
            if duration is not None:
                jobs.append(JobInterval(
                    event=event,
                    start_date=start_date,  # type: ignore
                    end_date=end_date,
                    duration_months=duration
                ))

        jobs = merge_intervals(jobs, self.config)
        raw_metrics = calculate_raw_metrics(jobs, academic_events, self.config)
        intelligence = build_career_intelligence(raw_metrics, jobs, self.config)
        interpretation = generate_interpretation(intelligence, self.config)

        return ResumeAnalysisResult(
            raw_metrics=raw_metrics,
            career_intelligence=intelligence,
            interpretation=interpretation
        )
from __future__ import annotations
from datetime import datetime, timezone
from typing import list
from models.domain_models import JobInterval
from .duration import calculate_duration
from core.config import ResumeAnalyzerConfig

def merge_intervals(jobs: list[JobInterval], config: ResumeAnalyzerConfig) -> list[JobInterval]:
    if not jobs:
        return []
    ordered = sorted(jobs, key=lambda job: job.start_date)
    merged: list[JobInterval] = [ordered[0]]
    for current in ordered[1:]:
        previous = merged[-1]
        previous_end = previous.end_date or datetime.now(previous.start_date.tzinfo or timezone.utc)
        current_end = current.end_date or datetime.now(current.start_date.tzinfo or timezone.utc)
        if current.start_date <= previous_end:
            if current_end > previous_end:
                merged[-1] = JobInterval(
                    event=previous.event,
                    start_date=previous.start_date,
                    end_date=current.end_date,
                    duration_months=calculate_duration(previous.start_date, current.end_date, config) or previous.duration_months
                )
        else:
            merged.append(current)
    return merged

def calculate_job_gaps(jobs: list[JobInterval], config: ResumeAnalyzerConfig) -> list[float]:
    if len(jobs) < 2:
        return []
    ordered = sorted(jobs, key=lambda job: job.start_date)
    gaps: list[float] = []
    for index in range(len(ordered) - 1):
        current, next_job = ordered[index], ordered[index + 1]
        current_end = current.end_date or datetime.now(current.start_date.tzinfo or timezone.utc)
        gap_days = (next_job.start_date - current_end).days
        if gap_days > 0:
            gaps.append(gap_days / config.days_per_month)
    return gaps
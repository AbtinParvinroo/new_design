from __future__ import annotations
from statistics import mean, stdev
from resume_analyzer.models.domain_models import JobInterval
from resume_analyzer.models.input_models import ResumeEvent
from resume_analyzer.models.output_models import RawMetrics
from resume_analyzer.core.config import ResumeAnalyzerConfig
from resume_analyzer.metrics.duration import calculate_duration
from resume_analyzer.metrics.intervals import calculate_job_gaps
from resume_analyzer.metrics.statistics import linear_regression_slope, pearson_correlation
from resume_analyzer.metrics.progression import calculate_level_progression

def calculate_raw_metrics(jobs: list[JobInterval], academic_events: list[ResumeEvent], config: ResumeAnalyzerConfig) -> RawMetrics:
    durations = [job.duration_months for job in jobs]
    total_months = sum(durations)
    stability_index = None
    if len(durations) >= 3 and stdev(durations) > 0:
        stability_index = mean(durations) / stdev(durations)
    
    promotion_count, demotion_count, previous_level = 0, 0, None
    for job in jobs:
        current_level = config.level_rank.get(job.event.level or "")
        if current_level is None:
            continue
        if previous_level is not None:
            if current_level > previous_level:
                promotion_count += 1
            elif current_level < previous_level:
                demotion_count += 1
        previous_level = current_level

    unique_titles = {job.event.title for job in jobs if job.event.title}
    start_years = [float(job.start_date.year) for job in jobs]
    gaps = calculate_job_gaps(jobs, config)
    level_prog = calculate_level_progression(jobs, config)

    return RawMetrics(
        total_experience_years=total_months / 12 if total_months else None,
        num_jobs=len(jobs),
        avg_duration_months=mean(durations) if durations else None,
        min_duration_months=min(durations) if durations else None,
        max_duration_months=max(durations) if durations else None,
        stability_index=stability_index,
        unique_role_count=len(unique_titles),
        role_variety_ratio=(len(unique_titles) / len(jobs)) if jobs else None,
        promotion_count=promotion_count,
        demotion_count=demotion_count,
        employment_gap_months=sum(gaps) if gaps else 0.0,
        skill_event_count=sum(1 for e in academic_events if e.type == "skill"),
        trend_slope=linear_regression_slope(start_years, durations),
        career_correlation=pearson_correlation(start_years, durations),
        level_progression=level_prog
    )
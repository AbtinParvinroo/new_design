from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional
from dateutil import parser as date_parser
from core.config import ResumeAnalyzerConfig
from core.exceptions import DateParsingError

logger = logging.getLogger(__name__)

def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = date_parser.parse(value)
    except Exception:
        return None
    now = datetime.now(parsed.tzinfo or timezone.utc)
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if parsed > now:
        return None
    return parsed

def calculate_duration(start_date: Optional[datetime], end_date: Optional[datetime], config: ResumeAnalyzerConfig) -> Optional[float]:
    if start_date is None:
        return None
    actual_end_date = end_date or datetime.now(start_date.tzinfo or timezone.utc)
    days = (actual_end_date - start_date).days
    if days < 0:
        return None
    return days / config.days_per_month
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .input_models import ResumeEvent
from typing import Optional

@dataclass(slots=True)
class JobInterval:
    event: ResumeEvent
    start_date: datetime
    end_date: Optional[datetime]
    duration_months: float
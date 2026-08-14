from __future__ import annotations
from typing import Any, Optional
import math

def parse_duration(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        duration = float(value)

    except (TypeError, ValueError):
        return None

    if not math.isfinite(duration):
        return None

    if duration < 0:
        return None

    return duration
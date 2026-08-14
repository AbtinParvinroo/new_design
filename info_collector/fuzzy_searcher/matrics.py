from __future__ import annotations
from typing import Any, Dict, Optional
from collections import defaultdict

class MetricsTracker:
    def __init__(self, latency_sample_size: int = 10000):
        self.counters: Dict[str, int] = defaultdict(int)
        self.latency_sample_size = max(100, latency_sample_size)
        self.latency_count = 0
        self.latency_total_ms = 0.0
        self.latency_min_ms: Optional[float] = None
        self.latency_max_ms: Optional[float] = None

    def increment(self, metric: str, count: int = 1) -> None:
        self.counters[metric] += count

    def record_latency(self, latency_ms: float) -> None:
        latency_ms = max(0.0, float(latency_ms))
        self.latency_count += 1
        self.latency_total_ms += latency_ms

        if self.latency_min_ms is None or latency_ms < self.latency_min_ms:
            self.latency_min_ms = latency_ms

        if self.latency_max_ms is None or latency_ms > self.latency_max_ms:
            self.latency_max_ms = latency_ms

    def get_metrics(self) -> Dict[str, Any]:
        average = (
            self.latency_total_ms / self.latency_count
            if self.latency_count
            else 0.0
        )

        return {
            "counters": dict(self.counters),
            "latency_ms_avg": round(average, 2),
            "latency_ms_min": round(self.latency_min_ms, 2) if self.latency_min_ms is not None else 0.0,
            "latency_ms_max": round(self.latency_max_ms, 2) if self.latency_max_ms is not None else 0.0,
            "total_requests": self.latency_count
        }
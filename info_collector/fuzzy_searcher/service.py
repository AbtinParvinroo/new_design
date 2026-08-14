from __future__ import annotations
from fuzzy_searcher.repository import OccupationRepository, PostgreSQLOccupationRepository
from fuzzy_searcher.config import ConfigManager, LoggerFactory
from typing import Any, Dict, List, Optional, Sequence, Tuple
from fuzzy_searcher.normalization import OccupationNormalizer
from fuzzy_searcher.resolver import OccupationResolver
from fuzzy_searcher.validation import InputValidator
from fuzzy_searcher.service import OccupationService
from fuzzy_searcher.matrics import MetricsTracker
from fuzzy_searcher.cache import OccupationCache
from fuzzy_searcher.index import OccupationIndex
import time

class OccupationService:
    def __init__(
        self,
        config_path: str = "config.json",
        repository: Optional[OccupationRepository] = None
    ):
        self.config = ConfigManager(
            config_path
        )

        self.logger = LoggerFactory.create(
            self.config
        )

        metrics_config = self.config.get(
            "metrics",
            default={}
        )

        self.metrics = MetricsTracker(
            latency_sample_size=int(
                metrics_config.get(
                    "latency_sample_size",
                    10000
                )
            )
        )

        self.validator = InputValidator(
            self.config
        )

        self.normalizer = OccupationNormalizer(
            self.config
        )

        self.repository = (
            repository
            or PostgreSQLOccupationRepository(
                self.config,
                self.logger
            )
        )

        self.cache = OccupationCache(
            self.config,
            self.logger
        )

        records = self.repository.fetch_all()

        index = OccupationIndex(
            records,
            self.normalizer
        )

        self.resolver = OccupationResolver(
            self.normalizer,
            self.validator,
            index,
            self.config,
            self.metrics
        )

    def _get_threshold_limit(
        self,
        threshold: Optional[float],
        limit: Optional[int]
    ) -> Tuple[float, int]:
        fuzzy_config = self.config.fuzzy()

        threshold_value = float(
            threshold
            if threshold is not None
            else fuzzy_config.get(
                "threshold",
                70
            )
        )

        if not 0 <= threshold_value <= 100:
            raise ValueError(
                "Runtime threshold must be between 0 and 100"
            )

        limit_value = int(
            limit
            if limit is not None
            else fuzzy_config.get(
                "limit",
                5
            )
        )

        if limit_value < 1:
            raise ValueError(
                "Runtime limit must be greater than zero"
            )

        limit_value = min(
            limit_value,
            100
        )

        return (
            threshold_value,
            limit_value
        )

    def resolve(
        self,
        raw_title: str,
        threshold: Optional[float] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        try:
            threshold_value, limit_value = (
                self._get_threshold_limit(
                    threshold,
                    limit
                )
            )

            validated = self.validator.validate(
                raw_title
            )

            if not validated:
                result = self.resolver.resolve(
                    raw_title,
                    threshold_value,
                    limit_value
                ).to_dict()

                return result

            normalized = self.normalizer.normalize(
                validated
            )

            if not normalized:
                result = self.resolver.resolve(
                    raw_title,
                    threshold_value,
                    limit_value
                ).to_dict()

                return result

            cached = self.cache.get(
                normalized,
                threshold_value,
                limit_value
            )

            if cached is not None:
                self.metrics.increment(
                    "cache_hit"
                )

                return cached

            self.metrics.increment(
                "cache_miss"
            )

            result = self.resolver.resolve(
                validated,
                threshold_value,
                limit_value
            ).to_dict()

            self.cache.set(
                normalized,
                threshold_value,
                limit_value,
                result
            )

            return result

        finally:
            self.metrics.record_latency(
                (time.perf_counter() - start_time)
                * 1000
            )

    def resolve_many(
        self,
        titles: Sequence[str],
        threshold: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        start_time = time.perf_counter()

        try:
            threshold_value, limit_value = (
                self._get_threshold_limit(
                    threshold,
                    limit
                )
            )

            normalized_to_raw: Dict[
                str,
                str
            ] = {}

            normalized_order: List[str] = []

            raw_validity: List[
                Tuple[str, str]
            ] = []

            for raw_title in titles:
                validated = self.validator.validate(
                    raw_title
                )

                if not validated:
                    raw_validity.append(
                        (
                            raw_title,
                            ""
                        )
                    )

                    continue

                normalized = self.normalizer.normalize(
                    validated
                )

                if not normalized:
                    raw_validity.append(
                        (
                            raw_title,
                            ""
                        )
                    )

                    continue

                raw_validity.append(
                    (
                        raw_title,
                        normalized
                    )
                )

                if normalized not in normalized_to_raw:
                    normalized_to_raw[
                        normalized
                    ] = validated

                    normalized_order.append(
                        normalized
                    )

            if not normalized_order:
                return [
                    self.resolver.resolve(
                        raw_title,
                        threshold_value,
                        limit_value
                    ).to_dict()
                    for raw_title, _ in raw_validity
                ]

            keys = [
                self.cache.build_key(
                    normalized,
                    threshold_value,
                    limit_value
                )
                for normalized in normalized_order
            ]

            cached_results = self.cache.mget(
                keys
            )

            resolved_by_normalized: Dict[
                str,
                Dict[str, Any]
            ] = {}

            to_cache = []

            for normalized, cached in zip(
                normalized_order,
                cached_results
            ):
                if cached is not None:
                    self.metrics.increment(
                        "cache_hit"
                    )

                    resolved_by_normalized[
                        normalized
                    ] = cached

                    continue

                self.metrics.increment(
                    "cache_miss"
                )

                raw_value = normalized_to_raw[
                    normalized
                ]

                result = self.resolver.resolve(
                    raw_value,
                    threshold_value,
                    limit_value
                ).to_dict()

                resolved_by_normalized[
                    normalized
                ] = result

                to_cache.append(
                    (
                        normalized,
                        threshold_value,
                        limit_value,
                        result
                    )
                )

            self.cache.mset_pipeline(
                to_cache
            )

            final_output = []

            for raw_title, normalized in raw_validity:
                if not normalized:
                    final_output.append(
                        self.resolver.resolve(
                            raw_title,
                            threshold_value,
                            limit_value
                        ).to_dict()
                    )

                    continue

                final_output.append(
                    resolved_by_normalized[
                        normalized
                    ]
                )

            return final_output

        finally:
            self.metrics.record_latency(
                (time.perf_counter() - start_time)
                * 1000
            )

    def get_metrics(self) -> Dict[str, Any]:
        return self.metrics.get_metrics()

    def close(self) -> None:
        try:
            if self.repository is not None:
                self.repository.close()
        finally:
            self.cache.close()

    def __enter__(self) -> "OccupationService":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ) -> None:
        self.close()
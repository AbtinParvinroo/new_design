from __future__ import annotations
from redis.exceptions import RedisError, TimeoutError as RedisTimeoutError
from redis.exceptions import ConnectionError as RedisConnectionError
from typing import Any, Dict, List, Optional, Sequence, Tuple
from fuzzy_searcher.enums import ResolutionStatus
from fuzzy_searcher.config import ConfigManager
import logging
import hashlib
import redis
import json

class OccupationCache:
    def __init__(
        self,
        config: ConfigManager,
        logger: logging.Logger
    ):
        self.config = config
        self.logger = logger

        cache_config = config.cache()

        self.enabled = bool(
            cache_config.get(
                "enabled",
                True
            )
        )

        self.prefix = str(
            cache_config.get(
                "prefix",
                "occupation"
            )
        )

        taxonomy_version = str(
            config.taxonomy().get(
                "version",
                "v1"
            )
        )

        self.version = str(
            cache_config.get(
                "version",
                taxonomy_version
            )
        )

        self.ttl = max(
            1,
            int(
                cache_config.get(
                    "ttl",
                    3600
                )
            )
        )

        self.review_ttl = max(
            1,
            int(
                cache_config.get(
                    "review_ttl",
                    self.ttl
                )
            )
        )

        self.negative_ttl = max(
            1,
            int(
                cache_config.get(
                    "negative_ttl",
                    300
                )
            )
        )

        self.redis_client = None

        if self.enabled:
            self._connect()

    def _connect(self) -> None:
        try:
            redis_config = self.config.redis()

            redis_config.setdefault(
                "socket_timeout",
                1.0
            )

            redis_config.setdefault(
                "socket_connect_timeout",
                1.0
            )

            redis_config.setdefault(
                "health_check_interval",
                30
            )

            self.redis_client = redis.Redis(
                **redis_config
            )

            self.redis_client.ping()

            self.logger.info(
                "Redis connected"
            )

        except (
            RedisError,
            OSError
        ) as exc:
            self.logger.warning(
                "Redis unavailable: %s",
                exc
            )

            self.redis_client = None
            self.enabled = False

    def build_key(
        self,
        query: str,
        threshold: float,
        limit: int
    ) -> str:
        payload = {
            "query": query,
            "threshold": round(threshold, 4),
            "limit": limit,
            "version": self.version
        }

        digest = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest()

        return (
            f"{self.prefix}:"
            f"{self.version}:"
            f"{digest}"
        )

    def get(
        self,
        query: str,
        threshold: float,
        limit: int
    ) -> Optional[Dict[str, Any]]:
        if not self.enabled or self.redis_client is None:
            return None

        try:
            cached = self.redis_client.get(
                self.build_key(
                    query,
                    threshold,
                    limit
                )
            )

            if not cached:
                return None

            if isinstance(cached, bytes):
                cached = cached.decode(
                    "utf-8"
                )

            value = json.loads(cached)

            return value if isinstance(
                value,
                dict
            ) else None

        except (
            RedisTimeoutError,
            RedisConnectionError
        ) as exc:
            self.logger.warning(
                "Redis read connection error: %s",
                exc
            )

        except (
            RedisError,
            json.JSONDecodeError,
            TypeError,
            ValueError
        ) as exc:
            self.logger.warning(
                "Redis read error: %s",
                exc
            )

        return None

    def mget(
        self,
        keys: Sequence[str]
    ) -> List[Optional[Dict[str, Any]]]:
        if (
            not self.enabled
            or self.redis_client is None
            or not keys
        ):
            return [None] * len(keys)

        try:
            raw_results = self.redis_client.mget(
                list(keys)
            )

            results = []

            for raw_value in raw_results:
                if not raw_value:
                    results.append(None)
                    continue

                if isinstance(raw_value, bytes):
                    raw_value = raw_value.decode(
                        "utf-8"
                    )

                try:
                    value = json.loads(
                        raw_value
                    )
                except (
                    json.JSONDecodeError,
                    TypeError,
                    ValueError
                ):
                    value = None

                results.append(
                    value
                    if isinstance(value, dict)
                    else None
                )

            return results

        except RedisError as exc:
            self.logger.warning(
                "Redis mget error: %s",
                exc
            )

            return [None] * len(keys)

    def _ttl_for_status(
        self,
        status: str
    ) -> int:
        if status in {
            ResolutionStatus.UNRESOLVED.value,
            ResolutionStatus.AMBIGUOUS.value
        }:
            return self.negative_ttl

        if status == ResolutionStatus.REVIEW.value:
            return self.review_ttl

        return self.ttl

    def set(
        self,
        query: str,
        threshold: float,
        limit: int,
        value: Dict[str, Any]
    ) -> None:
        if not self.enabled or self.redis_client is None:
            return

        try:
            status = str(
                value.get(
                    "status",
                    ResolutionStatus.UNRESOLVED.value
                )
            )

            ttl = self._ttl_for_status(
                status
            )

            payload = json.dumps(
                value,
                ensure_ascii=False
            )

            self.redis_client.setex(
                self.build_key(
                    query,
                    threshold,
                    limit
                ),
                ttl,
                payload
            )

        except RedisError as exc:
            self.logger.warning(
                "Redis write error: %s",
                exc
            )

    def mset_pipeline(
        self,
        items: Sequence[
            Tuple[str, float, int, Dict[str, Any]]
        ]
    ) -> None:
        if (
            not self.enabled
            or self.redis_client is None
            or not items
        ):
            return

        try:
            pipeline = self.redis_client.pipeline(
                transaction=False
            )

            for (
                query,
                threshold,
                limit,
                value
            ) in items:
                status = str(
                    value.get(
                        "status",
                        ResolutionStatus.UNRESOLVED.value
                    )
                )

                ttl = self._ttl_for_status(
                    status
                )

                pipeline.setex(
                    self.build_key(
                        query,
                        threshold,
                        limit
                    ),
                    ttl,
                    json.dumps(
                        value,
                        ensure_ascii=False
                    )
                )

            pipeline.execute()

        except RedisError as exc:
            self.logger.warning(
                "Redis pipeline write error: %s",
                exc
            )

    def close(self) -> None:
        if self.redis_client is not None:
            try:
                self.redis_client.close()
            except RedisError:
                pass

            self.redis_client = None
from __future__ import annotations
from fuzzy_searcher.data_models import OccupationRecord
from fuzzy_searcher.config import ConfigManager
from psycopg2 import OperationalError, pool
from typing import Any, List
import logging
import json
import time
import re

class OccupationRepository:
    def fetch_all(self) -> List[OccupationRecord]:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

class PostgreSQLOccupationRepository(OccupationRepository):
    def __init__(
        self,
        config: ConfigManager,
        logger: logging.Logger
    ):
        self.config = config
        self.logger = logger
        self.connection_pool = None
        self._create_pool()

    def _create_pool(self) -> None:
        database_config = self.config.database()

        min_connections = int(
            database_config.pop(
                "min_connections",
                1
            )
        )

        max_connections = int(
            database_config.pop(
                "max_connections",
                10
            )
        )

        if min_connections < 1:
            raise ValueError(
                "min_connections must be greater than zero"
            )

        if max_connections < min_connections:
            raise ValueError(
                "max_connections cannot be lower than min_connections"
            )

        database_config.setdefault(
            "connect_timeout",
            5
        )

        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                **database_config
            )

            self.logger.info(
                "PostgreSQL connection pool initialized"
            )

        except OperationalError as exc:
            self.logger.error(
                "Failed to initialize PostgreSQL pool: %s",
                exc
            )

            raise RuntimeError(
                "Database initialization failed"
            ) from exc

    def fetch_all(self) -> List[OccupationRecord]:
        if self.connection_pool is None:
            raise RuntimeError(
                "Database connection pool is not initialized"
            )

        database_config = self.config.database()

        retries = max(
            1,
            int(database_config.get("retries", 3))
        )

        delay = 1.0

        query = """
            SELECT
                uri,
                preferred_label,
                alt_labels,
                isco_code,
                definition
            FROM occupations
            WHERE preferred_label IS NOT NULL
        """

        for attempt in range(retries):
            connection = None

            try:
                connection = self.connection_pool.getconn()

                records: List[OccupationRecord] = []

                with connection.cursor() as cursor:
                    cursor.execute(query)

                    for row in cursor:
                        records.append(
                            OccupationRecord(
                                uri=str(row[0] or ""),
                                preferred_label=str(row[1] or ""),
                                alt_labels=tuple(
                                    self._parse_alt_labels(row[2])
                                ),
                                isco_code=str(row[3] or ""),
                                definition=str(row[4] or ""),
                                taxonomy=str(
                                    self.config.taxonomy().get(
                                        "name",
                                        "esco"
                                    )
                                ),
                                source=str(
                                    self.config.taxonomy().get(
                                        "source",
                                        "database"
                                    )
                                )
                            )
                        )

                self.logger.info(
                    "Loaded %s occupations",
                    len(records)
                )

                return records

            except OperationalError as exc:
                self.logger.warning(
                    "Database error on attempt %s/%s: %s",
                    attempt + 1,
                    retries,
                    exc
                )

                if attempt >= retries - 1:
                    raise

                time.sleep(delay)
                delay = min(
                    delay * 2,
                    8.0
                )

            finally:
                if connection is not None:
                    self.connection_pool.putconn(
                        connection
                    )

        raise RuntimeError(
            "Database loading failed"
        )

    @staticmethod
    def _parse_alt_labels(value: Any) -> List[str]:
        if not value:
            return []

        if isinstance(value, (list, tuple)):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        if isinstance(value, str):
            value = value.strip()

            if (
                value.startswith("[")
                and value.endswith("]")
            ):
                try:
                    parsed = json.loads(value)

                    if isinstance(parsed, list):
                        return [
                            str(item).strip()
                            for item in parsed
                            if str(item).strip()
                        ]

                except json.JSONDecodeError:
                    pass

            return [
                item.strip()
                for item in re.split(
                    r"[|;,]",
                    value
                )
                if item.strip()
            ]

        normalized = str(value).strip()

        return [normalized] if normalized else []

    def close(self) -> None:
        if self.connection_pool is not None:
            self.connection_pool.closeall()
            self.connection_pool = None

            self.logger.info(
                "PostgreSQL pool closed"
            )
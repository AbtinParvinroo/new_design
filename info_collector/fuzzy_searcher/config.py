from __future__ import annotations
from typing import Any, Dict
import logging
import json

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self._validate_config()

    @staticmethod
    def _load_config(config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError("Configuration root must be an object")

            return data

        except FileNotFoundError:
            logging.getLogger("occupation_resolver").warning(
                "Config file not found. Using defaults."
            )
            return {}

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON configuration: {exc}"
            ) from exc

    def _validate_config(self) -> None:
        fuzzy = self.fuzzy()

        threshold = self._validate_score(
            fuzzy.get("threshold", 70),
            "threshold"
        )

        accept_threshold = self._validate_score(
            fuzzy.get("accept_threshold", 90),
            "accept_threshold"
        )

        review_threshold = self._validate_score(
            fuzzy.get("review_threshold", 75),
            "review_threshold"
        )

        if review_threshold > accept_threshold:
            raise ValueError(
                "review_threshold cannot be greater than accept_threshold"
            )

        if threshold < 0 or threshold > 100:
            raise ValueError("threshold must be between 0 and 100")

        limit = int(fuzzy.get("limit", 5))
        candidate_limit = int(fuzzy.get("candidate_limit", 20))

        if limit < 1:
            raise ValueError("limit must be greater than zero")

        if candidate_limit < limit:
            raise ValueError(
                "candidate_limit must be greater than or equal to limit"
            )

        preferred_weight = float(
            fuzzy.get("preferred_label_weight", 0.70)
        )

        alias_weight = float(
            fuzzy.get("alias_weight", 0.30)
        )

        if preferred_weight < 0 or alias_weight < 0:
            raise ValueError("Scoring weights cannot be negative")

        if preferred_weight + alias_weight <= 0:
            raise ValueError(
                "At least one scoring weight must be greater than zero"
            )

        accept_margin = float(fuzzy.get("accept_margin", 8))
        review_margin = float(fuzzy.get("review_margin", 3))

        if accept_margin < 0 or review_margin < 0:
            raise ValueError("Margins cannot be negative")

        if review_margin > accept_margin:
            raise ValueError(
                "review_margin cannot be greater than accept_margin"
            )

        max_query_length = int(
            self.validation().get("max_query_length", 256)
        )

        if max_query_length < 1:
            raise ValueError(
                "max_query_length must be greater than zero"
            )

    @staticmethod
    def _validate_score(value: Any, name: str) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric"
            ) from exc

        if not 0 <= score <= 100:
            raise ValueError(
                f"{name} must be between 0 and 100"
            )

        return score

    def get(self, *keys: str, default: Any = None) -> Any:
        value: Any = self.config

        for key in keys:
            if not isinstance(value, dict):
                return default

            value = value.get(key)

            if value is None:
                return default

        return value

    def database(self) -> Dict[str, Any]:
        return dict(self.get("database", default={}))

    def redis(self) -> Dict[str, Any]:
        return dict(self.get("redis", default={}))

    def cache(self) -> Dict[str, Any]:
        return dict(self.get("cache", default={}))

    def fuzzy(self) -> Dict[str, Any]:
        return dict(self.get("fuzzy_search", default={}))

    def logging(self) -> Dict[str, Any]:
        return dict(self.get("logging", default={}))

    def taxonomy(self) -> Dict[str, Any]:
        return dict(self.get("taxonomy", default={}))

    def validation(self) -> Dict[str, Any]:
        return dict(self.get("validation", default={}))

    def normalization(self) -> Dict[str, Any]:
        return dict(self.get("normalization", default={}))

class LoggerFactory:
    @staticmethod
    def create(config: ConfigManager) -> logging.Logger:
        log_config = config.logging()

        level = getattr(
            logging,
            str(log_config.get("level", "INFO")).upper(),
            logging.INFO
        )

        format_string = log_config.get(
            "format",
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )

        logging.basicConfig(
            level=level,
            format=format_string
        )

        return logging.getLogger("occupation_resolver")
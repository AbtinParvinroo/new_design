from __future__ import annotations
from fuzzy_searcher.config import ConfigManager
from typing import Optional

class InputValidator:
    def __init__(self, config: ConfigManager):
        self.max_length = int(
            config.validation().get(
                "max_query_length",
                256
            )
        )

    def validate(self, value: Optional[str]) -> str:
        if value is None:
            return ""

        if not isinstance(value, str):
            raise TypeError(
                "Occupation title must be a string"
            )

        value = value.strip()

        if not value:
            return ""

        if len(value) > self.max_length:
            raise ValueError(
                f"Occupation title exceeds maximum length of "
                f"{self.max_length}"
            )

        return value
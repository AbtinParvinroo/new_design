from __future__ import annotations
from fuzzy_searcher.config import ConfigManager
from typing import Optional
import unicodedata
import re

class OccupationNormalizer:
    def __init__(self, config: ConfigManager):
        normalization_config = config.normalization()

        self.lowercase = bool(
            normalization_config.get(
                "lowercase",
                True
            )
        )

        self.strip_punctuation = bool(
            normalization_config.get(
                "strip_punctuation",
                True
            )
        )

        self.whitespace_pattern = re.compile(r"\s+")

        self.punctuation_pattern = re.compile(
            r"[^\w\s]",
            re.UNICODE
        )

        self.hyphen_pattern = re.compile(
            r"[-‐-‒–—―]"
        )

    def normalize(self, value: Optional[str]) -> str:
        if not value:
            return ""

        value = unicodedata.normalize(
            "NFKC",
            value
        )

        if self.lowercase:
            value = value.casefold()

        value = self.hyphen_pattern.sub(
            " ",
            value
        )

        if self.strip_punctuation:
            value = self.punctuation_pattern.sub(
                " ",
                value
            )

        value = self.whitespace_pattern.sub(
            " ",
            value
        )

        return value.strip()
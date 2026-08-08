# processors/normalizer.py
import re
import unicodedata
from typing import Tuple

from core.models import PostProcessorConfig


class TextNormalizer:
    def __init__(self, config: PostProcessorConfig):
        self.config = config
        self.bullet_pattern = re.compile(
            config.bullet_pattern,
            flags=re.MULTILINE,
            timeout=config.regex_timeout
        )

    def normalize_unicode(self, text: str) -> Tuple[str, int]:
        normalized = unicodedata.normalize(self.config.normalization_form, text)
        return normalized, int(normalized != text)

    def normalize_whitespace(self, text: str) -> Tuple[str, int]:
        original_len = len(text)
        text = re.sub(r"[ \t]+", " ", text, timeout=self.config.regex_timeout)
        text = re.sub(r"[ \t]+\n", "\n", text, timeout=self.config.regex_timeout)
        text = re.sub(r"\n{3,}", "\n\n", text, timeout=self.config.regex_timeout)
        changes = abs(original_len - len(text))
        return text, changes

    def remove_empty_lines(self, text: str) -> Tuple[str, int]:
        lines = text.splitlines()
        filtered = [line.strip() for line in lines if line.strip()]
        removed = len(lines) - len(filtered)
        return "\n".join(filtered), removed

    def fill_broken_paragraphs(self, text: str, lang: str) -> Tuple[str, int]:
        lines = text.splitlines()
        result: list[str] = []
        buffer: list[str] = []
        merged = 0

        terminators = (".", "!", "?", ":", "؟") if lang == "fa" else (".", "!", "?", ":")

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if buffer:
                    result.append(" ".join(buffer))
                    buffer.clear()
                continue

            if self.bullet_pattern.match(stripped):
                if buffer:
                    result.append(" ".join(buffer))
                    buffer.clear()
                result.append(stripped)
                continue

            buffer.append(stripped)

            if stripped.endswith(terminators):
                result.append(" ".join(buffer))
                merged += max(0, len(buffer) - 1)
                buffer.clear()

        if buffer:
            result.append(" ".join(buffer))
            merged += max(0, len(buffer) - 1)

        return "\n".join(result), merged
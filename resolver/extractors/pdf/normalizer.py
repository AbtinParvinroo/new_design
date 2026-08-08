# extractors/pdf/normalizer.py
import re
import unicodedata

from core.models import PDFResolverConfig


class TextNormalizer:
    def __init__(self, config: PDFResolverConfig):
        self.config = config

    def normalize(self, text: str) -> str:
        if not text:
            return ""

        if self.config.normalize_unicode:
            text = unicodedata.normalize("NFKC", text)

        if self.config.normalize_whitespace:
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = text.strip()

        return text
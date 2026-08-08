# processors/ocr_corrector.py
import logging
from typing import Tuple

from core.models import PostProcessorConfig

logger = logging.getLogger(__name__)


class OcrCorrector:
    def __init__(self, config: PostProcessorConfig):
        self.config = config

    def fix(self, text: str, lang: str) -> Tuple[str, int]:
        total = 0
        patterns = self.config.ocr_patterns_fa if lang == "fa" else self.config.ocr_patterns_en

        for pattern, replacement in patterns.items():
            try:
                count = text.count(pattern)
                if count > 0:
                    text = text.replace(pattern, replacement)
                    total += count
            except Exception as e:
                logger.warning("invalid_ocr_replacement", extra={"pattern": pattern, "error": str(e)})

        return text, total
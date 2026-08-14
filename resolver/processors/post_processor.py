# processors/post_processor.py
import logging
import time
from dataclasses import asdict
from typing import Optional
from resolver.core.models import PostProcessorConfig, PostProcessingStats, PostProcessingResult
from resolver.core.exceptions import ValidationError, ProcessingError
from resolver.processors.language_detector import detect_language
from resolver.processors.normalizer import TextNormalizer
from resolver.processors.ocr_corrector import OcrCorrector
from resolver.processors.section_extractor import SectionExtractor
from resolver.processors.pipeline import Pipeline

logger = logging.getLogger(__name__)

class PostProcessor:
    def __init__(self, config: Optional[PostProcessorConfig] = None):
        self.config = config or PostProcessorConfig()
        self.normalizer = TextNormalizer(self.config)
        self.ocr_corrector = OcrCorrector(self.config)
        self.section_extractor = SectionExtractor(self.config)
        self.pipeline = Pipeline(self.config)

    def _validate_input(self, text: str) -> None:
        if not isinstance(text, str):
            raise ValidationError(f"Input must be a string, got {type(text).__name__}.")
        if len(text) > self.config.max_text_length:
            raise ValidationError(f"Input length ({len(text)}) exceeds maximum allowed ({self.config.max_text_length}).")

    def _build_stage_handlers(self, lang: str):
        return {
            "normalize_unicode": self.normalizer.normalize_unicode,
            "remove_headers": self._remove_headers,  # dummy for now
            "remove_page_numbers": self._remove_page_numbers,  # dummy
            "fix_ocr_errors": lambda t: self.ocr_corrector.fix(t, lang),
            "fill_broken_paragraphs": lambda t: self.normalizer.fill_broken_paragraphs(t, lang),
            "normalize_whitespace": self.normalizer.normalize_whitespace,
            "remove_empty_lines": self.normalizer.remove_empty_lines,
        }

    def _remove_headers(self, text: str) -> tuple[str, int]:
        # Placeholder: implement header removal using patterns if needed
        return text, 0

    def _remove_page_numbers(self, text: str) -> tuple[str, int]:
        # Placeholder: implement page number removal using patterns
        removed = 0
        for pattern in self.config.page_patterns:
            # Using re.sub with compiled pattern would be better, but for now we'll just return
            pass
        return text, 0

    def process(self, raw_text: str) -> PostProcessingResult:
        self._validate_input(raw_text)

        start_time = time.perf_counter()
        logger.info("post_processing_started", extra={"input_length": len(raw_text)})

        lang = detect_language(raw_text)
        text = raw_text
        stats = PostProcessingStats(
            input_lines=len(raw_text.splitlines()),
            detected_language=lang
        )

        try:
            stage_handlers = self._build_stage_handlers(lang)
            result = self.pipeline.execute(text, stage_handlers)
            text = result["text"]
            stage_stats = result["stats"]

            # Map stage stats to PostProcessingStats attributes
            stat_mapping = {
                "normalize_unicode": "unicode_changes",
                "remove_headers": "headers_removed",
                "remove_page_numbers": "page_numbers_removed",
                "fix_ocr_errors": "ocr_replacements",
                "fill_broken_paragraphs": "paragraph_merges",
                "normalize_whitespace": "whitespace_normalized",
                "remove_empty_lines": "empty_lines_removed",
            }
            for stage, value in stage_stats.items():
                attr = stat_mapping.get(stage)
                if attr:
                    setattr(stats, attr, value)

            # Section extraction
            sections = self.section_extractor.extract(text)

            stats.output_lines = len(text.splitlines())
            stats.sections_found = sum(1 for val in sections.values() if val.strip())
            if len(raw_text) > 0:
                stats.text_reduction_ratio = round(1.0 - (len(text) / len(raw_text)), 4)

        except TimeoutError as exc:
            logger.error("regex_timeout_detected")
            raise ProcessingError("ReDoS protection triggered: Regex processing timed out.") from exc
        except Exception as exc:
            logger.exception("post_processing_failed")
            raise ProcessingError("An unexpected error occurred during processing.") from exc

        elapsed_time = round(time.perf_counter() - start_time, 4)

        logger.info(
            "post_processing_completed",
            extra={
                **asdict(stats),
                "elapsed_seconds": elapsed_time
            }
        )

        return PostProcessingResult(
            text=text,
            processing_time=elapsed_time,
            stats=stats,
            sections=sections
        )
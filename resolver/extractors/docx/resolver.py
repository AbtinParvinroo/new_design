# extractors/docx/resolver.py
import logging
import time
from pathlib import Path
from typing import Optional

from core.models import WordResolverConfig, WordExtractionResult, WordMetadata
from core.exceptions import WordExtractionError
from .archive import WordArchiveHandler
from .metadata import WordMetadataExtractor
from .elements import WordElementExtractor

logger = logging.getLogger(__name__)


class WordResolver:
    def __init__(
        self,
        file_path: str | Path,
        config: Optional[WordResolverConfig] = None
    ):
        self.file_path = Path(file_path)
        self.config = config or WordResolverConfig()
        self.archive_handler = WordArchiveHandler(self.file_path, self.config)
        self._cached_result: Optional[WordExtractionResult] = None
        self._cached_metadata: Optional[WordMetadata] = None

        logger.debug(
            "word_resolver_initialized",
            extra={
                "file": str(self.file_path),
                "max_text_length": self.config.max_text_length,
                "max_compressed_size_mb": self.config.max_compressed_size_mb,
                "max_uncompressed_size_mb": self.config.max_uncompressed_size_mb
            }
        )

    def __enter__(self) -> WordResolver:
        self.archive_handler.initialize_document()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.cleanup()

    def _extract_metadata(self) -> WordMetadata:
        if self._cached_metadata is not None:
            return self._cached_metadata

        doc = self.archive_handler.get_document()
        self._cached_metadata = WordMetadataExtractor.extract(doc, self.file_path)
        return self._cached_metadata

    def _truncate_text(self, text: str) -> tuple[str, int, bool]:
        total_chars = len(text)
        if total_chars <= self.config.max_text_length:
            return text, total_chars, False

        candidate = text[:self.config.max_text_length]
        boundary = candidate.rfind(" ")
        if boundary > 0:
            candidate = candidate[:boundary]

        candidate += "\n\n...[TRUNCATED]"

        logger.warning(
            "word_text_truncated",
            extra={
                "original_length": total_chars,
                "limit": self.config.max_text_length
            }
        )
        return candidate, total_chars, True

    def extract(self) -> WordExtractionResult:
        if self._cached_result is not None:
            logger.debug("word_cached_result_returned", extra={"file": str(self.file_path)})
            return self._cached_result

        start_time = time.perf_counter()
        health_status = "Healthy"

        try:
            metadata = self._extract_metadata()
            doc = self.archive_handler.get_document()
            element_extractor = WordElementExtractor(self.config, doc)

            body_chunks, par_count, ne_par_count, table_count = element_extractor.extract_body()
            header_chunks = element_extractor.extract_headers_and_footers()
            textbox_chunks, textbox_count = element_extractor.extract_textboxes()

            chunks = [*body_chunks, *header_chunks]
            if textbox_chunks:
                chunks.extend(f"[Textbox] {value}" for value in textbox_chunks)

            full_text = "\n".join(chunks)
            full_text, total_chars, truncated = self._truncate_text(full_text)

            if truncated:
                health_status = "Degraded"

            extraction_time = round(time.perf_counter() - start_time, 4)

            result = WordExtractionResult(
                text=full_text,
                total_chars=total_chars,
                truncated=truncated,
                extraction_time=extraction_time,
                paragraph_count=par_count,
                non_empty_paragraph_count=ne_par_count,
                table_count=table_count,
                textbox_count=textbox_count,
                metadata=metadata,
                health_status=health_status,
                success=True
            )

            self._cached_result = result
            logger.info(
                "word_extraction_completed",
                extra={
                    "file": str(self.file_path),
                    "characters": total_chars,
                    "paragraphs": par_count,
                    "health": health_status,
                    "elapsed_seconds": extraction_time
                }
            )
            return result

        except Exception as e:
            logger.exception("word_extraction_failed", extra={"file": str(self.file_path)})
            raise WordExtractionError(f"Extraction failed: {str(e)}") from e

    @property
    def metadata(self) -> WordMetadata:
        return self._extract_metadata()

    def cleanup(self) -> None:
        logger.debug("word_cleanup_started", extra={"file": str(self.file_path)})
        self.archive_handler.cleanup()
        self._cached_result = None
        self._cached_metadata = None
        logger.info("word_cleanup_completed", extra={"file": str(self.file_path)})
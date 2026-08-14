# extractors/pdf/resolver.py
import logging
import time
from pathlib import Path
from typing import Optional, List
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from resolver.core.models import PDFResolverConfig, PDFExtractionResult
from resolver.core.exceptions import InvalidPDFError, EncryptedPDFError, PDFExtractionError
from resolver.validators.pdf_validator import PDFValidator
from resolver.extractors.pdf.metadata import PDFMetadataExtractor
from resolver.extractors.pdf.normalizer import TextNormalizer

logger = logging.getLogger(__name__)

class PDFResolver:
    def __init__(self, file_path: str | Path, config: Optional[PDFResolverConfig] = None):
        self.file_path = Path(file_path)
        self.config = config or PDFResolverConfig()
        self.reader: Optional[PdfReader] = None
        self.normalizer = TextNormalizer(self.config)
        self._cached_result: Optional[PDFExtractionResult] = None
        self._cached_page_count: Optional[int] = None
        self._cached_metadata = None

        logger.debug(
            "pdf_resolver_initialized",
            extra={
                "file": str(self.file_path),
                "max_pages": self.config.max_pages,
                "max_text_length": self.config.max_text_length,
                "mode": self.config.extraction_mode
            }
        )

    def __enter__(self):
        self._initialize_reader()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.cleanup()

    def _initialize_reader(self) -> None:
        if self.reader is not None:
            return

        PDFValidator.validate_file(self.file_path)

        try:
            self.reader = PdfReader(self.file_path, strict=False)
        except PdfReadError as exc:
            logger.exception("pdf_parsing_failed", extra={"file": str(self.file_path)})
            raise InvalidPDFError("Invalid PDF structure.") from exc

        if self.reader.is_encrypted:
            logger.error("pdf_encrypted_detected", extra={"file": str(self.file_path)})
            raise EncryptedPDFError("Encrypted PDFs are not supported.")

        logger.info("pdf_reader_initialized", extra={"file": str(self.file_path)})

    def _get_page_count(self) -> int:
        if self._cached_page_count is not None:
            return self._cached_page_count

        self._initialize_reader()
        assert self.reader is not None
        page_count = len(self.reader.pages)
        PDFValidator.validate_page_limit(page_count, self.config.max_pages)
        self._cached_page_count = page_count
        return page_count

    def _extract_metadata(self):
        if self._cached_metadata is not None:
            return self._cached_metadata

        self._initialize_reader()
        assert self.reader is not None
        self._cached_metadata = PDFMetadataExtractor.extract(self.reader, self.file_path.name)
        return self._cached_metadata

    def _extract_page_text(self, page, page_number: int) -> str:
        try:
            text = page.extract_text(extraction_mode=self.config.extraction_mode)
        except TypeError:
            logger.debug("pdf_extraction_mode_unsupported", extra={"page": page_number})
            text = page.extract_text()
        except (ValueError, KeyError, IndexError, PdfReadError) as e:
            logger.exception("pdf_primary_extraction_failed", extra={"page": page_number, "error": str(e)})
            raise PDFExtractionError(f"Extraction failed on page {page_number}") from e

        if text:
            return self.normalizer.normalize(text)

        try:
            fallback = page.extract_text()
        except (TypeError, ValueError, KeyError, IndexError, PdfReadError) as e:
            logger.exception("pdf_fallback_extraction_failed", extra={"page": page_number, "error": str(e)})
            raise PDFExtractionError(f"Fallback extraction failed on page {page_number}") from e

        return self.normalizer.normalize(fallback or "")

    def _is_probably_scanned_pdf(self, extracted_pages: int) -> bool:
        if extracted_pages > 0:
            return False
        logger.warning("pdf_no_extractable_text_detected", extra={"file": str(self.file_path)})
        return True

    def _truncate_text(self, text: str) -> tuple[str, bool]:
        if len(text) <= self.config.max_text_length:
            return text, False

        limit = self.config.max_text_length
        candidate = text[:limit]
        boundary = candidate.rfind(" ")
        if boundary > 0:
            candidate = candidate[:boundary]
        candidate += "\n\n...[TRUNCATED]"
        logger.warning(
            "pdf_text_truncated",
            extra={"original_length": len(text), "limit": limit}
        )
        return candidate, True

    def extract(self) -> PDFExtractionResult:
        if self._cached_result is not None:
            logger.debug("pdf_returning_cached_result", extra={"file": str(self.file_path)})
            return self._cached_result

        self._initialize_reader()
        assert self.reader is not None

        start_time = time.perf_counter()
        page_count = self._get_page_count()
        metadata = self._extract_metadata()
        text_chunks: List[str] = []
        failed_pages: List[int] = []
        extracted_pages = 0

        logger.info("pdf_extraction_started", extra={"file": str(self.file_path), "page_count": page_count})

        for page_index in range(page_count):
            page_number = page_index + 1
            try:
                page = self.reader.pages[page_index]
                text = self._extract_page_text(page=page, page_number=page_number)

                if text:
                    extracted_pages += 1
                    text_chunks.append(text)
                    logger.debug("pdf_page_extracted", extra={"page": page_number, "characters": len(text)})
                elif self.config.keep_empty_pages:
                    text_chunks.append("")
                    logger.debug("pdf_empty_page_preserved", extra={"page": page_number})
                else:
                    logger.debug("pdf_empty_page_skipped", extra={"page": page_number})

            except (PDFExtractionError, PdfReadError, ValueError):
                failed_pages.append(page_number)
                logger.exception("pdf_page_extraction_failed", extra={"page": page_number})

        full_text = "\n\n".join(text_chunks)
        original_total_chars = len(full_text)
        final_text, truncated = self._truncate_text(full_text)
        extraction_time = round(time.perf_counter() - start_time, 4)

        result = PDFExtractionResult(
            text=final_text,
            total_chars=original_total_chars,
            page_count=page_count,
            truncated=truncated,
            ocr_required=self._is_probably_scanned_pdf(extracted_pages),
            failed_pages=failed_pages,
            metadata=metadata,
            extraction_time=extraction_time
        )

        self._cached_result = result
        logger.info(
            "pdf_extraction_completed",
            extra={
                "file": str(self.file_path),
                "pages": page_count,
                "successful_pages": extracted_pages,
                "failed_pages": len(failed_pages),
                "characters": result.total_chars,
                "truncated": truncated,
                "ocr_required": result.ocr_required,
                "elapsed_seconds": extraction_time
            }
        )

        return result

    def has_extractable_text(self) -> bool:
        self._initialize_reader()
        assert self.reader is not None

        for page_index, page in enumerate(self.reader.pages, start=1):
            try:
                text = self._extract_page_text(page=page, page_number=page_index)
                if text:
                    logger.debug("pdf_extractable_text_detected", extra={"page": page_index})
                    return True
            except (PDFExtractionError, TypeError, ValueError, KeyError, IndexError, PdfReadError):
                logger.debug("pdf_failed_while_checking_page", extra={"page": page_index})

        logger.debug("pdf_no_extractable_text_detected", extra={"file": str(self.file_path)})
        return False

    @property
    def metadata(self):
        return self._extract_metadata()

    @property
    def page_count(self) -> int:
        return self._get_page_count()

    def cleanup(self) -> None:
        logger.debug("pdf_resolver_cleanup_started", extra={"file": str(self.file_path)})
        self.reader = None
        self._cached_result = None
        logger.info("pdf_resolver_cleanup_completed", extra={"file": str(self.file_path)})
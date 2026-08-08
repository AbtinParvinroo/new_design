# validators/pdf_validator.py
import logging
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from core.exceptions import InvalidPdfError, PDFValidationError, EncryptedPDFError

logger = logging.getLogger(__name__)


class PDFValidator:
    @staticmethod
    def validate_file(file_path: Path) -> None:
        if not file_path.exists():
            logger.error("pdf_file_not_found", extra={"file": str(file_path)})
            raise PDFValidationError(f"File not found: {file_path}")

        if not file_path.is_file():
            logger.error("pdf_path_not_a_file", extra={"file": str(file_path)})
            raise PDFValidationError("Path is not a regular file.")

        if file_path.suffix.lower() != ".pdf":
            logger.error("pdf_invalid_extension", extra={"file": str(file_path), "suffix": file_path.suffix})
            raise PDFValidationError("Only PDF files are supported.")

        if file_path.stat().st_size == 0:
            logger.error("pdf_file_empty", extra={"file": str(file_path)})
            raise PDFValidationError("PDF file is empty.")

    @staticmethod
    def validate_page_limit(page_count: int, max_pages: int) -> None:
        if page_count > max_pages:
            logger.error("pdf_max_pages_exceeded", extra={"page_count": page_count, "limit": max_pages})
            raise PDFValidationError(f"PDF contains {page_count} pages. Maximum supported: {max_pages}.")

    @staticmethod
    def validate_pdf_structure(path: Path) -> None:
        try:
            reader = PdfReader(path, strict=False)
            if reader.is_encrypted:
                raise EncryptedPDFError("Encrypted PDFs are not supported")
            page_count = len(reader.pages)
            if page_count == 0:
                raise InvalidPdfError("PDF contains no pages")
            logger.debug("pdf_structure_validated", extra={"page_count": page_count})
        except PdfReadError as e:
            raise InvalidPdfError(f"Corrupted or invalid PDF structure: {e}")
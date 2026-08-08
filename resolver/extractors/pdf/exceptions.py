# extractors/pdf/exceptions.py
# Re-export PDF specific exceptions from core for module convenience
from core.exceptions import (
    PDFResolverError,
    InvalidPDFError,
    EncryptedPDFError,
    PDFValidationError,
    PDFExtractionError
)

__all__ = [
    "PDFResolverError",
    "InvalidPDFError",
    "EncryptedPDFError",
    "PDFValidationError",
    "PDFExtractionError"
]
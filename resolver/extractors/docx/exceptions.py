# extractors/docx/exceptions.py
# Re-export DOCX specific exceptions from core
from core.exceptions import (
    WordResolverError,
    WordValidationError,
    InvalidDocxError,
    WordExtractionError
)

__all__ = [
    "WordResolverError",
    "WordValidationError",
    "InvalidDocxError",
    "WordExtractionError"
]
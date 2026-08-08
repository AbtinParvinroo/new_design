# validators/magic_detector.py
import logging
from pathlib import Path
from typing import Optional

from core.exceptions import InvalidFileTypeError, FileValidationError
from core.constants import ALLOWED_TYPES

logger = logging.getLogger(__name__)


class MagicDetector:
    @staticmethod
    def validate_magic(path: Path, file_type: str) -> None:
        try:
            with open(path, "rb") as file:
                header = file.read(8)
        except IOError as e:
            raise FileValidationError(f"Could not read file for magic number check: {e}")

        allowed_magic = ALLOWED_TYPES[file_type]["magic"]
        matched = any(header.startswith(magic) for magic in allowed_magic)

        if not matched:
            raise InvalidFileTypeError(f"File signature (magic number) does not match expected {file_type} format")

        logger.debug("magic_number_validated", extra={"file_type": file_type})
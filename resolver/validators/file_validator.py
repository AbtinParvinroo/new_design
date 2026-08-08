# validators/file_validator.py
import logging
import time
from pathlib import Path
from typing import Optional

from core.models import FileValidatorConfig, FileValidationResult
from core.exceptions import FileValidationError, InvalidFileTypeError
from core.constants import ALLOWED_TYPES
from .pdf_validator import PDFValidator
from .docx_validator import DOCXValidator
from .magic_detector import MagicDetector

logger = logging.getLogger(__name__)


class FileValidator:
    def __init__(self, config: Optional[FileValidatorConfig] = None):
        self.config = config or FileValidatorConfig()
        self.pdf_validator = PDFValidator()
        self.docx_validator = DOCXValidator(self.config)

    def validate(self, file_path: str) -> FileValidationResult:
        start_time = time.perf_counter()
        path = Path(file_path)

        result = FileValidationResult(
            valid=False,
            filename=path.name
        )

        logger.info(
            "file_validation_started",
            extra={"filename": path.name, "file_path": str(path)}
        )

        try:
            result.validation_stage = "path_validation"
            self._validate_path(path)

            result.validation_stage = "size_validation"
            result.size_mb = self._validate_size(path)

            result.validation_stage = "type_detection"
            file_type = self._detect_file_type(path)
            result.file_type = file_type

            result.validation_stage = "magic_number_validation"
            MagicDetector.validate_magic(path, file_type)

            result.validation_stage = "deep_structure_validation"
            if file_type == "docx":
                self.docx_validator.validate_docx_archive(path)
            elif file_type == "pdf":
                PDFValidator.validate_pdf_structure(path)

            result.valid = True
            result.validation_stage = "completed"

            logger.info(
                "file_validation_passed",
                extra={
                    "filename": path.name,
                    "file_type": file_type,
                    "size_mb": result.size_mb
                }
            )

        except (FileValidationError, InvalidFileTypeError) as e:
            result.failure_reason = str(e)
            logger.warning(
                "file_validation_failed",
                extra={
                    "filename": path.name,
                    "stage": result.validation_stage,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
        except Exception as e:
            result.failure_reason = f"Unexpected system error: {str(e)}"
            logger.error(
                "file_validation_system_error",
                extra={
                    "filename": path.name,
                    "stage": result.validation_stage,
                    "error": str(e)
                },
                exc_info=True
            )
        finally:
            result.validation_time = round(time.perf_counter() - start_time, 4)

        return result

    def _validate_path(self, path: Path) -> None:
        if not path.exists():
            raise FileValidationError("File does not exist")
        if not path.is_file():
            raise FileValidationError("Path is not a regular file")
        if ".." in path.parts:
            raise FileValidationError("Path traversal detected")
        logger.debug("path_validated", extra={"resolved_path": str(path.resolve())})

    def _validate_size(self, path: Path) -> float:
        size_bytes = path.stat().st_size
        size_mb = round(size_bytes / (1024 * 1024), 2)
        if size_bytes > self.config.max_file_size_bytes:
            raise FileValidationError(
                f"File size ({size_mb}MB) exceeds maximum allowed size ({self.config.max_file_size_mb}MB)"
            )
        logger.debug("size_validated", extra={"size_bytes": size_bytes, "size_mb": size_mb})
        return size_mb

    def _detect_file_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        for file_type, config in ALLOWED_TYPES.items():
            if suffix in config["extensions"]:
                logger.debug("type_detected", extra={"extension": suffix, "file_type": file_type})
                return file_type
        raise InvalidFileTypeError(f"Unsupported file extension: {suffix}")
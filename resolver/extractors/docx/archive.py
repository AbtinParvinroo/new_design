# extractors/docx/archive.py
import logging
from pathlib import Path
from typing import Optional

from docx import Document
from docx.document import Document as WordDocument
from docx.opc.exceptions import PackageNotFoundError

from core.models import WordResolverConfig
from core.exceptions import InvalidDocxError, WordValidationError
from validators.docx_validator import DOCXValidator

logger = logging.getLogger(__name__)


class WordArchiveHandler:
    def __init__(self, file_path: Path, config: WordResolverConfig):
        self.file_path = file_path
        self.config = config
        self.doc: Optional[WordDocument] = None
        self._validator = DOCXValidator(
            # Convert WordResolverConfig to a compatible config for DOCXValidator
            # We'll create a minimal config object with required fields
            self._to_file_validator_config()
        )

    def _to_file_validator_config(self):
        # Create a dummy FileValidatorConfig from WordResolverConfig
        # This is a bridge to reuse DOCXValidator
        from core.models import FileValidatorConfig
        return FileValidatorConfig(
            max_file_size_mb=self.config.max_compressed_size_mb,
            max_uncompressed_size_mb=self.config.max_uncompressed_size_mb,
            max_zip_files=1000,
            max_compression_ratio=100
        )

    def validate(self) -> None:
        self._validator.validate_file(self.file_path)
        self._validator.validate_archive(self.file_path)

    def initialize_document(self) -> None:
        if self.doc is not None:
            return

        self.validate()

        try:
            self.doc = Document(self.file_path)
        except PackageNotFoundError as exc:
            logger.exception("word_invalid_package", extra={"file": str(self.file_path)})
            raise InvalidDocxError("Invalid DOCX package structure.") from exc
        except Exception as exc:
            logger.exception("word_initialization_failed", extra={"file": str(self.file_path)})
            raise InvalidDocxError(f"Failed to load Word document: {str(exc)}") from exc

        logger.info("word_document_loaded", extra={"file": str(self.file_path)})

    def get_document(self) -> WordDocument:
        if self.doc is None:
            self.initialize_document()
        assert self.doc is not None
        return self.doc

    def cleanup(self) -> None:
        self.doc = None
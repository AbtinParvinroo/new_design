# validators/docx_validator.py
import logging
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from resolver.core.exceptions import InvalidDocxError, WordValidationError, FileValidationError
from resolver.core.models import FileValidatorConfig

logger = logging.getLogger(__name__)


class DOCXValidator:
    def __init__(self, config: FileValidatorConfig):
        self.config = config

    def validate_file(self, file_path: Path) -> None:
        if not file_path.exists():
            raise WordValidationError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise WordValidationError("Path is not a regular file.")

        if file_path.suffix.lower() != ".docx":
            raise WordValidationError("Only DOCX files are supported.")

        if file_path.stat().st_size == 0:
            raise WordValidationError("DOCX file is empty.")

        # compressed size limit (if provided)
        max_compressed_bytes = getattr(self.config, 'max_compressed_size_mb', None)
        if max_compressed_bytes:
            max_compressed_bytes *= 1024 * 1024
            if file_path.stat().st_size > max_compressed_bytes:
                raise WordValidationError(
                    f"File size exceeds maximum allowed compressed size "
                    f"({max_compressed_bytes // (1024*1024)} MB)."
                )

    def validate_archive(self, file_path: Path) -> None:
        try:
            with ZipFile(file_path) as archive:
                names = {item.filename for item in archive.infolist()}
                if "word/document.xml" not in names:
                    raise InvalidDocxError("Missing document.xml. Not a valid Word structure.")

                total_size = sum(item.file_size for item in archive.infolist())
                max_uncompressed = self.config.max_uncompressed_size_bytes
                if total_size > max_uncompressed:
                    raise WordValidationError("DOCX expanded size exceeds limit.")

                # additional zip bomb checks (compression ratio, file count)
                if len(archive.infolist()) > self.config.max_zip_files:
                    raise InvalidDocxError(f"DOCX contains too many inner files (Max: {self.config.max_zip_files})")

                for item in archive.infolist():
                    if item.compress_size > 0:
                        ratio = item.file_size / item.compress_size
                        if ratio > self.config.max_compression_ratio:
                            raise InvalidDocxError(
                                f"Suspicious compression ratio ({ratio:.2f}) detected (Zip Bomb protection)"
                            )

        except BadZipFile as exc:
            logger.exception("word_invalid_archive", extra={"file": str(file_path)})
            raise InvalidDocxError("Invalid DOCX archive. File may be corrupted.") from exc

    def validate_docx_archive(self, path: Path) -> None:
        try:
            with ZipFile(path) as archive:
                names = archive.namelist()
                if "word/document.xml" not in names:
                    raise InvalidDocxError("Missing 'word/document.xml'. File is not a valid Word document.")

                files = archive.infolist()
                if len(files) > self.config.max_zip_files:
                    raise InvalidDocxError(f"DOCX contains too many inner files (Max: {self.config.max_zip_files})")

                total_uncompressed = 0
                for item in files:
                    total_uncompressed += item.file_size
                    if item.compress_size > 0:
                        ratio = item.file_size / item.compress_size
                        if ratio > self.config.max_compression_ratio:
                            raise InvalidDocxError(
                                f"Suspicious compression ratio ({ratio:.2f}) detected (Zip Bomb protection)"
                            )

                if total_uncompressed > self.config.max_uncompressed_size_bytes:
                    raise InvalidDocxError("DOCX uncompressed size exceeds maximum allowed limit")

            logger.debug("docx_structure_validated", extra={"inner_files_count": len(files)})

        except BadZipFile:
            raise InvalidDocxError("File is not a valid ZIP/DOCX archive (Corrupted)")
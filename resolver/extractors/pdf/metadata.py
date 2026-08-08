# extractors/pdf/metadata.py
from pypdf import PdfReader

from core.models import PDFMetadata


class PDFMetadataExtractor:
    @staticmethod
    def extract(reader: PdfReader, filename: str) -> PDFMetadata:
        metadata = reader.metadata or {}
        return PDFMetadata(
            filename=filename,
            title=metadata.get("/Title"),
            author=metadata.get("/Author"),
            subject=metadata.get("/Subject"),
            creator=metadata.get("/Creator"),
            producer=metadata.get("/Producer"),
            creation_date=metadata.get("/CreationDate"),
            modification_date=metadata.get("/ModDate")
        )
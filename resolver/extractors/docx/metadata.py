# extractors/docx/metadata.py
from pathlib import Path
from typing import Optional

from docx import Document
from docx.document import Document as WordDocument

from core.models import WordMetadata


class WordMetadataExtractor:
    @staticmethod
    def extract(doc: WordDocument, file_path: Path) -> WordMetadata:
        properties = doc.core_properties
        creator_val = getattr(properties, 'creator', None)

        return WordMetadata(
            filename=file_path.name,
            title=properties.title,
            author=properties.author,
            subject=properties.subject,
            creator=creator_val,
            last_modified_by=properties.last_modified_by,
            revision=str(properties.revision) if properties.revision else None,
            created=properties.created.isoformat() if properties.created else None,
            modified=properties.modified.isoformat() if properties.modified else None
        )
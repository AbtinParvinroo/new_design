# extractors/docx/__init__.py
from .resolver import WordResolver
from .metadata import WordMetadataExtractor
from .archive import WordArchiveHandler
from .elements import WordElementExtractor
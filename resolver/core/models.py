# core/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass(frozen=True)
class FileValidatorConfig:
    max_file_size_mb: int = 5
    max_zip_files: int = 1000
    max_uncompressed_size_mb: int = 100
    max_compression_ratio: int = 100

    max_file_size_bytes: int = field(init=False)
    max_uncompressed_size_bytes: int = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'max_file_size_bytes', self.max_file_size_mb * 1024 * 1024)
        object.__setattr__(self, 'max_uncompressed_size_bytes', self.max_uncompressed_size_mb * 1024 * 1024)

@dataclass
class FileValidationResult:
    valid: bool
    filename: str
    file_type: Optional[str] = None
    size_mb: float = 0.0
    validation_time: float = 0.0
    validation_stage: str = "initialization"
    failure_reason: Optional[str] = None

@dataclass(frozen=True, slots=True)
class WordResolverConfig:
    max_text_length: int = 500_000
    max_compressed_size_mb: int = 50
    max_uncompressed_size_mb: int = 100
    normalize_unicode: bool = True
    normalize_whitespace: bool = True
    keep_empty_paragraphs: bool = False


@dataclass(frozen=True, slots=True)
class WordMetadata:
    filename: str
    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    creator: Optional[str]
    last_modified_by: Optional[str]
    revision: Optional[str]
    created: Optional[str]
    modified: Optional[str]

@dataclass(frozen=True, slots=True)
class WordExtractionResult:
    text: str
    total_chars: int
    truncated: bool
    extraction_time: float
    paragraph_count: int
    non_empty_paragraph_count: int
    table_count: int
    textbox_count: int
    metadata: WordMetadata
    health_status: str
    success: bool

@dataclass(frozen=True, slots=True)
class PDFResolverConfig:
    max_pages: int = 1_000
    max_text_length: int = 500_000
    extraction_mode: str = "layout"
    normalize_unicode: bool = True
    normalize_whitespace: bool = True
    keep_empty_pages: bool = False

@dataclass(frozen=True, slots=True)
class PDFMetadata:
    filename: str
    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    modification_date: Optional[str]

@dataclass(frozen=True, slots=True)
class PDFExtractionResult:
    text: str
    total_chars: int
    page_count: int
    truncated: bool
    ocr_required: bool
    failed_pages: List[int]
    metadata: PDFMetadata
    extraction_time: float

@dataclass(slots=True, frozen=True)
class PostProcessorConfig:
    max_text_length: int = 2_000_000
    regex_timeout: float = 2.0
    normalization_form: str = "NFKC"
    pipeline_stages: tuple[str, ...] = (
        "normalize_unicode",
        "remove_headers",
        "remove_page_numbers",
        "fix_ocr_errors",
        "fill_broken_paragraphs",
        "normalize_whitespace",
        "remove_empty_lines"
    )
    page_patterns: tuple[str, ...] = (
        r"(?m)^\s*\d+\s*/\s*\d+\s*$",
        r"(?m)^\s*[-–]*\s*\d+\s*[-–]*\s*$",
        r"(?m)^\s*page\s+\d+\s*$",
        r"(?m)^\s*\d+\s+of\s+\d+\s*$"
    )
    header_footer_patterns: tuple[str, ...] = ()
    bullet_pattern: str = r"^(\-|\*|•|\d+\.|[الف-ی]\.)\s+"
    ocr_patterns_en: dict[str, str] = field(default_factory=lambda: {
        "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"
    })
    ocr_patterns_fa: dict[str, str] = field(default_factory=lambda: {
        "ي": "ی", "ك": "ک", "ے": "ی", "ة": "ه"
    })
    section_keywords: dict[str, list[str]] = field(default_factory=lambda: {
        "work": ["work experience", "employment", "سوابق کاری", "تجربه کاری"],
        "education": ["education", "تحصیلات"],
        "skills": ["skills", "technical skills", "مهارت‌ها"],
        "certificates": ["certificates", "certifications", "گواهینامه‌ها"]
    })

@dataclass
class PostProcessingStats:
    unicode_changes: int = 0
    headers_removed: int = 0
    page_numbers_removed: int = 0
    ocr_replacements: int = 0
    paragraph_merges: int = 0
    empty_lines_removed: int = 0
    whitespace_normalized: int = 0
    input_lines: int = 0
    output_lines: int = 0
    text_reduction_ratio: float = 0.0
    sections_found: int = 0
    detected_language: str = "en"

@dataclass
class PostProcessingResult:
    text: str
    processing_time: float
    stats: PostProcessingStats
    sections: dict[str, str]
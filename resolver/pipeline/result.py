# pipeline/result.py
from dataclasses import dataclass
from typing import Optional, Union
from resolver.core.models import FileValidationResult, WordExtractionResult, PDFExtractionResult, PostProcessingResult

@dataclass
class PipelineResult:
    validation: Optional[FileValidationResult] = None
    extraction: Optional[Union[WordExtractionResult, PDFExtractionResult]] = None
    post_processing: Optional[PostProcessingResult] = None
    success: bool = False
    error: Optional[str] = None
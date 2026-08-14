# pipeline/document_pipeline.py
import logging
from pathlib import Path
from typing import Optional, Union
from resolver.core.models import (
    FileValidatorConfig,
    WordResolverConfig,
    PDFResolverConfig,
    PostProcessorConfig
)
from resolver.validators.file_validator import FileValidator
from resolver.extractors.pdf import PDFResolver
from resolver.extractors.docx import WordResolver
from resolver.processors.post_processor import PostProcessor
from resolver.pipeline.result import PipelineResult

logger = logging.getLogger(__name__)

class DocumentPipeline:
    def __init__(
        self,
        file_validator_config: Optional[FileValidatorConfig] = None,
        word_resolver_config: Optional[WordResolverConfig] = None,
        pdf_resolver_config: Optional[PDFResolverConfig] = None,
        post_processor_config: Optional[PostProcessorConfig] = None,
    ):
        self.file_validator = FileValidator(file_validator_config or FileValidatorConfig())
        self.word_resolver_config = word_resolver_config or WordResolverConfig()
        self.pdf_resolver_config = pdf_resolver_config or PDFResolverConfig()
        self.post_processor = PostProcessor(post_processor_config or PostProcessorConfig())

    def process(self, file_path: str) -> PipelineResult:
        result = PipelineResult()
        path = Path(file_path)

        # 1. Validate
        validation_result = self.file_validator.validate(str(path))
        result.validation = validation_result
        if not validation_result.valid:
            result.success = False
            result.error = f"Validation failed: {validation_result.failure_reason}"
            return result

        # 2. Extract
        file_type = validation_result.file_type
        try:
            if file_type == "pdf":
                with PDFResolver(path, config=self.pdf_resolver_config) as resolver:
                    extraction_result = resolver.extract()
                    result.extraction = extraction_result
                    raw_text = extraction_result.text
            elif file_type == "docx":
                with WordResolver(path, config=self.word_resolver_config) as resolver:
                    extraction_result = resolver.extract()
                    result.extraction = extraction_result
                    raw_text = extraction_result.text
            else:
                result.success = False
                result.error = f"Unsupported file type: {file_type}"
                return result
        except Exception as e:
            result.success = False
            result.error = f"Extraction failed: {str(e)}"
            return result

        # 3. Post-process
        try:
            post_result = self.post_processor.process(raw_text)
            result.post_processing = post_result
        except Exception as e:
            result.success = False
            result.error = f"Post-processing failed: {str(e)}"
            return result

        result.success = True
        return result
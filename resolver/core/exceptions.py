# core/exceptions.py

# FileValidator exceptions
class FileValidatorError(Exception):
    pass

class FileValidationError(FileValidatorError):
    pass

class InvalidFileTypeError(FileValidatorError):
    pass

class InvalidDocxError(FileValidatorError):
    pass

class InvalidPdfError(FileValidatorError):
    pass

# WordResolver exceptions
class WordResolverError(Exception):
    pass

class WordValidationError(WordResolverError):
    pass

class WordExtractionError(WordResolverError):
    pass

# PDFResolver exceptions
class PDFResolverError(Exception):
    pass

class InvalidPDFError(PDFResolverError):
    pass

class EncryptedPDFError(PDFResolverError):
    pass

class PDFValidationError(PDFResolverError):
    pass

class PDFExtractionError(PDFResolverError):
    pass

# PostProcessor exceptions
class PostProcessorError(Exception):
    pass

class ValidationError(PostProcessorError):
    pass

class ProcessingError(PostProcessorError):
    pass

class SectionExtractionError(PostProcessorError):
    pass
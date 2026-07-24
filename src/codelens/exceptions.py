class CodeLensError(Exception):
    """Base exception for all CodeLens errors."""
    pass

class EmbeddingError(CodeLensError):
    """Base exception for embedding API failures."""
    pass

class RateLimitError(EmbeddingError):
    """Raised when the embedding API returns a 429 Rate Limit error."""
    pass

class PayloadTooLargeError(EmbeddingError):
    """Raised when the payload exceeds the embedding API token limit."""
    pass

class StoreError(CodeLensError):
    """Raised for database or store-related failures."""
    pass

class IndexingError(CodeLensError):
    """Raised when indexing a file fails."""
    pass

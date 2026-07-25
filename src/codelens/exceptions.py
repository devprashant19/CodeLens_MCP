class CodeLensError(Exception):
    """Base exception for all CodeLens errors."""

class EmbeddingError(CodeLensError):
    """Base exception for embedding API failures."""

class RateLimitError(EmbeddingError):
    """Raised when the embedding API returns a 429 Rate Limit error."""

class PayloadTooLargeError(EmbeddingError):
    """Raised when the payload exceeds the embedding API token limit."""

class StoreError(CodeLensError):
    """Raised for database or store-related failures."""

class IndexingError(CodeLensError):
    """Raised when indexing a file fails."""

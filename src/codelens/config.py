import os
from dataclasses import dataclass


@dataclass
class Config:
    # Database
    db_path: str = "codelens.sqlite"

    # Embeddings
    embedding_model: str = "text-embedding-004"
    embedding_dim: int = 768
    embedding_batch_size: int = 50
    truncation_limit: int = 8000

    # Logging
    log_file: str = "logs/tool_calls.jsonl"
    log_max_bytes: int = 5 * 1024 * 1024
    log_backup_count: int = 3

    # MCP Tools
    tool_max_results: int = 20

    # API
    api_key: str | None = None

    def __post_init__(self):
        # Override defaults with environment variables
        self.db_path = os.environ.get("CODELENS_DB_PATH", self.db_path)
        self.embedding_model = os.environ.get("CODELENS_EMBEDDING_MODEL", self.embedding_model)
        self.embedding_dim = int(os.environ.get("CODELENS_EMBEDDING_DIM", self.embedding_dim))
        self.embedding_batch_size = int(os.environ.get("CODELENS_BATCH_SIZE", self.embedding_batch_size))
        self.truncation_limit = int(os.environ.get("CODELENS_TRUNCATION_LIMIT", self.truncation_limit))
        self.log_file = os.environ.get("CODELENS_LOG_FILE", self.log_file)
        self.log_max_bytes = int(os.environ.get("CODELENS_LOG_MAX_BYTES", self.log_max_bytes))
        self.log_backup_count = int(os.environ.get("CODELENS_LOG_BACKUP_COUNT", self.log_backup_count))
        self.tool_max_results = int(os.environ.get("CODELENS_TOOL_MAX_RESULTS", self.tool_max_results))

        # GEMINI_API_KEY could be already passed in, if not, pull from env
        if not self.api_key:
            self.api_key = os.environ.get("GEMINI_API_KEY")

        # Validation
        if not self.db_path:
            raise ValueError("CODELENS_DB_PATH cannot be empty")
        if self.embedding_dim <= 0:
            raise ValueError(f"Invalid embedding dimension: {self.embedding_dim}")
        if self.truncation_limit <= 0:
            raise ValueError(f"Invalid truncation limit: {self.truncation_limit}")
        if self.embedding_batch_size <= 0:
            raise ValueError(f"Invalid batch size: {self.embedding_batch_size}")

config = Config()

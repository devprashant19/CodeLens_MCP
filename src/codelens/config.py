import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Database
    db_path: str = os.environ.get("CODELENS_DB_PATH", "codelens.sqlite")
    
    # Embeddings
    embedding_model: str = os.environ.get("CODELENS_EMBEDDING_MODEL", "text-embedding-004")
    embedding_dim: int = int(os.environ.get("CODELENS_EMBEDDING_DIM", "768"))
    embedding_batch_size: int = int(os.environ.get("CODELENS_BATCH_SIZE", "50"))
    truncation_limit: int = int(os.environ.get("CODELENS_TRUNCATION_LIMIT", "8000"))
    
    # Logging
    log_file: str = os.environ.get("CODELENS_LOG_FILE", "logs/tool_calls.jsonl")
    log_max_bytes: int = int(os.environ.get("CODELENS_LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    log_backup_count: int = int(os.environ.get("CODELENS_LOG_BACKUP_COUNT", "3"))
    
    # MCP Tools
    tool_max_results: int = int(os.environ.get("CODELENS_TOOL_MAX_RESULTS", "20"))
    
    # API
    api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")

config = Config()

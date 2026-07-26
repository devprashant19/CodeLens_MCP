# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed
- **Config (config.py):** Environment variable evaluation moved from module-load time to `__post_init__`, ensuring test environments with mocked env vars work correctly.
- **Server (server.py):** `Store` and `EmbeddingService` are now lazily initialized via `get_store()` and `get_embedding_service()` factory functions, eliminating side effects on import.
- **Observability (observability.py):** Log file handler creation is now deferred until the first tool call via `_setup_handler()`, preventing spurious `logs/` directory creation during tests.
- **Embeddings (embeddings.py):** Exception handling in the retry loop now uses proper exception chaining (`raise ... from e`) and explicitly surfaces `PayloadTooLargeError` on final retry exhaustion.
- **Analytics (analytics.py):** Timestamp parsing updated to handle timezone-aware datetime objects, fixing crashes on Python 3.11+ when comparing naive and aware datetimes.
- **Store (store.py):** SQL `IN`-clause for vector deletion now uses parameterized placeholders instead of f-string interpolation, closing a potential SQL injection vector. Trailing whitespace removed from all embedded SQL queries.
- **Models (models.py):** Introduced `SymbolLocation` base dataclass to reduce field duplication across `ChunkResult`, `SearchResult`, and `StructureEntry`.
- **Indexer (indexer.py):** `SUPPORTED_EXTENSIONS` is now imported from `chunker.py` as the single source of truth, eliminating logic drift between modules.

### Added
- **Typed exception hierarchy (exceptions.py):** `CodeLensError` base class with specific subclasses: `EmbeddingError`, `RateLimitError`, `PayloadTooLargeError`, `StoreError`, `IndexingError`.
- **PEP 561 compliance (py.typed):** Added marker file for downstream type checker compatibility.
- **Docker Compose (docker-compose.yml):** Added local development container orchestration alongside the existing Dockerfile.
- **Environment variable `CODELENS_LOG_LEVEL`:** Controls the application log level (default: `INFO`). Supports `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- **Pyright type checking:** Added `[tool.pyright]` configuration in `pyproject.toml` (standard mode) and a `type-check` job in the CI pipeline.
- **Ruff linting:** Added comprehensive `[tool.ruff]` configuration with curated rule sets (`E`, `F`, `I`, `W`, `C90`, `N`, `B`, `UP`, `SIM`).
- **Pytest configuration:** Added `[tool.pytest.ini_options]` in `pyproject.toml` for consistent test runner behavior.

### Fixed
- **CI pipeline (ci.yml):** Removed `continue-on-error: true` from Windows test jobs — failures are now enforced across all platforms. Added dedicated `type-check` job with Pyright.
- **Test fixtures (conftest.py):** Updated mocks to patch `get_store` and `get_embedding_service` factory functions instead of non-existent module-level variables.

---

## [0.1.0] - 2025-07-20

### Added
- **Core MCP Server:** Six tools exposed via the Model Context Protocol stdio transport:
  - `semantic_code_search` — Natural-language vector similarity search over the codebase.
  - `find_usages` — Exact-match symbol reference search across all indexed files.
  - `explain_function` — Returns a function's source code along with all call sites.
  - `exact_search` — Literal text search across all indexed code chunks.
  - `get_file_structure` — Outline of all symbols defined in a file with line numbers.
  - `get_repo_map` — List of every indexed file in the repository.
- **Tree-sitter Chunker:** Parses Python and JavaScript/TypeScript code into logical AST-level chunks (functions, classes, methods) instead of fixed-size text blocks, producing higher-quality embeddings.
- **Embedded Vector Store:** Integrates `sqlite-vec` directly into the application for zero-infrastructure cosine similarity search. Runs in WAL mode for concurrent read performance.
- **Embedding Integration:** Connects to the Gemini `text-embedding-004` model with configurable batch sizes, exponential backoff on rate limits, and automatic payload truncation on 400 errors.
- **CLI Indexer:** `codelens index /path` command with incremental file hashing (only re-embeds changed files) and `rich` progress bars for visual feedback.
- **Containerization:** Production-ready Dockerfile (Python 3.11-slim, non-root user, health check) and `.dockerignore` for portable deployments.
- **Testing & CI:** Comprehensive `pytest` suite with `pytest-cov` coverage reporting, automated via GitHub Actions across Ubuntu and Windows runners with Python 3.11 and 3.12.
- **Observability:** Structured rotating file logger that records tool name, input arguments, latency (ms), success/failure, and result count as JSON lines.
- **Analytics CLI:** `codelens-analytics` command for generating tool success rate and latency reports from the structured log file.
- **Evaluation Harness:** Self-contained script (`tests/eval_harness.py`) testing LLM tool selection and argument extraction accuracy across 26 natural-language queries (achieving 100% accuracy with Gemini 2.5 Flash).

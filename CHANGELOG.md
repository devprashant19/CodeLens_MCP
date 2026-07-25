# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Initial Release

### Added
- **Core MCP Server**: Exposes standard tools (`semantic_code_search`, `find_usages`, `explain_function`, `exact_search`, `get_file_structure`, `get_repo_map`) via the Model Context Protocol stdio transport.
- **Tree-sitter Chunker**: Intelligently chunks Python and JavaScript/TypeScript code by function and class boundaries instead of fixed text lengths for superior semantic accuracy.
- **Embedded Vector Store**: Integrates `sqlite-vec` directly into the application process for zero-infra cosine similarity searches, running in fast WAL mode.
- **Embedding Integration**: Connects to the Gemini `text-embedding-004` model to vectorize AST chunks.
- **CLI Indexer**: Provides a `codelens index /path` command with incremental file hashing and `rich` progress bars.
- **Containerization**: Includes a hardened Dockerfile and `.dockerignore` for portable, isolated deployments.
- **Testing & CI**: Comprehensive `pytest` suite with `pytest-cov`, automated via GitHub Actions across Ubuntu and Windows runners.
- **Observability**: Structured rotating file logging for tool execution latency, success rates, and operational warnings.
- **Analytics Tool**: An `analytics.py` script to generate success/latency reports over time.
- **Eval Harness**: A self-contained evaluation script testing the LLM client's tool selection and argument extraction accuracy (currently achieving 100% on 26 test cases).

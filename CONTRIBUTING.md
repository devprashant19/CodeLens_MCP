# Contributing to CodeLens MCP

Thank you for your interest in contributing to CodeLens MCP! This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Code Quality Standards](#code-quality-standards)
- [Testing](#testing)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Commit Convention](#commit-convention)
- [Architectural Constraints](#architectural-constraints)
- [Adding Language Support](#adding-language-support)

---

## Development Setup

### Prerequisites

| Requirement | Purpose |
|---|---|
| Python 3.11+ | Runtime and type annotations (`X \| Y` union syntax) |
| Gemini API key | Required for embedding generation during integration testing |
| Git | Version control |

> **Note:** C++ build tools are **not** required. CodeLens uses `tree-sitter-language-pack`, which ships pre-compiled binaries for all supported platforms.

### Clone and Install

```bash
git clone https://github.com/devprashant19/CodeLens_MCP.git
cd CodeLens_MCP
python -m venv venv
source venv/bin/activate        # Linux / macOS
# .\\venv\\Scripts\\activate      # Windows PowerShell
pip install -e ".[dev]"
```

The `[dev]` extra installs `pytest`, `pytest-cov`, and `ruff`.

### Environment Variables

Copy `.env.example` to `.env` and fill in your Gemini API key:

```dotenv
GEMINI_API_KEY=your_key_here
```

See the [README Environment Variables table](README.md#environment-variables) for the full list of configurable options.

---

## Project Architecture

```
src/codelens/
├── server.py          # MCP server — tool definitions, lazy service initialization
├── store.py           # SQLite + sqlite-vec — CRUD operations, vector search
├── chunker.py         # tree-sitter parser — produces function/class/method chunks
├── embeddings.py      # Gemini API wrapper — batched embedding with retry & truncation
├── indexer.py         # CLI — walks a repo, hashes files, indexes changed files
├── config.py          # Centralized Config dataclass with env-var overrides
├── models.py          # Data models — SymbolLocation hierarchy
├── exceptions.py      # Typed exception tree (CodeLensError → subtypes)
├── observability.py   # Structured JSON logging decorator for MCP tool calls
├── logging_config.py  # Application logging setup (console, configurable log level)
├── analytics.py       # CLI for generating tool success/latency reports
└── py.typed           # PEP 561 marker for downstream type checking
```

### Key Design Patterns

- **Lazy initialization:** `server.py` uses factory functions (`get_store()`, `get_embedding_service()`) to avoid side effects at import time. This keeps tests clean and makes the module safe to import without triggering database or API connections.
- **Typed exception hierarchy:** All errors derive from `CodeLensError`. Callers can catch specific subclasses (`RateLimitError`, `PayloadTooLargeError`, `StoreError`, `IndexingError`) or the base class for blanket handling.
- **Configurable via environment:** Every tunable parameter lives in the `Config` dataclass and is overridable via environment variables, evaluated at construction time (not at import time).

---

## Code Quality Standards

### Linting — Ruff

We use [Ruff](https://docs.astral.sh/ruff/) with a curated set of rule categories:

```bash
ruff check src/ tests/
```

**Enabled rule sets:** `E` (pycodestyle), `F` (pyflakes), `I` (isort), `W` (warnings), `C90` (mccabe complexity), `N` (naming), `B` (bugbear), `UP` (pyupgrade), `SIM` (simplify).

Configuration lives in `pyproject.toml` under `[tool.ruff]`.

### Type Checking — Pyright

We use [Pyright](https://github.com/microsoft/pyright) in `standard` mode for static type analysis:

```bash
pyright src/
```

The `src/codelens/py.typed` marker file signals PEP 561 compliance to downstream consumers and type checkers.

Configuration lives in `pyproject.toml` under `[tool.pyright]`.

### Code Style

- **Type annotations:** All public function signatures should include type annotations.
- **Docstrings:** All public classes, functions, and methods should have docstrings.
- **Import order:** Managed by Ruff's `isort` integration. Standard library → third-party → local.
- **Line length:** Soft limit of 100 characters (configured in Ruff, not enforced as a hard error).

---

## Testing

### Running Tests

```bash
# Full suite with coverage
pytest tests/ -v --tb=short --cov=src/codelens

# Run a specific test file
pytest tests/test_chunker.py -v

# Run a specific test
pytest tests/test_store.py::test_find_usages_excludes_definition -v
```

### Test Structure

| File | Coverage Area |
|---|---|
| `test_chunker.py` | tree-sitter parsing for Python and JavaScript, nested functions, decorators, empty/error files |
| `test_embeddings.py` | Batched embedding, 400-error truncation retry logic |
| `test_server.py` | MCP tool integration tests with mocked store and embedding service |
| `test_store.py` | SQLite CRUD operations, hash tracking, usage exclusion, fuzzy symbol lookup |
| `eval_harness.py` | End-to-end tool selection accuracy (requires `GEMINI_API_KEY`) |

### Writing Tests

- All test files go in the `tests/` directory and must be named `test_*.py`.
- Use the shared fixtures in `conftest.py` for database and mock setup.
- When testing MCP tools from `server.py`, mock `get_store` and `get_embedding_service` — **not** module-level variables.
- Tests must not produce side effects (no database files, no log directories, no network calls unless explicitly mocked).

### CI Pipeline

Every push and pull request triggers the GitHub Actions CI pipeline:

| Job | Matrix | Checks |
|---|---|---|
| `test` | Ubuntu × Windows, Python 3.11 × 3.12 | Ruff lint → Pytest with coverage |
| `type-check` | Ubuntu, Python 3.11 | Pyright static analysis |

All checks must pass before a PR can be merged.

---

## Pull Request Guidelines

1. **Branch from `main`:** Create a feature branch with a descriptive name:
   ```
   feat/add-go-support
   fix/vector-search-null-filter
   docs/update-readme-tools-table
   ```

2. **Keep it atomic:** Each PR should address exactly one concern. If you're fixing a bug and adding a feature, submit them as separate PRs.

3. **Add tests:** Every new feature must include tests. Every bug fix must include a regression test.

4. **Update documentation:** If your change affects user-facing behavior, update the relevant markdown files (`README.md`, `CHANGELOG.md`).

5. **Ensure CI passes:** Before requesting review, verify that linting, tests, and type checking all pass locally:
   ```bash
   ruff check src/ tests/
   pytest tests/ -v --tb=short --cov=src/codelens
   pyright src/
   ```

6. **Write a clear PR description:** Explain *what* changed, *why* it changed, and any trade-offs or follow-up work.

---

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/) for a clean, parseable history:

| Prefix | Usage |
|---|---|
| `feat:` | A new feature or capability |
| `fix:` | A bug fix |
| `docs:` | Documentation-only changes |
| `test:` | Adding or updating tests |
| `chore:` | Build config, CI, tooling, dependency updates |
| `refactor:` | Code restructuring with no behavior change |
| `perf:` | Performance improvements |

**Examples:**
```
feat(chunker): add Go language support
fix(store): handle NULL parent_symbol in vector search
docs: update README with Docker Compose instructions
test(server): add coverage for empty query edge case
chore(ci): add Python 3.13 to test matrix
```

---

## Architectural Constraints

When contributing, please respect these non-negotiable design decisions:

### No Heavy Databases
Do **not** introduce Postgres, Chroma, Pinecone, Weaviate, or any external database dependency. CodeLens relies exclusively on embedded `sqlite-vec` to guarantee zero infrastructure overhead for the end user. This is a core design principle.

### No Vendor-Specific Client Naming
Do **not** reference specific AI assistants (Claude, ChatGPT, Copilot, etc.) in code, comments, documentation, or commit messages. Use generic terms like **"the LLM client"**, **"an MCP client"**, or **"the AI assistant"**. CodeLens is client-agnostic by design.

### No Side Effects at Import Time
Modules must be safe to import without creating files, directories, database connections, or network requests. Use lazy initialization patterns (see `server.py` for the canonical example). This is critical for test isolation.

---

## Adding Language Support

To add support for a new programming language:

1. **Update `SUPPORTED_EXTENSIONS`** in `src/codelens/chunker.py`:
   ```python
   SUPPORTED_EXTENSIONS = {
       ".py": "python",
       ".js": "javascript",
       # Add your language:
       ".go": "go",
   }
   ```

2. **Verify tree-sitter grammar availability:** The language must be supported by `tree-sitter-language-pack`. Check their documentation for available grammars.

3. **Test the AST node types:** Tree-sitter uses different node type names per language. You may need to update the `_walk_tree` method in `Chunker` if the new language uses different node types for functions and classes (e.g., `func_declaration` instead of `function_definition`).

4. **Add tests:** Create test cases in `test_chunker.py` with sample source files for the new language, covering at least:
   - Basic function/class extraction
   - Nested definitions
   - Edge cases (empty files, syntax errors)

5. **Update documentation:** Add the new language to the supported languages list in `README.md`.

---

## Questions?

If you're unsure about anything, open a [GitHub Issue](https://github.com/devprashant19/CodeLens_MCP/issues) to discuss before starting work. We're happy to help!

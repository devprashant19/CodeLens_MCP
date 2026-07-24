# Contributing to CodeLens MCP

First off, thanks for taking the time to contribute! CodeLens MCP is designed to be a lightweight, zero-infra semantic search tool for the LLM client, and we welcome improvements.

## Development Setup

1. **Prerequisites**
   - Python 3.11+
   - A Gemini API key (for embedding generation)
   - C++ Build Tools (required on Windows for `tree-sitter` and `sqlite-vec` compilation)

2. **Clone and Install**
   ```bash
   git clone https://github.com/devprashant19/CodeLens_MCP.git
   cd CodeLens_MCP
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Environment Variables**
   Copy `.env.example` to `.env` and fill in your details.
   ```bash
   GEMINI_API_KEY=your_key_here
   ```

## Testing and Linting

We enforce strict quality checks on all pull requests.

- **Run tests (with coverage):**
  ```bash
  pytest tests/ -v --cov=src/codelens
  ```

- **Run linter:**
  ```bash
  ruff check src/ tests/
  ```

## Project Structure

- `src/codelens/chunker.py`: Uses `tree-sitter` to parse code into logical AST chunks (functions/classes).
- `src/codelens/store.py`: Manages the SQLite database, including the `sqlite-vec` virtual tables for vector search.
- `src/codelens/embeddings.py`: Wraps the Gemini API for generating vectors.
- `src/codelens/server.py`: The FastMCP entrypoint that exposes tools to the LLM client.

## Pull Request Guidelines

1. **Keep it atomic:** Each PR should do exactly one thing. If you're fixing a bug and adding a feature, split them.
2. **Add tests:** If you add a feature, add a test. If you fix a bug, add a test that catches it.
3. **Follow Conventional Commits:** Our commit history is structured. Please use prefixes like `feat:`, `fix:`, `docs:`, `test:`, or `chore:`.

## Known Constraints

When adding features, please respect these architectural constraints:
- **No Heavy Databases:** Do not introduce Postgres, Chroma, or Pinecone. We rely exclusively on embedded `sqlite-vec` to ensure zero infrastructure overhead for the end user.
- **Generic Client Naming:** Do not mention specific AI assistants (like Claude, ChatGPT, etc.) in documentation or comments. Use generic terms like "the LLM client" or "an MCP client."

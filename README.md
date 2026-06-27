# CodeLens MCP

CodeLens MCP is a local, repo-aware Model Context Protocol (MCP) server that empowers LLM clients (like Claude Desktop) to perform semantic searches and answer questions about your codebase accurately, avoiding hallucinations. By leveraging local tree-sitter parsing and the lightweight `sqlite-vec` vector store, CodeLens delivers high-precision semantic code retrieval with zero infrastructure overhead.

## Architecture

```mermaid
graph TD
    A[Codebase] -->|Indexed via tree-sitter| B(Chunker)
    B -->|Splits by function/class| C(Embeddings: Gemini text-embedding-004)
    C -->|Vector Data| D[(sqlite-vec Store)]
    E[LLM Client / Claude Desktop] -->|MCP stdio| F[CodeLens MCP Server]
    F <-->|Query| D
    F -->|semantic_code_search| E
    F -->|find_usages| E
    F -->|explain_function| E
```

## Setup & Installation

*(Detailed instructions to be filled out after implementation...)*

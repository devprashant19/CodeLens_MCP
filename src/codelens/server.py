import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from codelens.store import Store
from codelens.embeddings import EmbeddingService
from codelens.observability import log_tool_call

mcp = FastMCP("CodeLens MCP", dependencies=["mcp", "google-genai", "sqlite-vec"])

store = Store()
try:
    embedding_service = EmbeddingService()
except ValueError:
    # Allows the server to start, but semantic search will fail cleanly if API key is missing
    embedding_service = None

def format_chunk_result(chunk: dict) -> str:
    res = f"File: {chunk['file_path']} (Lines {chunk['start_line']}-{chunk['end_line']})\n"
    res += f"Symbol: {chunk['symbol_name']} ({chunk['symbol_type']})\n"
    if chunk.get('relevance_score'):
        res += f"Relevance: {chunk['relevance_score']:.3f}\n"
    res += f"Code:\n```\n{chunk['code_text']}\n```\n"
    return res

@mcp.tool()
@log_tool_call("semantic_code_search")
async def semantic_code_search(query: str, top_k: int = 5, file_filter: str = "") -> str:
    """
    Search the codebase using semantic vector search.
    Use this tool when you need to understand conceptual ideas, find how something works generally, 
    or look for features by description (e.g. "how does authentication work").
    Unlike exact text matching, this understands natural language queries.
    """
    if not embedding_service:
        return "Error: GEMINI_API_KEY is not set. Semantic search is disabled."
        
    try:
        # We need a synchronous-looking call since embed_chunks is sync, 
        # but technically we might want to run it in a threadpool in a real async environment.
        # For a local MCP server, running it directly is usually fine.
        embeddings = embedding_service.embed_chunks([query])
        if not embeddings:
            return "Failed to generate embedding for query."
            
        query_embedding = embeddings[0]
        results = store.vector_search(query_embedding, top_k=top_k, file_filter=file_filter if file_filter else None)
        
        if not results:
            return "No matching code found."
            
        formatted_results = [format_chunk_result(r) for r in results]
        return "\n---\n".join(formatted_results)
    except Exception as e:
        return f"Search failed: {str(e)}"

@mcp.tool()
@log_tool_call("find_usages")
async def find_usages(symbol_name: str) -> str:
    """
    Find all references and usages of a specific function, class, or variable name.
    Use this tool when you know the exact name of a symbol and want to see where else in the codebase it is called or referenced.
    This is an exact-match search, not a semantic search.
    """
    results = store.find_usages(symbol_name)
    if not results:
        return f"No usages found for '{symbol_name}'."
        
    formatted_results = [format_chunk_result(r) for r in results]
    return "\n---\n".join(formatted_results)

@mcp.tool()
@log_tool_call("explain_function")
async def explain_function(file_path: str, function_name: str) -> str:
    """
    Get the full context of a function to explain its role.
    This returns the function's own code plus chunks that call it, giving you surrounding context
    to understand how it fits into the broader system.
    Use this when you are asked to explain what a specific function does.
    """
    target = store.get_chunk_by_symbol(file_path, function_name)
    if not target:
        return f"Function '{function_name}' not found in {file_path}."
        
    usages = store.get_calls_to(function_name)
    
    response = "### Target Function\n"
    response += format_chunk_result(target)
    
    if usages:
        response += "\n### Used By\n"
        for usage in usages:
            response += format_chunk_result(usage) + "\n---\n"
            
    return response

if __name__ == "__main__":
    mcp.run()

import os
import json
from typing import List, Dict, Any
from google import genai
from google.genai import types

# Define our tools as Gemini tool schemas
semantic_search_schema = {
    "name": "semantic_code_search",
    "description": "Search the codebase using semantic vector search. Use this when you need to understand conceptual ideas, find how something works generally, or look for features by description (e.g. 'how does authentication work').",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The natural language query"},
            "top_k": {"type": "integer", "description": "Number of results to return"},
            "file_filter": {"type": "string", "description": "Optional file path filter"}
        },
        "required": ["query"]
    }
}

find_usages_schema = {
    "name": "find_usages",
    "description": "Find all references and usages of a specific function, class, or variable name. Use this tool when you know the exact name of a symbol and want to see where else in the codebase it is called or referenced. This is an exact-match search.",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol_name": {"type": "string", "description": "The exact name of the symbol"}
        },
        "required": ["symbol_name"]
    }
}

explain_function_schema = {
    "name": "explain_function",
    "description": "Get the full context of a function to explain its role. This returns the function's own code plus chunks that call it. Use this when you are asked to explain what a specific function does.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file containing the function"},
            "function_name": {"type": "string", "description": "Name of the function to explain"}
        },
        "required": ["file_path", "function_name"]
    }
}

# 20 Queries
EVAL_QUERIES = [
    {
        "query": "Where is the tree-sitter chunking logic implemented?",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["chunk", "tree-sitter"]
    },
    {
        "query": "How is the sqlite-vec extension loaded into the database connection?",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["sqlite-vec", "load_extension"]
    },
    {
        "query": "Find all places where the Chunker class is used.",
        "expected_tool": "find_usages",
        "expected_args_contain": ["Chunker"]
    },
    {
        "query": "Explain what the get_parser_for_ext function does in the chunker.",
        "expected_tool": "explain_function",
        "expected_args_contain": ["get_parser_for_ext"]
    },
    {
        "query": "How does the system handle rate limits from the Gemini embedding API?",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["rate limit", "429", "backoff"]
    },
    {
        "query": "Show me where the embedding vectors are inserted into the database.",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["insert", "vector"]
    },
    {
        "query": "Find references to the Store class.",
        "expected_tool": "find_usages",
        "expected_args_contain": ["Store"]
    },
    {
        "query": "Explain the semantic_code_search function in the server.",
        "expected_tool": "explain_function",
        "expected_args_contain": ["semantic_code_search"]
    },
    {
        "query": "How does incremental indexing skip unchanged files?",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["hash", "incremental", "skip"]
    },
    {
        "query": "Show usages of the log_tool_call decorator.",
        "expected_tool": "find_usages",
        "expected_args_contain": ["log_tool_call"]
    },
    {
        "query": "What does the _walk_tree method in Chunker do?",
        "expected_tool": "explain_function",
        "expected_args_contain": ["_walk_tree"]
    },
    {
        "query": "Where are the API keys loaded from the environment variables?",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["API_KEY", "env"]
    },
    {
        "query": "How are results formatted before being returned to the MCP client?",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["format", "result"]
    },
    {
        "query": "Find all usages of get_file_hash.",
        "expected_tool": "find_usages",
        "expected_args_contain": ["get_file_hash"]
    },
    {
        "query": "Explain the _embed_with_retry method.",
        "expected_tool": "explain_function",
        "expected_args_contain": ["_embed_with_retry"]
    },
    {
        "query": "Where is the FastMCP server instantiated?",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["FastMCP", "server"]
    },
    {
        "query": "Find usages of the delete_file_chunks method.",
        "expected_tool": "find_usages",
        "expected_args_contain": ["delete_file_chunks"]
    },
    {
        "query": "Explain what the vector_search method in the Store class does.",
        "expected_tool": "explain_function",
        "expected_args_contain": ["vector_search"]
    },
    {
        "query": "How do we map file extensions to tree-sitter language identifiers?",
        "expected_tool": "semantic_code_search",
        "expected_args_contain": ["extension", "language", "map"]
    },
    {
        "query": "Find usages of EmbeddingService.",
        "expected_tool": "find_usages",
        "expected_args_contain": ["EmbeddingService"]
    }
]

def run_eval():
    print("Starting Eval Harness...")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
                        
    if not api_key:
        print("GEMINI_API_KEY is not set. Cannot run evaluation.")
        return

    client = genai.Client(api_key=api_key)
    
    # We define the tools for the Gemini model
    # Note: genai SDK expects FunctionDeclaration objects, but we can pass dicts in some versions,
    # or construct them using types.FunctionDeclaration. We'll use the types module for safety.
    
    tool_defs = [
        types.FunctionDeclaration(**semantic_search_schema),
        types.FunctionDeclaration(**find_usages_schema),
        types.FunctionDeclaration(**explain_function_schema)
    ]
    gemini_tools = [types.Tool(function_declarations=tool_defs)]

    results = []
    correct_tools = 0
    correct_args = 0

    for idx, eval_item in enumerate(EVAL_QUERIES):
        query = eval_item["query"]
        expected_tool = eval_item["expected_tool"]
        expected_args_keywords = eval_item["expected_args_contain"]
        
        print(f"[{idx+1}/20] Evaluating: {query}")
        
        try:
            # We sleep for 12 seconds between requests to avoid the Gemini Free Tier rate limit 
            # of 5 requests per minute (which allows ~1 request every 12 seconds).
            import time
            time.sleep(12)
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=query,
                config=types.GenerateContentConfig(
                    tools=gemini_tools,
                    temperature=0.0
                )
            )
            
            tool_called = None
            args = {}
            if response.function_calls:
                fc = response.function_calls[0]
                tool_called = fc.name
                args = fc.args
                
            tool_match = (tool_called == expected_tool)
            
            # Check args
            args_str = json.dumps(args).lower()
            args_match = any(kw.lower() in args_str for kw in expected_args_keywords) if tool_called else False
            
            if tool_match:
                correct_tools += 1
            if args_match:
                correct_args += 1
                
            results.append({
                "query": query,
                "expected": expected_tool,
                "actual": tool_called or "None",
                "tool_pass": tool_match,
                "args_pass": args_match
            })
            
        except Exception as e:
            print(f"Error during eval query: {e}")
            results.append({
                "query": query,
                "expected": expected_tool,
                "actual": "ERROR",
                "tool_pass": False,
                "args_pass": False
            })

    # Print Markdown Table
    print("\n## Eval Results\n")
    print("| Query | Expected Tool | Actual Tool | Tool Pass | Args Pass |")
    print("|-------|---------------|-------------|-----------|-----------|")
    for r in results:
        t_pass = "PASS" if r["tool_pass"] else "FAIL"
        a_pass = "PASS" if r["args_pass"] else "FAIL"
        print(f"| {r['query']} | {r['expected']} | {r['actual']} | {t_pass} | {a_pass} |")
        
    print(f"\n**Tool Selection Accuracy:** {correct_tools}/{len(EVAL_QUERIES)} ({(correct_tools/len(EVAL_QUERIES))*100:.1f}%)")
    print(f"**Argument Extraction Accuracy:** {correct_args}/{len(EVAL_QUERIES)} ({(correct_args/len(EVAL_QUERIES))*100:.1f}%)")

if __name__ == "__main__":
    run_eval()

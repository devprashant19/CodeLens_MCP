import os
from dataclasses import dataclass
from typing import List, Optional
from tree_sitter_languages import get_language, get_parser
from tree_sitter import Node

@dataclass
class Chunk:
    file_path: str
    start_line: int
    end_line: int
    code_text: str
    symbol_name: str
    symbol_type: str
    parent_symbol: Optional[str]

# Mapping of file extensions to tree-sitter language names
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}

class Chunker:
    def __init__(self):
        # We load parsers dynamically to avoid loading them all at startup
        self.parsers = {}

    def get_parser_for_ext(self, ext: str):
        if ext not in SUPPORTED_EXTENSIONS:
            return None
        
        lang_name = SUPPORTED_EXTENSIONS[ext]
        if lang_name not in self.parsers:
            language = get_language(lang_name)
            parser = get_parser(lang_name)
            self.parsers[lang_name] = parser
        return self.parsers[lang_name]

    def chunk_file(self, file_path: str) -> List[Chunk]:
        """
        Parses a file and returns a list of Chunks.
        If a file contains syntax errors, we attempt to parse it anyway (tree-sitter is resilient),
        and if it fails completely or the file is empty/invalid, we just skip it.
        """
        _, ext = os.path.splitext(file_path)
        parser = self.get_parser_for_ext(ext)
        if not parser:
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            # If we can't read the file (e.g. binary, permission error), skip it
            return []

        if not content.strip():
            return []

        tree = parser.parse(content.encode("utf-8"))
        if not tree or not tree.root_node:
            return []
            
        chunks = []
        self._walk_tree(tree.root_node, content, file_path, None, chunks)
        
        # If no functions/classes were found, we might want to chunk the whole file as "module",
        # but the requirements specifically said "chunk by function/class, not fixed-size text blocks".
        # We'll return what we found.
        return chunks

    def _walk_tree(self, node: Node, source: str, file_path: str, parent_symbol: Optional[str], chunks: List[Chunk]):
        symbol_name = None
        symbol_type = None

        # Determine if this node is a class, function, or method
        if node.type in ("class_definition", "class_declaration"):
            symbol_type = "class"
            symbol_name = self._get_node_name(node, source)
        elif node.type in ("function_definition", "function_declaration", "method_definition", "arrow_function"):
            symbol_type = "method" if node.type == "method_definition" else "function"
            symbol_name = self._get_node_name(node, source)
            # If arrow function doesn't have a name in the node itself, maybe it's assigned to a variable
            if not symbol_name and node.parent and node.parent.type == "variable_declarator":
                symbol_name = self._get_node_name(node.parent, source)

        # If it's a valid chunkable block, add it
        if symbol_name and symbol_type:
            # Get the exact text of the node
            # Start and end lines are 0-indexed in tree-sitter, we add 1 for standard 1-based lines
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            code_text = source[node.start_byte:node.end_byte]
            
            chunks.append(Chunk(
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                code_text=code_text,
                symbol_name=symbol_name,
                symbol_type=symbol_type,
                parent_symbol=parent_symbol
            ))

            # The new parent for children is this symbol
            parent_symbol = symbol_name

        # Recursively walk children
        for child in node.children:
            self._walk_tree(child, source, file_path, parent_symbol, chunks)

    def _get_node_name(self, node: Node, source: str) -> Optional[str]:
        # Typically, the name is an identifier child
        # tree-sitter python/js puts the name as a named child often called 'name'
        name_node = node.child_by_field_name("name")
        if name_node:
            return source[name_node.start_byte:name_node.end_byte]
            
        # Fallback if no field name: search for identifier children
        for child in node.children:
            if child.type in ("identifier", "property_identifier"):
                return source[child.start_byte:child.end_byte]
        return None

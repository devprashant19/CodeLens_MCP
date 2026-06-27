import os
import pytest
import tempfile
from codelens.chunker import Chunker

@pytest.fixture
def chunker():
    return Chunker()

def create_temp_file(content: str, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix, text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def test_chunker_basic_python(chunker):
    code = """
def hello_world():
    print("Hello")

class MyClass:
    def method_one(self):
        pass
"""
    path = create_temp_file(code, ".py")
    try:
        chunks = chunker.chunk_file(path)
        assert len(chunks) == 3
        
        # We should find hello_world, MyClass, and method_one
        names = {c.symbol_name for c in chunks}
        assert names == {"hello_world", "MyClass", "method_one"}
        
        # Check parents
        method_chunk = next(c for c in chunks if c.symbol_name == "method_one")
        assert method_chunk.parent_symbol == "MyClass"
        assert method_chunk.symbol_type == "function" # Or method, depending on tree-sitter
    finally:
        os.remove(path)

def test_chunker_nested_functions(chunker):
    code = """
def outer():
    def inner():
        pass
    return inner
"""
    path = create_temp_file(code, ".py")
    try:
        chunks = chunker.chunk_file(path)
        assert len(chunks) == 2
        inner = next(c for c in chunks if c.symbol_name == "inner")
        assert inner.parent_symbol == "outer"
    finally:
        os.remove(path)

def test_chunker_decorators(chunker):
    code = """
@pytest.fixture
def chunker_fixture():
    pass
"""
    path = create_temp_file(code, ".py")
    try:
        chunks = chunker.chunk_file(path)
        assert len(chunks) == 1
        assert chunks[0].symbol_name == "chunker_fixture"
        assert "@pytest.fixture" in chunks[0].code_text
    finally:
        os.remove(path)

def test_chunker_empty_and_syntax_error(chunker):
    path_empty = create_temp_file("", ".py")
    path_error = create_temp_file("def broken_syntax( {", ".py")
    try:
        assert len(chunker.chunk_file(path_empty)) == 0
        
        # Syntax error file should not crash, it might just return 0 chunks
        chunks = chunker.chunk_file(path_error)
        assert isinstance(chunks, list)
    finally:
        os.remove(path_empty)
        os.remove(path_error)

def test_chunker_js(chunker):
    code = """
class User {
  constructor() {}
  login() {}
}

function process() {
    const x = () => {};
}
"""
    path = create_temp_file(code, ".js")
    try:
        chunks = chunker.chunk_file(path)
        names = {c.symbol_name for c in chunks if c.symbol_name}
        assert "User" in names
        assert "login" in names
        assert "process" in names
    finally:
        os.remove(path)

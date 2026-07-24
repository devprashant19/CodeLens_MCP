import pytest
from unittest.mock import patch, MagicMock

# Important: we mock the genai and sqlite_vec before importing server
# so it doesn't crash if they are not fully configured in test env

@pytest.fixture
def mock_store():
    with patch('codelens.server.store') as mock:
        yield mock

@pytest.fixture
def mock_embeddings():
    with patch('codelens.server.embedding_service') as mock:
        yield mock

def test_semantic_code_search(mock_store, mock_embeddings):
    from codelens.server import semantic_code_search
    
    mock_embeddings.embed_chunks.return_value = [[0.1, 0.2, 0.3]]
    mock_store.vector_search.return_value = [
        {
            "file_path": "test.py",
            "start_line": 1,
            "end_line": 5,
            "code_text": "def test(): pass",
            "symbol_name": "test",
            "symbol_type": "function",
            "relevance_score": 0.95
        }
    ]
    
    result = semantic_code_search("how to test")
    assert "File: test.py" in result
    assert "def test(): pass" in result
    assert "0.95" in result

def test_find_usages(mock_store):
    from codelens.server import find_usages
    
    mock_store.find_usages.return_value = [
        {
            "file_path": "caller.py",
            "start_line": 10,
            "end_line": 15,
            "code_text": "def call_test():\n    test()",
            "symbol_name": "call_test",
            "symbol_type": "function",
        }
    ]
    
    result = find_usages("test")
    assert "caller.py" in result
    assert "call_test" in result

def test_explain_function(mock_store):
    from codelens.server import explain_function
    
    mock_store.get_chunk_by_symbol.return_value = {
        "file_path": "test.py",
        "start_line": 1,
        "end_line": 5,
        "code_text": "def test(): pass",
        "symbol_name": "test",
        "symbol_type": "function",
    }
    mock_store.get_calls_to.return_value = []
    
    result = explain_function("test.py", "test")
    assert "Target Function" in result
    assert "def test(): pass" in result

def test_exact_search(mock_store):
    from codelens.server import exact_search
    mock_store.exact_search.return_value = [
        {
            "file_path": "test.py",
            "start_line": 1,
            "end_line": 2,
            "code_text": "foo = 42",
            "symbol_name": "foo",
            "symbol_type": "variable",
        }
    ]
    
    result = exact_search("foo = 42")
    assert "foo = 42" in result

def test_get_file_structure(mock_store):
    from codelens.server import get_file_structure
    mock_store.get_file_structure.return_value = [
        {
            "start_line": 1,
            "end_line": 5,
            "symbol_name": "MyClass",
            "symbol_type": "class",
            "parent_symbol": None
        }
    ]
    result = get_file_structure("test.py")
    assert "MyClass" in result
    assert "Line 1-5" in result

def test_get_repo_map(mock_store):
    from codelens.server import get_repo_map
    mock_store.get_repo_map.return_value = ["file1.py", "file2.py"]
    result = get_repo_map()
    assert "file1.py" in result
    assert "file2.py" in result

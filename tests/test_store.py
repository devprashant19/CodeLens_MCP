from codelens.chunker import Chunk


def test_insert_and_get_hashes(store):
    chunks = [
        Chunk("test.py", 1, 5, "def foo(): pass", "foo", "function", None)
    ]
    embeddings = [[0.1] * 768]
    
    store.insert_chunks(chunks, embeddings, "hash123")
    
    hashes = store.get_file_hashes()
    assert "test.py" in hashes
    assert hashes["test.py"] == "hash123"

def test_find_usages_excludes_definition(store):
    chunks = [
        Chunk("def.py", 1, 5, "def my_func(): pass", "my_func", "function", None),
        Chunk("call.py", 1, 5, "def caller(): my_func()", "caller", "function", None)
    ]
    embeddings = [[0.1] * 768, [0.2] * 768]
    store.insert_chunks(chunks, embeddings, "hash")
    
    usages = store.find_usages("my_func")
    assert len(usages) == 1
    assert usages[0].file_path == "call.py"

def test_delete_file_chunks(store):
    chunks = [
        Chunk("test.py", 1, 5, "def foo(): pass", "foo", "function", None)
    ]
    store.insert_chunks(chunks, [[0.1] * 768], "hash")
    
    assert len(store.get_file_hashes()) == 1
    store.delete_file_chunks("test.py")
    assert len(store.get_file_hashes()) == 0

def test_get_chunk_by_symbol_fuzzy(store):
    chunks = [
        Chunk("test.py", 1, 5, "def foo(): pass", "MyClass.foo", "function", "MyClass")
    ]
    store.insert_chunks(chunks, [[0.1] * 768], "hash")
    
    # Should match exact
    assert store.get_chunk_by_symbol("test.py", "MyClass.foo") is not None
    # Should match fuzzy (suffix)
    assert store.get_chunk_by_symbol("test.py", "foo") is not None
    # Should not match completely different
    assert store.get_chunk_by_symbol("test.py", "bar") is None

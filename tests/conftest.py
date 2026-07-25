from unittest.mock import patch

import pytest

from codelens.store import Store


@pytest.fixture
def store(tmp_path):
    """Provides a thread-safe Store instance with a temporary database file."""
    db_path = tmp_path / "test_codelens.sqlite"
    test_store = Store(db_path=str(db_path))

    yield test_store

    # Proper teardown
    test_store.close()

    # We do not need to explicitly os.remove since tmp_path cleans itself up

@pytest.fixture
def mock_genai_client():
    """Provides a mocked Gemini client."""
    with patch('codelens.embeddings.genai.Client') as mock_client:
        yield mock_client.return_value

@pytest.fixture
def mock_store_service():
    """Provides a mocked store for higher-level tests."""
    with patch('codelens.server.store') as mock:
        yield mock

@pytest.fixture
def mock_embeddings():
    """Provides a mocked embedding service for higher-level tests."""
    with patch('codelens.server.embedding_service') as mock:
        yield mock

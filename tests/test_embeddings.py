from unittest.mock import MagicMock

from codelens.embeddings import EmbeddingService


def test_embed_chunks_batching(mock_genai_client):
    service = EmbeddingService(api_key="fake")
    service.batch_size = 2  # Small batch size for testing

    texts = ["a", "b", "c", "d", "e"]

    # Mock response
    mock_response = MagicMock()
    # We will just return 2 items per call, then 1 item
    mock_emb = MagicMock()
    mock_emb.values = [0.1, 0.2]
    mock_response.embeddings = [mock_emb, mock_emb]

    mock_genai_client.models.embed_content.return_value = mock_response

    result = service.embed_chunks(texts)

    # We expect 3 calls (2 + 2 + 1)
    assert mock_genai_client.models.embed_content.call_count == 3
    assert len(result) == 6 # 3 calls * 2 returned embeddings (based on our naive mock)

def test_embed_chunks_400_truncation(mock_genai_client):
    service = EmbeddingService(api_key="fake")

    # Create an exception that contains "400"
    error = Exception("400 Bad Request: payload too large")

    mock_response_success = MagicMock()
    mock_emb = MagicMock()
    mock_emb.values = [1.0]
    mock_response_success.embeddings = [mock_emb]

    # Fail first time, succeed second time
    mock_genai_client.models.embed_content.side_effect = [error, mock_response_success]

    # Pass a huge text
    huge_text = "A" * 10000
    result = service._embed_with_retry([huge_text])

    assert len(result) == 1
    # Check that the second call used truncated text (8000 chars)
    call_args = mock_genai_client.models.embed_content.call_args_list[1]
    assert len(call_args.kwargs['contents'][0]) == 8000

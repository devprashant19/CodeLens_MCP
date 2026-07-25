import time

from google import genai

from codelens.config import config
from codelens.exceptions import EmbeddingError, RateLimitError
from codelens.logging_config import get_logger

logger = get_logger("embeddings")

class EmbeddingService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = config.embedding_model
        self.batch_size = config.embedding_batch_size

    def embed_chunks(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts using the Gemini API.
        Handles batching and basic retry logic on rate limits (429).
        """
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = self._embed_with_retry(batch)
            all_embeddings.extend(embeddings)
            
        return all_embeddings

    def _embed_with_retry(self, texts: list[str], max_retries: int = 5) -> list[list[float]]:
        delay = 2
        for attempt in range(max_retries):
            try:
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=texts
                )
                # response.embeddings is a list of embeddings
                return [emb.values for emb in response.embeddings]
            except Exception as e:
                # Basic check for rate limit or quota exceeded
                if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
                    if attempt == max_retries - 1:
                        raise RateLimitError(f"Rate limited by Gemini API: {e}")
                    logger.warning(f"Rate limited by Gemini API. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                elif "400" in str(e) or "invalid argument" in str(e).lower():
                    # Likely a payload too large / token limit error.
                    # We can try to truncate the texts to a safe limit.
                    logger.warning("400 Bad Request encountered (likely token limit). Truncating chunks...")
                    texts = [t[:config.truncation_limit] for t in texts]
                else:
                    # If it's a different error, raise immediately
                    raise EmbeddingError(f"Embedding API failed: {e}")
        raise EmbeddingError("Failed to embed chunks after max retries")

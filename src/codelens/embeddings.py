import os
import time
from typing import List, Optional
from google import genai

class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "text-embedding-004"
        self.batch_size = 50

    def embed_chunks(self, texts: List[str]) -> List[List[float]]:
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

    def _embed_with_retry(self, texts: List[str], max_retries: int = 5) -> List[List[float]]:
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
                        raise e
                    print(f"Rate limited by Gemini API. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                elif "400" in str(e) or "invalid argument" in str(e).lower():
                    # Likely a payload too large / token limit error.
                    # We can try to truncate the texts to a safe limit.
                    # Gemini text-embedding-004 limit is around 2048 tokens ~ 8000 chars.
                    # We'll do a naive truncation if it failed with 400.
                    print("400 Bad Request encountered (likely token limit). Truncating chunks...")
                    texts = [t[:8000] for t in texts]
                else:
                    # If it's a different error, raise immediately
                    raise e
        return []

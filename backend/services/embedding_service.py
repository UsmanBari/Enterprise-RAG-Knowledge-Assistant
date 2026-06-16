import os
import sys
from sentence_transformers import SentenceTransformer

# Ensure parent directory (backend) is in Python path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class EmbeddingService:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        print(f"[EmbeddingService] Loading model '{config.EMBEDDING_MODEL}' on startup...")
        try:
            self.model = SentenceTransformer(config.EMBEDDING_MODEL)
            print("[EmbeddingService] Model loaded successfully.")
        except Exception as e:
            print(f"[EmbeddingService] Error loading embedding model: {e}")
            raise e

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Batch embeds a list of strings and returns their vector representations.
        """
        if not texts:
            return []
            
        print(f"[EmbeddingService] Generating embeddings for {len(texts)} texts...")
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            print(f"[EmbeddingService] Error generating embeddings: {e}")
            raise e

embedding_service = EmbeddingService()

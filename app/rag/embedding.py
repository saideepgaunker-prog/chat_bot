import re
import math
import numpy as np
from typing import List, Union
from app.core.config import settings
from app.core.logger import logger

class EmbeddingService:
    def __init__(self, vector_dim: int = 128):
        self.vector_dim = vector_dim
        self._gemini_client = None
        self._has_gemini = False
        self._init_gemini()

    def _init_gemini(self):
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._has_gemini = True
            except Exception as e:
                logger.warning(f"Could not configure Gemini embeddings: {e}")

    def embed_text(self, text: str) -> List[float]:
        """Generate a normalized embedding vector for the given text."""
        if not text or not text.strip():
            return [0.0] * self.vector_dim

        # Fast deterministic semantic hashing vectorizer (hashing trick + n-grams + word weights)
        tokens = re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())
        vec = np.zeros(self.vector_dim, dtype=np.float32)
        
        for i, token in enumerate(tokens):
            # Token hash
            h = hash(token) % self.vector_dim
            weight = 1.0 / (math.log(i + 2))
            vec[h] += float(weight)
            
            # Sub-token n-grams (3-grams) for robust typo & stem tolerance
            if len(token) >= 3:
                for j in range(len(token) - 2):
                    sub = token[j:j+3]
                    sub_h = hash(sub) % self.vector_dim
                    vec[sub_h] += 0.35

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vector representations."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

embedding_service = EmbeddingService()

"""
Abstract Provider Interfaces for Module C.
Decouples vendor-specific embedding/LLM/vector/graph implementations from core domain logic.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np


class EmbeddingProvider(ABC):
    """Abstract interface for embedding generation."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for single text passage."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for batch of text passages."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Return embedding dimension."""
        pass


class LLMProvider(ABC):
    """Abstract interface for LLM operations (reasoning, extraction)."""
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> str:
        """Generate text completion from prompt."""
        pass

    @abstractmethod
    async def extract_structured_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured JSON conforming to schema."""
        pass


class RerankerProvider(ABC):
    """Abstract interface for cross-encoder/heuristic candidate reranking."""
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Score and rerank candidate items against query."""
        pass


class VectorStore(ABC):
    """Abstract interface for vector similarity retrieval and indexing."""
    
    @abstractmethod
    async def insert_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """Insert a vector entry with metadata."""
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Cosine similarity search with metadata filtering."""
        pass

    @abstractmethod
    async def delete_by_source(self, source_id: str, source_version: Optional[int] = None) -> int:
        """Remove vectors associated with a source."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic feature-hash embedding provider for testing and offline execution."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    STOPWORDS = {
        "what", "is", "the", "of", "and", "a", "an", "in", "to", "for", "on", "with",
        "as", "by", "at", "from", "or", "which", "this", "that", "it", "are", "be",
        "under", "any", "how", "where", "when", "who", "all", "shall", "may"
    }

    async def embed_text(self, text: str) -> List[float]:
        import re
        import hashlib
        raw_words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
        words = [w for w in raw_words if w not in self.STOPWORDS]
        vec = np.zeros(self.dimension, dtype=np.float32)
        for w in words:
            # Deterministic hash index across platforms
            idx = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16) % self.dimension
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(t) for t in texts]

    def get_dimension(self) -> int:
        return self.dimension


class MockLLMProvider(LLMProvider):
    """Mock LLM Provider for unit testing and deterministic execution."""
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> str:
        return "CivicSphere Knowledge Provider Completion: Evidence verified from official source."

    async def extract_structured_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        return {"entities": [], "relationships": []}

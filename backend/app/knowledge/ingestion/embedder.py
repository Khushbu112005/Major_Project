"""
Chunk Embedder Pipeline with Caching.
Integrates with abstract EmbeddingProvider to generate and attach dense vectors to chunks.
"""

from typing import List, Dict, Any, Tuple
import hashlib
from backend.app.common.providers import EmbeddingProvider, MockEmbeddingProvider
from backend.app.knowledge.domain.source import ChunkRecord


class ChunkEmbedder:
    """Generates embedding vectors for chunks with memory caching."""

    def __init__(self, provider: EmbeddingProvider = None):
        self.provider = provider or MockEmbeddingProvider()
        self._cache: Dict[str, List[float]] = {}

    async def embed_chunks(self, chunks: List[ChunkRecord]) -> List[Tuple[ChunkRecord, List[float]]]:
        results: List[Tuple[ChunkRecord, List[float]]] = []
        texts_to_embed: List[str] = []
        indices_to_embed: List[int] = []

        for idx, chunk in enumerate(chunks):
            cache_key = chunk.content_hash
            if cache_key in self._cache:
                results.append((chunk, self._cache[cache_key]))
            else:
                texts_to_embed.append(chunk.text)
                indices_to_embed.append(idx)

        if texts_to_embed:
            vectors = await self.provider.embed_batch(texts_to_embed)
            for chunk_idx, vec in zip(indices_to_embed, vectors):
                chunk = chunks[chunk_idx]
                self._cache[chunk.content_hash] = vec
                results.append((chunk, vec))

        # Sort back to original order
        results.sort(key=lambda x: x[0].chunk_index)
        return results

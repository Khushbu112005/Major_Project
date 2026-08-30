"""
Vector Store and Vector Writer for Ingestion Pipeline.
Stores chunk embeddings with metadata filtering (jurisdiction, verification status, effective dates)
and provides cosine similarity search.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from packages.schemas.contracts import VerificationStatus
from backend.app.knowledge.domain.source import ChunkRecord
from backend.app.common.providers import VectorStore


class InMemoryVectorStore(VectorStore):
    """In-memory Vector Store implementation with cosine similarity search and metadata filtering."""

    def __init__(self):
        self._vectors: Dict[str, np.ndarray] = {}  # chunk_id -> vector
        self._metadata: Dict[str, Dict[str, Any]] = {}  # chunk_id -> metadata
        self._chunks: Dict[str, ChunkRecord] = {}

    async def insert_vector(
        self,
        vector_id: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        arr = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        self._vectors[vector_id] = arr
        self._metadata[vector_id] = metadata

    def store_chunk_mapping(self, chunk: ChunkRecord, vector: List[float]) -> None:
        self._chunks[chunk.chunk_id] = chunk
        arr = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        self._vectors[chunk.chunk_id] = arr
        self._metadata[chunk.chunk_id] = {
            "chunk_id": chunk.chunk_id,
            "source_id": chunk.source_id,
            "source_version": chunk.source_version,
            "source_type": chunk.source_type,
            "jurisdiction": chunk.jurisdiction,
            "verification_status": chunk.verification_status.value if hasattr(chunk.verification_status, 'value') else chunk.verification_status,
            "effective_date": chunk.effective_date,
            "content_hash": chunk.content_hash,
            "section_number": chunk.section_number,
            "act_title": chunk.act_title,
        }

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self._vectors:
            return []

        q_arr = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_arr)
        if q_norm > 0:
            q_arr = q_arr / q_norm

        scored_candidates: List[Tuple[float, str, ChunkRecord]] = []

        for chunk_id, vec in self._vectors.items():
            meta = self._metadata.get(chunk_id, {})
            chunk = self._chunks.get(chunk_id)
            if not chunk:
                continue

            # Apply metadata filters
            if filters:
                if "jurisdiction" in filters and filters["jurisdiction"]:
                    if meta.get("jurisdiction", "").lower() != filters["jurisdiction"].lower():
                        continue
                if "verification_status" in filters and filters["verification_status"]:
                    req_status = filters["verification_status"]
                    if isinstance(req_status, list):
                        req_status_vals = [s.value if hasattr(s, 'value') else s for s in req_status]
                        if meta.get("verification_status") not in req_status_vals:
                            continue
                    elif meta.get("verification_status") != (req_status.value if hasattr(req_status, 'value') else req_status):
                        continue
                if "source_types" in filters and filters["source_types"]:
                    if meta.get("source_type") not in filters["source_types"]:
                        continue

            score = float(np.dot(q_arr, vec))
            if score > 0.05:
                scored_candidates.append((score, chunk_id, chunk))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk_id, chunk in scored_candidates[:top_k]:
            results.append({
                "chunk_id": chunk_id,
                "score": score,
                "chunk": chunk,
                "metadata": self._metadata.get(chunk_id, {})
            })

        return results

    async def delete_by_source(self, source_id: str, source_version: Optional[int] = None) -> int:
        deleted = 0
        to_delete = []
        for cid, meta in self._metadata.items():
            if meta.get("source_id") == source_id:
                if source_version is None or meta.get("source_version") == source_version:
                    to_delete.append(cid)

        for cid in to_delete:
            self._vectors.pop(cid, None)
            self._metadata.pop(cid, None)
            self._chunks.pop(cid, None)
            deleted += 1

        return deleted

    def clear(self) -> None:
        self._vectors.clear()
        self._metadata.clear()
        self._chunks.clear()


# Global Singleton Vector Store
vector_store = InMemoryVectorStore()

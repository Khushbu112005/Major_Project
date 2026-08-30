"""
Semantic Vector Retrieval Engine.
Uses embedding representations to identify semantically relevant provisions and knowledge items.
"""

from typing import List, Dict, Any, Optional
from backend.app.common.providers import EmbeddingProvider, MockEmbeddingProvider
from backend.app.knowledge.domain.retrieval import RetrievalCandidate, FilterCriteria
from backend.app.knowledge.ingestion.vector_writer import vector_store


class VectorRetriever:
    """Semantic retrieval engine with metadata pre-filtering."""

    def __init__(self, embedder_provider: Optional[EmbeddingProvider] = None):
        self.provider = embedder_provider or MockEmbeddingProvider()

    async def search(
        self,
        query: str,
        filters: Optional[FilterCriteria] = None,
        top_k: int = 10
    ) -> List[RetrievalCandidate]:
        # Generate embedding for query
        query_vec = await self.provider.embed_text(query)

        # Convert FilterCriteria to dict for VectorStore
        filter_dict = {}
        if filters:
            if filters.jurisdiction:
                filter_dict["jurisdiction"] = filters.jurisdiction
            if filters.verification_statuses:
                filter_dict["verification_status"] = filters.verification_statuses
            if filters.source_types:
                filter_dict["source_types"] = filters.source_types

        search_results = await vector_store.search(
            query_vector=query_vec,
            top_k=top_k,
            filters=filter_dict
        )

        candidates: List[RetrievalCandidate] = []
        for res in search_results:
            chunk = res["chunk"]
            candidates.append(
                RetrievalCandidate(
                    chunk_id=chunk.chunk_id,
                    source_id=chunk.source_id,
                    source_version=chunk.source_version,
                    text=chunk.text,
                    score=float(res["score"]),
                    retrieval_channel="vector",
                    metadata={
                        "act_title": chunk.act_title,
                        "section_number": chunk.section_number,
                        "section_title": chunk.section_title,
                        "publisher": chunk.metadata.get("publisher"),
                        "official_url": chunk.metadata.get("official_url"),
                        "verification_status": chunk.verification_status.value if hasattr(chunk.verification_status, 'value') else chunk.verification_status
                    }
                )
            )

        return candidates

"""
Re-Indexing and Embedding Refresh Jobs.
Re-indexes vectors and graph entities when embedding models or parsers are updated.
"""

from typing import Dict, Any, List
import uuid
import asyncio
from datetime import datetime, timezone
import logging

from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.ingestion.embedder import ChunkEmbedder
from backend.app.knowledge.ingestion.vector_writer import vector_store

logger = logging.getLogger("civicsphere.jobs.reindex")


class ReindexJobManager:
    """Manages re-indexing of chunks into vector and graph stores."""

    @classmethod
    async def reindex_all_sources(cls, actor_id: str = "admin") -> Dict[str, Any]:
        sources = source_registry.list_sources()
        total_chunks = 0
        reindexed_sources = 0
        embedder = ChunkEmbedder()

        for source in sources:
            chunks = source_registry.get_chunks(source.source_id)
            if not chunks:
                continue

            # Remove old vectors for this source
            await vector_store.delete_by_source(source.source_id)

            # Generate new embeddings
            embedded = await embedder.embed_chunks(chunks)
            for chunk, vec in embedded:
                vector_store.store_chunk_mapping(chunk, vec)
                total_chunks += 1

            reindexed_sources += 1

        return {
            "status": "COMPLETED",
            "sources_reindexed": reindexed_sources,
            "chunks_reindexed": total_chunks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

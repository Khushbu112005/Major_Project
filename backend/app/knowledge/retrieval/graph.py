"""
Graph-Based Relational Retrieval Engine.
Answers relationship-oriented queries (e.g. "What authority administers this provision?",
"What documents are required?", "Which notification amended this section?") by traversing connected graph entities.
"""

from typing import List, Dict, Any, Optional
from backend.app.knowledge.domain.entities import EntityType
from backend.app.knowledge.domain.relationships import RelationType
from backend.app.knowledge.domain.retrieval import RetrievalCandidate, FilterCriteria
from backend.app.knowledge.graph.repository import graph_repository
from backend.app.knowledge.sources.registry import source_registry


class GraphRetriever:
    """Retrieves grounded knowledge candidates via structural graph traversal."""

    @classmethod
    async def search(
        cls,
        query: str,
        filters: Optional[FilterCriteria] = None,
        top_k: int = 10
    ) -> List[RetrievalCandidate]:
        # 1. Identify seed entities matching query terms
        matched_entities = graph_repository.find_entities_by_name(query, limit=5)
        if not matched_entities:
            return []

        candidates: List[RetrievalCandidate] = []
        seen_chunks = set()

        for entity in matched_entities:
            # Get neighborhood up to depth 2
            sub_entities, relationships = graph_repository.get_neighborhood(entity.entity_id, max_depth=2, limit_per_node=6)
            
            # Find chunk references linked via relationships and entities
            related_source_ids = set(entity.source_ids)
            for r in relationships:
                related_source_ids.add(r.source_id)

            for src_id in related_source_ids:
                chunks = source_registry.get_chunks(src_id)
                for chunk in chunks:
                    if chunk.chunk_id in seen_chunks:
                        continue

                    # Check if chunk mentions this entity or related relationships
                    if entity.name.lower() in chunk.text.lower() or (chunk.section_number and chunk.section_number in entity.name):
                        seen_chunks.add(chunk.chunk_id)
                        
                        # Build graph context summary
                        graph_ctx = [
                            f"{r.relation_type.value} -> target_id {r.target_entity_id}"
                            for r in relationships if r.source_entity_id == entity.entity_id
                        ]

                        candidates.append(
                            RetrievalCandidate(
                                chunk_id=chunk.chunk_id,
                                source_id=chunk.source_id,
                                source_version=chunk.source_version,
                                text=chunk.text,
                                score=0.85,  # Strong structural association score
                                retrieval_channel="graph",
                                metadata={
                                    "matched_entity_id": entity.entity_id,
                                    "matched_entity_name": entity.name,
                                    "matched_entity_type": entity.entity_type.value,
                                    "graph_connections": graph_ctx,
                                    "act_title": chunk.act_title,
                                    "section_number": chunk.section_number,
                                    "section_title": chunk.section_title,
                                    "publisher": chunk.metadata.get("publisher"),
                                    "official_url": chunk.metadata.get("official_url"),
                                    "verification_status": chunk.verification_status.value if hasattr(chunk.verification_status, 'value') else chunk.verification_status
                                }
                            )
                        )

        return candidates[:top_k]

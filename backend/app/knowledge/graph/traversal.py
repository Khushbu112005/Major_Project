"""
Graph Traversal and Neighborhood Explorer.
Provides bounded exploration and structured neighborhood expansion for UI and Agent retrieval.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.knowledge.domain.entities import EntityDomainModel
from backend.app.knowledge.domain.relationships import RelationshipDomainModel
from backend.app.knowledge.graph.repository import graph_repository


class GraphExplorationResponse(BaseModel):
    selected_entity: EntityDomainModel
    neighborhood_entities: List[EntityDomainModel] = Field(default_factory=list)
    relationships: List[RelationshipDomainModel] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    depth: int = 1
    total_nodes: int = 0
    total_edges: int = 0


class GraphTraversalService:
    """Safely traverses relational knowledge graph with limits to prevent graph explosion."""

    @classmethod
    def explore_entity(
        cls,
        entity_id: str,
        depth: int = 1,
        limit_per_node: int = 8
    ) -> GraphExplorationResponse:
        selected_entity = graph_repository.get_entity(entity_id)
        entities, relationships = graph_repository.get_neighborhood(
            entity_id=entity_id,
            max_depth=depth,
            limit_per_node=limit_per_node
        )

        all_sources = set(selected_entity.source_ids)
        for e in entities:
            all_sources.update(e.source_ids)
        for r in relationships:
            all_sources.add(r.source_id)

        other_entities = [e for e in entities if e.entity_id != entity_id]

        return GraphExplorationResponse(
            selected_entity=selected_entity,
            neighborhood_entities=other_entities,
            relationships=relationships,
            sources=list(all_sources),
            depth=depth,
            total_nodes=len(entities),
            total_edges=len(relationships)
        )

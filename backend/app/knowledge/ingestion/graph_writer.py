"""
Graph Insertion Writer for Ingestion Pipeline.
Persists validated entity candidates and relational edges into the GraphRepository with provenance anchors.
"""

from typing import List, Tuple
from backend.app.knowledge.domain.entities import EntityDomainModel
from backend.app.knowledge.domain.relationships import RelationshipDomainModel
from backend.app.knowledge.graph.repository import graph_repository


class GraphWriter:
    """Writes extracted entities and relationships into the Knowledge Graph."""

    @classmethod
    def write_extracted_graph(
        cls,
        entities: List[EntityDomainModel],
        relationships: List[RelationshipDomainModel]
    ) -> Tuple[int, int]:
        nodes_written = 0
        edges_written = 0

        for ent in entities:
            graph_repository.insert_entity(ent)
            nodes_written += 1

        for rel in relationships:
            graph_repository.insert_relationship(rel)
            edges_written += 1

        return nodes_written, edges_written

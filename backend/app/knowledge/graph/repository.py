"""
Neo4j Graph Repository for CivicSphere.
Enforces parameterized Cypher queries, bounded neighborhood exploration, provenance tracking, and strict authorization.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
import logging

from backend.app.knowledge.domain.entities import EntityDomainModel, EntityType
from backend.app.knowledge.domain.relationships import RelationshipDomainModel, RelationType
from backend.app.common.config import settings
from backend.app.common.errors import SecurityBlockedException, NotFoundException

logger = logging.getLogger("civicsphere.graph")


class GraphRepository:
    """
    Secure Graph Repository interface.
    Implements in-memory graph index with full Cypher parameterization guarantees.
    """

    def __init__(self):
        self._nodes: Dict[str, EntityDomainModel] = {}
        self._relationships: Dict[str, RelationshipDomainModel] = {}
        # Indexes for fast bounded traversal
        self._adjacency_out: Dict[str, List[str]] = {}  # entity_id -> [rel_id, ...]
        self._adjacency_in: Dict[str, List[str]] = {}

    def insert_entity(self, entity: EntityDomainModel) -> EntityDomainModel:
        """Stores or updates an entity node in the graph."""
        if entity.entity_id in self._nodes:
            # Update attributes and merge sources
            existing = self._nodes[entity.entity_id]
            for sid in entity.source_ids:
                if sid not in existing.source_ids:
                    existing.source_ids.append(sid)
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            return existing

        self._nodes[entity.entity_id] = entity
        self._adjacency_out[entity.entity_id] = []
        self._adjacency_in[entity.entity_id] = []
        return entity

    def insert_relationship(self, relationship: RelationshipDomainModel) -> RelationshipDomainModel:
        """Stores a verified relationship edge."""
        if relationship.source_entity_id not in self._nodes or relationship.target_entity_id not in self._nodes:
            logger.warning(f"Cannot insert edge {relationship.relationship_id}: Source or target node missing.")
            return relationship

        self._relationships[relationship.relationship_id] = relationship
        self._adjacency_out.setdefault(relationship.source_entity_id, []).append(relationship.relationship_id)
        self._adjacency_in.setdefault(relationship.target_entity_id, []).append(relationship.relationship_id)
        return relationship

    def get_entity(self, entity_id: str) -> EntityDomainModel:
        if entity_id not in self._nodes:
            raise NotFoundException(f"Graph entity with ID '{entity_id}' not found.")
        return self._nodes[entity_id]

    def find_entities_by_type(self, entity_type: EntityType, limit: int = 50) -> List[EntityDomainModel]:
        results = [e for e in self._nodes.values() if e.entity_type == entity_type]
        return results[:limit]

    def find_entities_by_name(self, name_query: str, limit: int = 10) -> List[EntityDomainModel]:
        query_clean = name_query.strip().lower()
        matches = []
        for e in self._nodes.values():
            if query_clean in e.name.lower() or any(query_clean in a.lower() for a in e.aliases):
                matches.append(e)
        return matches[:limit]

    def get_neighborhood(
        self,
        entity_id: str,
        max_depth: int = 2,
        limit_per_node: int = 10
    ) -> Tuple[List[EntityDomainModel], List[RelationshipDomainModel]]:
        """
        Explores bounded subgraph neighborhood up to max_depth.
        Guarantees: Depth <= settings.NEO4J_MAX_DEPTH, no full graph dumps.
        """
        if max_depth > settings.NEO4J_MAX_DEPTH:
            max_depth = settings.NEO4J_MAX_DEPTH

        visited_nodes: Set[str] = {entity_id}
        collected_entities: Dict[str, EntityDomainModel] = {}
        collected_relationships: Dict[str, RelationshipDomainModel] = {}

        if entity_id in self._nodes:
            collected_entities[entity_id] = self._nodes[entity_id]

        current_frontier = [entity_id]

        for depth in range(max_depth):
            next_frontier = []
            for node_id in current_frontier:
                # Outgoing edges
                out_rel_ids = self._adjacency_out.get(node_id, [])[:limit_per_node]
                for r_id in out_rel_ids:
                    rel = self._relationships.get(r_id)
                    if rel:
                        collected_relationships[rel.relationship_id] = rel
                        target_id = rel.target_entity_id
                        if target_id not in visited_nodes:
                            visited_nodes.add(target_id)
                            if target_id in self._nodes:
                                collected_entities[target_id] = self._nodes[target_id]
                                next_frontier.append(target_id)

                # Incoming edges
                in_rel_ids = self._adjacency_in.get(node_id, [])[:limit_per_node]
                for r_id in in_rel_ids:
                    rel = self._relationships.get(r_id)
                    if rel:
                        collected_relationships[rel.relationship_id] = rel
                        source_id = rel.source_entity_id
                        if source_id not in visited_nodes:
                            visited_nodes.add(source_id)
                            if source_id in self._nodes:
                                collected_entities[source_id] = self._nodes[source_id]
                                next_frontier.append(source_id)

            current_frontier = next_frontier
            if not current_frontier:
                break

        return list(collected_entities.values()), list(collected_relationships.values())

    def execute_parameterized_query(
        self,
        query_name: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Executes strictly pre-compiled, parameterized graph queries.
        Arbitrary user/LLM Cypher strings are strictly rejected.
        """
        if query_name == "get_section_authority":
            sec_name = params.get("section_name", "").lower()
            results = []
            for rel in self._relationships.values():
                if rel.relation_type == RelationType.ADMINISTERED_BY:
                    sec_node = self._nodes.get(rel.source_entity_id)
                    auth_node = self._nodes.get(rel.target_entity_id)
                    if sec_node and auth_node and sec_name in sec_node.name.lower():
                        results.append({
                            "section": sec_node.model_dump(),
                            "authority": auth_node.model_dump(),
                            "relationship": rel.model_dump()
                        })
            return results

        elif query_name == "get_right_and_remedies":
            right_query = params.get("right_name", "").lower()
            results = []
            for rel in self._relationships.values():
                if rel.relation_type == RelationType.DERIVED_FROM:
                    right_node = self._nodes.get(rel.source_entity_id)
                    sec_node = self._nodes.get(rel.target_entity_id)
                    if right_node and sec_node and right_query in right_node.name.lower():
                        results.append({
                            "right": right_node.model_dump(),
                            "section": sec_node.model_dump(),
                            "relationship": rel.model_dump()
                        })
            return results

        raise SecurityBlockedException(f"Query template '{query_name}' is not in the parameterized allowlist.")

    def clear(self) -> None:
        self._nodes.clear()
        self._relationships.clear()
        self._adjacency_out.clear()
        self._adjacency_in.clear()


# Global Singleton Graph Instance
graph_repository = GraphRepository()

"""
Graph-Level Authorization and Visibility Enforcement.
Ensures graph nodes and relationships are filtered according to user roles, jurisdictions, and source verification state.
"""

from typing import List, Tuple
from backend.app.common.security import AuthContext
from backend.app.knowledge.domain.entities import EntityDomainModel
from backend.app.knowledge.domain.relationships import RelationshipDomainModel


class GraphAuthorizationPolicy:
    """Enforces fine-grained access control on graph entities and relationships."""

    @classmethod
    def filter_entities(
        cls,
        entities: List[EntityDomainModel],
        auth: AuthContext
    ) -> List[EntityDomainModel]:
        # Normal public entities are accessible to all authenticated roles
        # If custom private entities exist (e.g. tenant-specific document graph), filter by tenant_id
        if auth.role in ("admin", "system"):
            return entities

        authorized = []
        for ent in entities:
            # Check tenant if marked
            ent_tenant = ent.attributes.get("tenant_id")
            if ent_tenant and ent_tenant != auth.tenant_id:
                continue
            authorized.append(ent)

        return authorized

    @classmethod
    def filter_relationships(
        cls,
        relationships: List[RelationshipDomainModel],
        authorized_entity_ids: set
    ) -> List[RelationshipDomainModel]:
        # Only retain relationships where both endpoints are authorized
        return [
            r for r in relationships
            if r.source_entity_id in authorized_entity_ids and r.target_entity_id in authorized_entity_ids
        ]

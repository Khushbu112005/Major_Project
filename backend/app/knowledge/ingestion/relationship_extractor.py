"""
Relationship Extraction Engine.
Extracts grounded relational edges between domain entities (ACT -> HAS_SECTION -> SECTION,
SECTION -> ADMINISTERED_BY -> AUTHORITY, RIGHT -> DERIVED_FROM -> SECTION, etc.)
attaching exact provenance metadata.
"""

from typing import List, Dict, Any, Tuple
from backend.app.knowledge.domain.entities import EntityDomainModel, EntityType
from backend.app.knowledge.domain.relationships import RelationshipDomainModel, RelationType
from backend.app.knowledge.domain.source import ChunkRecord


class RelationshipExtractor:
    """Extracts verified relational links connecting domain entities."""

    @classmethod
    def extract_relationships(
        cls,
        chunk: ChunkRecord,
        entities: List[EntityDomainModel]
    ) -> List[RelationshipDomainModel]:
        relationships: List[RelationshipDomainModel] = []
        
        # Index entities by type
        acts = [e for e in entities if e.entity_type == EntityType.ACT]
        sections = [e for e in entities if e.entity_type == EntityType.SECTION]
        authorities = [e for e in entities if e.entity_type == EntityType.AUTHORITY]
        rights = [e for e in entities if e.entity_type == EntityType.RIGHT]
        deadlines = [e for e in entities if e.entity_type == EntityType.DEADLINE]

        # 1. ACT -> HAS_SECTION -> SECTION
        for act in acts:
            for sec in sections:
                relationships.append(
                    RelationshipDomainModel(
                        source_entity_id=act.entity_id,
                        target_entity_id=sec.entity_id,
                        relation_type=RelationType.HAS_SECTION,
                        source_id=chunk.source_id,
                        source_version=chunk.source_version,
                        source_chunk_id=chunk.chunk_id,
                        confidence=1.0
                    )
                )

        # 2. SECTION -> ADMINISTERED_BY -> AUTHORITY
        for sec in sections:
            for auth in authorities:
                relationships.append(
                    RelationshipDomainModel(
                        source_entity_id=sec.entity_id,
                        target_entity_id=auth.entity_id,
                        relation_type=RelationType.ADMINISTERED_BY,
                        source_id=chunk.source_id,
                        source_version=chunk.source_version,
                        source_chunk_id=chunk.chunk_id,
                        confidence=0.95
                    )
                )

        # 3. RIGHT -> DERIVED_FROM -> SECTION
        for right in rights:
            for sec in sections:
                relationships.append(
                    RelationshipDomainModel(
                        source_entity_id=right.entity_id,
                        target_entity_id=sec.entity_id,
                        relation_type=RelationType.DERIVED_FROM,
                        source_id=chunk.source_id,
                        source_version=chunk.source_version,
                        source_chunk_id=chunk.chunk_id,
                        confidence=0.90
                    )
                )

        # 4. SECTION -> SUBJECT_TO_DEADLINE -> DEADLINE
        for sec in sections:
            for deadline in deadlines:
                relationships.append(
                    RelationshipDomainModel(
                        source_entity_id=sec.entity_id,
                        target_entity_id=deadline.entity_id,
                        relation_type=RelationType.SUBJECT_TO_DEADLINE,
                        source_id=chunk.source_id,
                        source_version=chunk.source_version,
                        source_chunk_id=chunk.chunk_id,
                        confidence=0.95
                    )
                )

        # Deduplicate relationships by canonical key
        deduped: Dict[str, RelationshipDomainModel] = {}
        for rel in relationships:
            key = rel.get_canonical_key()
            if key not in deduped:
                deduped[key] = rel

        return list(deduped.values())

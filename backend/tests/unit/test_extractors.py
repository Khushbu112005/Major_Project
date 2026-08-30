"""
Unit tests for Entity and Relationship Extractors.
Verifies entity classification, deduplication, and relational edges.
"""

import pytest
from backend.app.knowledge.domain.source import ChunkRecord
from backend.app.knowledge.domain.entities import EntityType
from backend.app.knowledge.domain.relationships import RelationType
from backend.app.knowledge.ingestion.entity_extractor import EntityExtractor
from backend.app.knowledge.ingestion.relationship_extractor import RelationshipExtractor
from packages.schemas.contracts import VerificationStatus


def test_entity_and_relationship_extraction():
    chunk = ChunkRecord(
        chunk_id="chk_test_1",
        source_id="src_rti_1",
        source_version=1,
        chunk_index=0,
        text="[Right to Information Act, 2005 - Section 19: Appeal]\nAn appeal shall lie to the Central Information Commission within 90 days. Every citizen shall have the right to access public records.",
        content_hash="dummy_hash",
        act_title="Right to Information Act, 2005",
        section_number="19",
        section_title="Appeal",
        jurisdiction="IN",
        source_type="ACT",
        verification_status=VerificationStatus.ACTIVE
    )

    # 1. Entity Extraction
    entities = EntityExtractor.extract_entities_from_chunk(chunk)
    entity_types = {e.entity_type for e in entities}

    assert EntityType.ACT in entity_types
    assert EntityType.SECTION in entity_types
    assert EntityType.AUTHORITY in entity_types
    assert EntityType.RIGHT in entity_types

    # Verify authority name
    auth_entities = [e for e in entities if e.entity_type == EntityType.AUTHORITY]
    assert any("Central Information Commission" in e.name for e in auth_entities)

    # 2. Relationship Extraction
    relationships = RelationshipExtractor.extract_relationships(chunk, entities)
    relation_types = {r.relation_type for r in relationships}

    assert RelationType.HAS_SECTION in relation_types
    assert RelationType.ADMINISTERED_BY in relation_types
    assert RelationType.DERIVED_FROM in relation_types

    # Verify provenance attached to relationship
    rel = relationships[0]
    assert rel.source_id == "src_rti_1"
    assert rel.source_version == 1
    assert rel.source_chunk_id == "chk_test_1"

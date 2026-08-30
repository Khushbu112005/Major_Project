"""
CivicSphere Knowledge Domain Relationship Definitions.
Defines valid directional relationship types between entities.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class RelationType(str, Enum):
    HAS_SECTION = "HAS_SECTION"
    HAS_SUBSECTION = "HAS_SUBSECTION"
    HAS_RULE = "HAS_RULE"
    AMENDED_BY = "AMENDED_BY"
    ADMINISTERED_BY = "ADMINISTERED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    PUNISHABLE_UNDER = "PUNISHABLE_UNDER"
    AVAILABLE_AT = "AVAILABLE_AT"
    REQUIRES = "REQUIRES"
    PROVIDED_BY = "PROVIDED_BY"
    AVAILABLE_IN = "AVAILABLE_IN"
    HAS_ELIGIBILITY = "HAS_ELIGIBILITY"
    APPLIED_THROUGH = "APPLIED_THROUGH"
    ESCALATES_TO = "ESCALATES_TO"
    APPEAL_TO = "APPEAL_TO"
    SUBJECT_TO_DEADLINE = "SUBJECT_TO_DEADLINE"
    SUPERSEDES = "SUPERSEDES"
    CITES = "CITES"


class RelationshipDomainModel(BaseModel):
    """Strongly typed graph edge/relationship model."""
    relationship_id: str = Field(default_factory=lambda: f"rel_{uuid.uuid4().hex[:12]}")
    source_entity_id: str
    target_entity_id: str
    relation_type: RelationType
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Provenance metadata
    source_id: str
    source_version: int = 1
    source_chunk_id: Optional[str] = None
    confidence: float = 1.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def get_canonical_key(self) -> str:
        """Deterministic relationship key."""
        return f"{self.source_entity_id}:{self.relation_type.value}:{self.target_entity_id}"

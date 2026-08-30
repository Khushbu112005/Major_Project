"""
CivicSphere Knowledge Domain Entity Definitions.
Defines strongly typed entity types representing civic, legal, and governmental constructs.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class EntityType(str, Enum):
    ACT = "ACT"
    SECTION = "SECTION"
    SUBSECTION = "SUBSECTION"
    RULE = "RULE"
    REGULATION = "REGULATION"
    NOTIFICATION = "NOTIFICATION"
    ORDER = "ORDER"
    COURT = "COURT"
    JUDGMENT = "JUDGMENT"
    AUTHORITY = "AUTHORITY"
    RIGHT = "RIGHT"
    DUTY = "DUTY"
    REMEDY = "REMEDY"
    OFFENCE = "OFFENCE"
    PENALTY = "PENALTY"
    PROCEDURE = "PROCEDURE"
    DOCUMENT = "DOCUMENT"
    SERVICE = "SERVICE"
    SCHEME = "SCHEME"
    DEPARTMENT = "DEPARTMENT"
    MINISTRY = "MINISTRY"
    STATE = "STATE"
    DISTRICT = "DISTRICT"
    ELIGIBILITY = "ELIGIBILITY"
    FEE = "FEE"
    PORTAL = "PORTAL"
    GRIEVANCE = "GRIEVANCE"
    APPEAL = "APPEAL"
    DEADLINE = "DEADLINE"


class EntityDomainModel(BaseModel):
    """Strongly typed graph entity node."""
    entity_id: str = Field(default_factory=lambda: f"ent_{uuid.uuid4().hex[:12]}")
    name: str
    entity_type: EntityType
    canonical_id: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    jurisdiction: str = "IN"  # Default India
    state: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Provenance
    source_ids: List[str] = Field(default_factory=list)
    source_versions: List[int] = Field(default_factory=list)
    confidence: float = 1.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def get_canonical_key(self) -> str:
        """Generates deterministic canonical deduplication key."""
        clean_name = self.name.strip().lower().replace("  ", " ")
        return f"{self.entity_type.value}:{self.jurisdiction}:{clean_name}"

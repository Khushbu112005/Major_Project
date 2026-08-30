"""
Evidence Pack Domain Models.
Defines the strict data structures returned to downstream reasoning modules (Legal, Government, Agents).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

from packages.schemas.contracts import VerificationStatus, SourceTrustLevel, FailSafeState


class GraphContextItem(BaseModel):
    """Related graph relationship context for an evidence item."""
    relationship_id: str
    source_entity_name: str
    source_entity_type: str
    relation_type: str
    target_entity_name: str
    target_entity_type: str
    confidence: float = 1.0


class EvidenceItem(BaseModel):
    """An individual piece of grounded, ranked evidence with provenance."""
    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:12]}")
    source_id: str
    source_version: int
    chunk_id: str
    text: str
    source_title: str
    source_url: str
    source_type: str
    trust_level: SourceTrustLevel = SourceTrustLevel.TRUSTED_SECONDARY_SOURCE
    verification_status: VerificationStatus = VerificationStatus.ACTIVE
    jurisdiction: str = "IN"
    effective_date: Optional[str] = None
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    
    # Relevance & Ranking
    lexical_score: float = 0.0
    vector_score: float = 0.0
    graph_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    
    graph_context: List[GraphContextItem] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceConflict(BaseModel):
    """Details when two sources present contradictory or diverging rules."""
    conflict_id: str = Field(default_factory=lambda: f"conf_{uuid.uuid4().hex[:8]}")
    topic: str
    source_a_id: str
    source_a_version: int
    source_a_text: str
    source_b_id: str
    source_b_version: int
    source_b_text: str
    explanation: str
    severity: str = "HIGH"  # LOW, MEDIUM, HIGH


class EvidencePack(BaseModel):
    """
    The primary evidence payload passed to downstream reasoning modules.
    Ensures complete explainability, groundedness, and fail-safe operation.
    """
    pack_id: str = Field(default_factory=lambda: f"evp_{uuid.uuid4().hex[:12]}")
    query: str
    query_summary: Optional[str] = None
    fail_safe_state: FailSafeState = FailSafeState.VERIFIED
    
    items: List[EvidenceItem] = Field(default_factory=list)
    conflicts: List[EvidenceConflict] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    evidence_confidence: float = 0.0
    confidence_category: str = "Insufficient"  # Strong, Good, Limited, Insufficient
    
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

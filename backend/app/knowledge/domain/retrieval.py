"""
Retrieval request and candidate representations for hybrid multi-modal search.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel


class FilterCriteria(BaseModel):
    """Metadata filtering constraints applied during retrieval."""
    jurisdiction: Optional[str] = None
    state: Optional[str] = None
    source_types: Optional[List[str]] = None
    verification_statuses: List[VerificationStatus] = [VerificationStatus.ACTIVE]
    min_trust_level: Optional[SourceTrustLevel] = None
    effective_before: Optional[str] = None
    effective_after: Optional[str] = None
    exclude_expired: bool = True
    must_have_provenance: bool = True


class RetrievalRequest(BaseModel):
    """Standardized search query request for the knowledge engine."""
    query: str
    filters: Optional[FilterCriteria] = Field(default_factory=FilterCriteria)
    top_k: int = 5
    include_graph: bool = True
    include_vector: bool = True
    include_lexical: bool = True
    expand_entities: bool = True


class RetrievalCandidate(BaseModel):
    """Raw candidate produced by lexical, vector, or graph search."""
    chunk_id: str
    source_id: str
    source_version: int
    text: str
    score: float
    retrieval_channel: str  # lexical, vector, graph
    metadata: Dict[str, Any] = Field(default_factory=dict)

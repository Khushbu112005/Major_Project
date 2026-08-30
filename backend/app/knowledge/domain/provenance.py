"""
Provenance data structures for CivicSphere.
Enables tracing every extracted entity, relationship, and evidence passage back to its verified source version and location.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from packages.schemas.contracts import VerificationStatus, SourceTrustLevel


class ProvenanceTrace(BaseModel):
    """Full provenance chain for an evidence fact."""
    source_id: str
    source_title: str
    source_version: int
    chunk_id: str
    official_url: str
    publisher: str
    jurisdiction: str
    trust_level: SourceTrustLevel
    verification_status: VerificationStatus
    content_hash: str
    
    # Precise structural anchor
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validation_status: str = "VERIFIED"
    trace_details: Dict[str, Any] = Field(default_factory=dict)

"""
Source, SourceVersion, and Chunk domain models for CivicSphere.
Tracks full provenance, verification lifecycle, hashes, and version history.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

from packages.schemas.contracts import VerificationStatus, SourceTrustLevel, IngestionStatus


class SourceRecord(BaseModel):
    """Core Source Registry record."""
    source_id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:12]}")
    title: str
    publisher: str
    official_url: str
    jurisdiction: str = "IN"
    source_type: str  # ACT, NOTIFICATION, SCHEME, REGULATION, CIRCULAR, JUDGMENT
    trust_level: SourceTrustLevel = SourceTrustLevel.TRUSTED_SECONDARY_SOURCE
    
    current_version: int = 1
    content_hash: str
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    ingestion_status: IngestionStatus = IngestionStatus.PENDING
    
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    
    parser_version: str = "1.0.0"
    embedding_version: str = "1.0.0"
    
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_verified_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceVersionRecord(BaseModel):
    """Immutable record of a specific historical source version."""
    version_id: str = Field(default_factory=lambda: f"sver_{uuid.uuid4().hex[:12]}")
    source_id: str
    version_number: int
    content_hash: str
    raw_content: Optional[str] = None
    extracted_text: str
    change_summary: Optional[str] = None
    effective_date: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkRecord(BaseModel):
    """Granular, citation-addressable text chunk with structural location."""
    chunk_id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:12]}")
    source_id: str
    source_version: int
    chunk_index: int
    text: str
    content_hash: str
    
    # Structural hierarchy
    act_title: Optional[str] = None
    chapter: Optional[str] = None
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    subsection_number: Optional[str] = None
    page_number: Optional[int] = None
    
    jurisdiction: str = "IN"
    source_type: str = "ACT"
    verification_status: VerificationStatus = VerificationStatus.ACTIVE
    effective_date: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

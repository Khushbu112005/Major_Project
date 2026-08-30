"""
CivicSphere Shared Domain Schemas and Integration Contracts
Standardized across all CivicSphere modules (A, B, C, D, E, F).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
import uuid


class VerificationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"
    UNVERIFIED = "UNVERIFIED"
    BLOCKED = "BLOCKED"


class SourceTrustLevel(int, Enum):
    OFFICIAL_LEGISLATION = 1
    OFFICIAL_GOVERNMENT_DEPARTMENT = 2
    OFFICIAL_COURT_JUDICIARY = 3
    OFFICIAL_NOTIFICATION = 4
    TRUSTED_SECONDARY_SOURCE = 5


class IngestionStatus(str, Enum):
    PENDING = "PENDING"
    FETCHING = "FETCHING"
    VALIDATING = "VALIDATING"
    PARSING = "PARSING"
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    EMBEDDING = "EMBEDDING"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class FailSafeState(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICT = "CONFLICT"
    UNVERIFIED_SOURCE = "UNVERIFIED_SOURCE"
    STALE_SOURCE = "STALE_SOURCE"
    UNSUPPORTED_JURISDICTION = "UNSUPPORTED_JURISDICTION"
    NO_PROVENANCE = "NO_PROVENANCE"
    SECURITY_BLOCKED = "SECURITY_BLOCKED"


# --- API Envelopes ---

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: Optional[T] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApiErrorResponse(BaseModel):
    success: bool = False
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    error: ErrorDetail
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# --- Shared Domain Contracts ---

class User(BaseModel):
    user_id: str
    email: str
    role: str = "citizen"
    tenant_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Session(BaseModel):
    session_id: str
    user_id: str
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LegalSource(BaseModel):
    source_id: str
    title: str
    publisher: str
    official_url: str
    jurisdiction: str
    source_type: str
    trust_level: SourceTrustLevel = SourceTrustLevel.TRUSTED_SECONDARY_SOURCE
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_hash: str
    version: int = 1
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED


class GraphEntity(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    canonical_id: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    jurisdiction: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source_ids: List[str] = Field(default_factory=list)
    confidence: float = 1.0


class GraphRelationship(BaseModel):
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    source_ids: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    chunk_id: str
    source_id: str
    source_title: str
    source_url: str
    text: str
    score: float
    retrieval_mode: str  # lexical, vector, graph, hybrid
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    citation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    source_version: int
    chunk_id: str
    section: Optional[str] = None
    passage: str
    official_url: str
    verification_status: VerificationStatus
    is_verified: bool = False


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    actor_id: str
    role: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SecurityEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    threat_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    actor_id: Optional[str] = None
    endpoint: str
    payload_sample: Optional[str] = None
    action_taken: str  # BLOCKED, QUARANTINED, LOGGED
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentToolCall(BaseModel):
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    tool_name: str
    parameters: Dict[str, Any]
    authorized: bool = False
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    query: str
    tool_calls: List[AgentToolCall] = Field(default_factory=list)
    outcome: str
    evidence_pack_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

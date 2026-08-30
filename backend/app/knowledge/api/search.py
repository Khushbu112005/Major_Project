"""
Search API for CivicSphere Knowledge Engine.
Exposes unified hybrid retrieval endpoint returning structured Evidence Packs with provenance and confidence scores.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone

from packages.schemas.contracts import ApiResponse, VerificationStatus, SourceTrustLevel
from backend.app.common.security import AuthContext, get_current_user_context
from backend.app.knowledge.domain.retrieval import RetrievalRequest, FilterCriteria
from backend.app.knowledge.retrieval.hybrid import hybrid_retrieval_service

router = APIRouter(prefix="/knowledge", tags=["Search & Retrieval"])


class SearchApiRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500, description="Civic or legal query string")
    jurisdiction: Optional[str] = Field(default="IN", description="Jurisdiction filter")
    state: Optional[str] = Field(default=None, description="State level filter (e.g. Maharashtra, Delhi)")
    source_types: Optional[List[str]] = Field(default=None, description="Filter by source type (ACT, NOTIFICATION, SCHEME)")
    verified_only: bool = Field(default=True, description="Restrict retrieval strictly to verified ACTIVE sources")
    include_graph: bool = Field(default=True, description="Traverse knowledge graph relationships")
    top_k: int = Field(default=5, ge=1, le=25, description="Maximum number of evidence items")


@router.post("/search", response_model=ApiResponse[Dict[str, Any]])
async def search_knowledge(
    payload: SearchApiRequest,
    auth: AuthContext = Depends(get_current_user_context)
) -> ApiResponse[Dict[str, Any]]:
    """
    Executes hybrid retrieval (Lexical + Vector + Graph + Metadata Filter + RRF Rerank)
    and returns a structured Evidence Pack.
    """
    statuses = [VerificationStatus.ACTIVE] if payload.verified_only else [VerificationStatus.ACTIVE, VerificationStatus.UNVERIFIED]
    
    filters = FilterCriteria(
        jurisdiction=payload.jurisdiction,
        state=payload.state,
        source_types=payload.source_types,
        verification_statuses=statuses
    )

    req = RetrievalRequest(
        query=payload.query,
        filters=filters,
        top_k=payload.top_k,
        include_graph=payload.include_graph
    )

    evidence_pack = await hybrid_retrieval_service.retrieve(req, actor_id=auth.user_id)

    # Format into standard response envelope
    return ApiResponse(
        success=True,
        data=evidence_pack.model_dump(),
        sources=[{"source_id": it.source_id, "title": it.source_title, "url": it.source_url} for it in evidence_pack.items],
        confidence=evidence_pack.evidence_confidence,
        warnings=evidence_pack.warnings
    )

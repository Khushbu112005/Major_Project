"""
Knowledge Ingestion APIs.
Provides endpoints for submitting asynchronous ingestion jobs and synchronous admin ingestion.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from packages.schemas.contracts import ApiResponse, SourceTrustLevel
from backend.app.common.security import AuthContext, require_role
from backend.app.knowledge.ingestion.pipeline import ingestion_pipeline
from backend.app.knowledge.jobs.ingestion import IngestionJobManager

router = APIRouter(prefix="/knowledge/ingestion", tags=["Ingestion"])


class IngestSourceRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    publisher: str = Field(min_length=2, max_length=255)
    official_url: str = Field(min_length=5, max_length=1024)
    jurisdiction: str = Field(default="IN")
    source_type: str = Field(default="ACT")  # ACT, NOTIFICATION, SCHEME, REGULATION
    raw_text: Optional[str] = Field(default=None)
    fetch_remote: bool = Field(default=False)
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None


@router.post("/jobs", response_model=ApiResponse[Dict[str, Any]], status_code=status.HTTP_202_ACCEPTED)
async def submit_ingestion_job(
    payload: IngestSourceRequest,
    auth: AuthContext = Depends(require_role(["admin", "system"]))
) -> ApiResponse[Dict[str, Any]]:
    """Submits an asynchronous background ingestion job (Admin only)."""
    job_id = IngestionJobManager.submit_ingestion_job(
        title=payload.title,
        publisher=payload.publisher,
        official_url=payload.official_url,
        jurisdiction=payload.jurisdiction,
        source_type=payload.source_type,
        raw_text=payload.raw_text,
        fetch_remote=payload.fetch_remote,
        actor_id=auth.user_id
    )

    return ApiResponse(
        success=True,
        data={"job_id": job_id, "status": "QUEUED"}
    )


@router.get("/jobs/{job_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_ingestion_job_status(
    job_id: str,
    auth: AuthContext = Depends(require_role(["admin", "system"]))
) -> ApiResponse[Dict[str, Any]]:
    """Fetches status of background ingestion job."""
    job = IngestionJobManager.get_job(job_id)
    if not job:
        return ApiResponse(success=False, warnings=[f"Job '{job_id}' not found."])

    return ApiResponse(
        success=True,
        data=job
    )


@router.post("/sync", response_model=ApiResponse[Dict[str, Any]])
async def sync_ingest_source(
    payload: IngestSourceRequest,
    auth: AuthContext = Depends(require_role(["admin", "system"]))
) -> ApiResponse[Dict[str, Any]]:
    """Executes immediate synchronous ingestion for administrative or testing workflows."""
    result = await ingestion_pipeline.ingest_source(
        title=payload.title,
        publisher=payload.publisher,
        official_url=payload.official_url,
        jurisdiction=payload.jurisdiction,
        source_type=payload.source_type,
        raw_text=payload.raw_text,
        fetch_remote=payload.fetch_remote,
        publication_date=payload.publication_date,
        effective_date=payload.effective_date,
        expiry_date=payload.expiry_date,
        actor_id=auth.user_id
    )

    return ApiResponse(
        success=True,
        data=result
    )

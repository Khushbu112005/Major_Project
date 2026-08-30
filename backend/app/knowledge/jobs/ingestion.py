"""
Asynchronous Ingestion Background Jobs.
Handles heavy source ingestion, parsing, embedding generation, and graph indexing without blocking HTTP requests.
"""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timezone
import asyncio
import logging

from packages.schemas.contracts import IngestionStatus, SourceTrustLevel
from backend.app.common.audit import AuditManager
from backend.app.knowledge.ingestion.pipeline import ingestion_pipeline

logger = logging.getLogger("civicsphere.jobs.ingestion")


class IngestionJobManager:
    """Manages background ingestion tasks and tracks execution states."""

    _jobs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def submit_ingestion_job(
        cls,
        title: str,
        publisher: str,
        official_url: str,
        jurisdiction: str,
        source_type: str,
        raw_text: Optional[str] = None,
        fetch_remote: bool = False,
        trust_level: Optional[SourceTrustLevel] = None,
        actor_id: str = "admin"
    ) -> str:
        job_id = f"job_ing_{uuid.uuid4().hex[:10]}"
        job_record = {
            "job_id": job_id,
            "title": title,
            "publisher": publisher,
            "official_url": official_url,
            "status": "QUEUED",
            "actor_id": actor_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "result": None,
            "error": None
        }
        cls._jobs[job_id] = job_record

        # Run in background event loop
        asyncio.create_task(
            cls._execute_ingestion_job(
                job_id=job_id,
                title=title,
                publisher=publisher,
                official_url=official_url,
                jurisdiction=jurisdiction,
                source_type=source_type,
                raw_text=raw_text,
                fetch_remote=fetch_remote,
                trust_level=trust_level,
                actor_id=actor_id
            )
        )

        return job_id

    @classmethod
    async def _execute_ingestion_job(
        cls,
        job_id: str,
        title: str,
        publisher: str,
        official_url: str,
        jurisdiction: str,
        source_type: str,
        raw_text: Optional[str],
        fetch_remote: bool,
        trust_level: Optional[SourceTrustLevel],
        actor_id: str
    ) -> None:
        cls._jobs[job_id]["status"] = "RUNNING"
        try:
            result = await ingestion_pipeline.ingest_source(
                title=title,
                publisher=publisher,
                official_url=official_url,
                jurisdiction=jurisdiction,
                source_type=source_type,
                raw_text=raw_text,
                fetch_remote=fetch_remote,
                trust_level=trust_level,
                actor_id=actor_id
            )
            cls._jobs[job_id]["status"] = "COMPLETED"
            cls._jobs[job_id]["result"] = result
            cls._jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            logger.error(f"Ingestion job {job_id} failed: {exc}")
            cls._jobs[job_id]["status"] = "FAILED"
            cls._jobs[job_id]["error"] = str(exc)
            cls._jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        return cls._jobs.get(job_id)

    @classmethod
    def list_jobs(cls, limit: int = 50) -> list[Dict[str, Any]]:
        return list(cls._jobs.values())[-limit:]

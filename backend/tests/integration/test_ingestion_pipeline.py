"""
Integration tests for 13-stage Ingestion Pipeline.
"""

import asyncio
import pytest
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel
from backend.app.knowledge.ingestion.pipeline import ingestion_pipeline
from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.graph.repository import graph_repository
from backend.app.knowledge.ingestion.vector_writer import vector_store


def test_full_ingestion_pipeline():
    async def _run():
        raw_statute = """
        Section 1. Short title and commencement.
        (1) This Act may be called the Model Civic Governance Act, 2026.
        (2) It shall come into force at once.

        Section 5. Grievance Redressal Officer.
        Every Municipal Corporation shall designate an officer as the Grievance Redressal Officer to receive citizen complaints.
        """

        res = await ingestion_pipeline.ingest_source(
            title="Model Civic Governance Act, 2026",
            publisher="Ministry of Housing and Urban Affairs",
            official_url="https://mohua.gov.in/civic-governance-2026",
            jurisdiction="IN",
            source_type="ACT",
            raw_text=raw_statute,
            trust_level=SourceTrustLevel.OFFICIAL_LEGISLATION,
            actor_id="test_admin"
        )

        assert res["source_id"] is not None
        assert res["version"] == 1
        assert res["chunks_indexed"] == 2
        assert res["entities_indexed"] >= 2
        assert res["verification_status"] == VerificationStatus.ACTIVE.value

        # Verify presence in stores
        source_rec = source_registry.get_source(res["source_id"])
        assert source_rec.title == "Model Civic Governance Act, 2026"

        # Verify vector store records
        chunks = source_registry.get_chunks(res["source_id"])
        for chk in chunks:
            assert chk.chunk_id in vector_store._vectors

    asyncio.run(_run())

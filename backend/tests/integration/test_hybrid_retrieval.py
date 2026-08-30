"""
Integration tests for Hybrid Multi-Modal Retrieval and Evidence Pack Generation.
"""

import asyncio
import pytest
from packages.schemas.contracts import FailSafeState
from backend.app.knowledge.domain.retrieval import RetrievalRequest, FilterCriteria
from backend.app.knowledge.retrieval.hybrid import hybrid_retrieval_service


def test_hybrid_retrieval_rti_appeal():
    async def _run():
        req = RetrievalRequest(
            query="What is the timeline and procedure to file an appeal under Section 19 of RTI Act?",
            filters=FilterCriteria(jurisdiction="IN"),
            top_k=3
        )

        pack = await hybrid_retrieval_service.retrieve(req)

        assert pack.query == req.query
        assert len(pack.items) > 0
        assert pack.fail_safe_state in (FailSafeState.VERIFIED, FailSafeState.PARTIALLY_VERIFIED)
        assert pack.evidence_confidence >= 0.75  # Strong / Good confidence

        top_item = pack.items[0]
        assert "Section 19" in top_item.text or top_item.section_number == "19"
        assert top_item.source_url.startswith("https://")
        assert top_item.provenance["source_title"] == "Right to Information Act, 2005"
        assert top_item.provenance["verification_status"] == "ACTIVE"

    asyncio.run(_run())


def test_hybrid_retrieval_insufficient_evidence():
    async def _run():
        req = RetrievalRequest(
            query="What is the tax rate on quantum teleporters in Antarctica under Martian colonial law?",
            top_k=3
        )

        pack = await hybrid_retrieval_service.retrieve(req)

        assert len(pack.items) == 0
        assert pack.fail_safe_state == FailSafeState.INSUFFICIENT_EVIDENCE
        assert pack.evidence_confidence == 0.0
        assert "Insufficient" in pack.confidence_category

    asyncio.run(_run())

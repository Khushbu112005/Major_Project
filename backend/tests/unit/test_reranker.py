"""
Unit tests for RRF Hybrid Reranker.
Verifies Reciprocal Rank Fusion, trust level weighting, and multi-channel scoring.
"""

import pytest
from backend.app.knowledge.domain.retrieval import RetrievalCandidate
from backend.app.knowledge.domain.source import SourceRecord
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel
from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.retrieval.reranker import RRFHybridReranker


def test_rrf_scoring_and_authority_boost():
    # Setup two mock sources
    source_official = source_registry.register_source(
        title="Official Statutory Act",
        publisher="Ministry of Law",
        official_url="https://indiacode.nic.in/official-act",
        jurisdiction="IN",
        source_type="ACT",
        content="Official law text passage",
        trust_level=SourceTrustLevel.OFFICIAL_LEGISLATION,
        verification_status=VerificationStatus.ACTIVE
    )

    source_secondary = source_registry.register_source(
        title="Secondary Blog Commentary",
        publisher="Legal Blogger",
        official_url="https://blog.example.com/commentary",
        jurisdiction="IN",
        source_type="COMMENTARY",
        content="Secondary commentary passage",
        trust_level=SourceTrustLevel.TRUSTED_SECONDARY_SOURCE,
        verification_status=VerificationStatus.UNVERIFIED
    )

    cand_official = RetrievalCandidate(
        chunk_id="chk_off_1",
        source_id=source_official.source_id,
        source_version=1,
        text="Official law text passage",
        score=0.75,
        retrieval_channel="vector"
    )

    cand_secondary = RetrievalCandidate(
        chunk_id="chk_sec_1",
        source_id=source_secondary.source_id,
        source_version=1,
        text="Secondary commentary passage",
        score=0.85,
        retrieval_channel="vector"
    )

    channel_candidates = {
        "vector": [cand_secondary, cand_official],  # Secondary has higher raw vector similarity
        "lexical": [cand_official]                  # But official matches lexical query
    }

    reranked = RRFHybridReranker.rerank_candidates("statutory query", channel_candidates, top_k=2)
    assert len(reranked) == 2

    # Verify that the official legislation candidate ranks FIRST despite lower raw vector score
    # due to Level 1 trust + ACTIVE verification + multi-channel boost
    top_result = reranked[0]
    assert top_result["chunk_id"] == "chk_off_1"
    assert top_result["trust_level"] == SourceTrustLevel.OFFICIAL_LEGISLATION

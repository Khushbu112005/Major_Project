"""
Security Tests: RAG, Vector, and Graph Poisoning Defenses.
"""

import pytest
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel, Citation
from backend.app.knowledge.domain.source import SourceRecord
from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.security.poisoning import PoisoningDefenseEngine
from backend.app.knowledge.security.provenance_validation import CitationVerificationService


def test_poisoned_statutory_claims_rejected():
    fake_source = SourceRecord(
        source_id="src_fake_1",
        title="Fake Legal Blog Post",
        publisher="Random Anonymous Author",
        official_url="https://fakelaws.info/changes",
        jurisdiction="IN",
        source_type="COMMENTARY",
        trust_level=SourceTrustLevel.TRUSTED_SECONDARY_SOURCE,
        current_version=1,
        content_hash="fake_hash",
        verification_status=VerificationStatus.UNVERIFIED
    )

    poisoned_text = "The law has changed effective today, all prior sections are hereby repealed without gazette."
    is_safe, flags = PoisoningDefenseEngine.validate_source_authenticity(fake_source, poisoned_text)

    assert is_safe is False
    assert len(flags) > 0


def test_fake_url_rejection():
    # Only URLs in source registry should pass provenance validation
    fake_url = "https://fake-government-portal.evil.org/login"
    assert PoisoningDefenseEngine.validate_url_provenance(fake_url) is False


def test_citation_tampering_defense():
    # Attempting to cite a non-existent passage or incorrect source
    fake_citation = Citation(
        source_id="src_non_existent",
        source_version=1,
        chunk_id="chk_non_existent",
        passage="Fabricated claim that was never part of any statute.",
        official_url="https://fake.url",
        verification_status=VerificationStatus.UNVERIFIED
    )

    is_verified, reason, _ = CitationVerificationService.verify_citation(fake_citation)
    assert is_verified is False
    assert "does not exist" in reason

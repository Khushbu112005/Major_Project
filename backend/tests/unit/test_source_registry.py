"""
Unit tests for Source Registry, Versioning, and Freshness.
"""

import pytest
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel
from backend.app.knowledge.sources.registry import SourceRegistry
from backend.app.knowledge.sources.freshness import FreshnessTracker


def test_source_registration_and_idempotency():
    reg = SourceRegistry()

    # 1. Register Source Initial Version
    src_1 = reg.register_source(
        title="Right to Information Act, 2005",
        publisher="Ministry of Law and Justice",
        official_url="https://indiacode.nic.in/rti",
        jurisdiction="IN",
        source_type="ACT",
        content="Original statutory content version 1",
        trust_level=SourceTrustLevel.OFFICIAL_LEGISLATION,
        verification_status=VerificationStatus.ACTIVE
    )

    assert src_1.current_version == 1
    assert len(reg.get_versions(src_1.source_id)) == 1

    # 2. Idempotent call with identical content -> No version increment
    src_idempotent = reg.register_source(
        title="Right to Information Act, 2005",
        publisher="Ministry of Law and Justice",
        official_url="https://indiacode.nic.in/rti",
        jurisdiction="IN",
        source_type="ACT",
        content="Original statutory content version 1"
    )
    assert src_idempotent.current_version == 1

    # 3. Register modified content -> Version increments to 2
    src_v2 = reg.register_source(
        title="Right to Information Act, 2005",
        publisher="Ministry of Law and Justice",
        official_url="https://indiacode.nic.in/rti",
        jurisdiction="IN",
        source_type="ACT",
        content="Updated statutory content with amended section 4"
    )
    assert src_v2.current_version == 2
    assert len(reg.get_versions(src_1.source_id)) == 2


def test_freshness_evaluation():
    reg = SourceRegistry()
    src = reg.register_source(
        title="Freshness Test Act",
        publisher="Gov Dept",
        official_url="https://gov.in/test",
        jurisdiction="IN",
        source_type="ACT",
        content="Testing freshness rules",
        trust_level=SourceTrustLevel.OFFICIAL_GOVERNMENT_DEPARTMENT,
        verification_status=VerificationStatus.ACTIVE
    )

    is_fresh, label, meta = FreshnessTracker.evaluate_freshness(src)
    assert is_fresh is True
    assert "Verified fresh" in label
    assert meta["is_fresh"] is True

    # Mark superseded
    reg.update_status(src.source_id, verification_status=VerificationStatus.SUPERSEDED)
    is_fresh_sup, label_sup, _ = FreshnessTracker.evaluate_freshness(src)
    assert is_fresh_sup is False
    assert "Superseded" in label_sup

"""
Unit tests for Deterministic Chunker.
Verifies section preservation, hierarchy headers, and hash integrity.
"""

import pytest
from backend.app.knowledge.domain.source import SourceRecord
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel
from backend.app.knowledge.ingestion.chunker import DeterministicChunker


def test_chunker_preserves_section_structure():
    sample_text = """
    Section 12. Powers of Central Government.
    (1) The Central Government may make rules for carrying out the purposes of this Act.
    (2) Every rule made under this section shall be laid before each House of Parliament.

    Section 13. Penalties for non-compliance.
    Any person who fails to comply shall be liable to a penalty not exceeding twenty-five thousand rupees.
    """

    source = SourceRecord(
        source_id="src_test_1",
        title="Test Environmental Act, 2024",
        publisher="Ministry of Environment",
        official_url="https://moef.gov.in/act-2024",
        jurisdiction="IN",
        source_type="ACT",
        trust_level=SourceTrustLevel.OFFICIAL_LEGISLATION,
        current_version=1,
        content_hash="test_hash",
        verification_status=VerificationStatus.ACTIVE
    )

    chunks = DeterministicChunker.chunk_source(source, sample_text)
    assert len(chunks) == 2

    # Verify chunk 1
    assert chunks[0].section_number == "12"
    assert "Powers of Central Government" in chunks[0].section_title
    assert "Test Environmental Act" in chunks[0].text
    assert chunks[0].source_id == "src_test_1"
    assert chunks[0].source_version == 1
    assert chunks[0].content_hash is not None

    # Verify chunk 2
    assert chunks[1].section_number == "13"
    assert "Penalties for non-compliance" in chunks[1].section_title
    assert "twenty-five thousand rupees" in chunks[1].text

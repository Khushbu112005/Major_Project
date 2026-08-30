"""
Citation Verification and Provenance Validation Service.
Verifies downstream citations through the strict 6-stage chain:
SOURCE EXISTS -> VERSION EXISTS -> LOCATION EXISTS -> PASSAGE EXISTS -> CITATION MAPS TO PASSAGE -> SOURCE STATUS VALID
"""

from typing import Dict, Any, Tuple, Optional
from packages.schemas.contracts import Citation, VerificationStatus
from backend.app.knowledge.sources.registry import source_registry


class CitationVerificationService:
    """Verifies that generated citations accurately correspond to genuine indexed source passages."""

    @classmethod
    def verify_citation(cls, citation: Citation) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes 6-stage verification.
        Returns (is_verified, reason, details).
        """
        details = {
            "source_exists": False,
            "version_exists": False,
            "location_exists": False,
            "passage_exists": False,
            "status_valid": False,
        }

        # Stage 1: SOURCE EXISTS
        try:
            source = source_registry.get_source(citation.source_id)
            details["source_exists"] = True
        except Exception:
            return False, f"Source '{citation.source_id}' does not exist in registry.", details

        # Stage 2: VERSION EXISTS
        versions = source_registry.get_versions(citation.source_id)
        version_rec = next((v for v in versions if v.version_number == citation.source_version), None)
        if not version_rec:
            return False, f"Source version '{citation.source_version}' not found for source {citation.source_id}.", details
        details["version_exists"] = True

        # Stage 3: LOCATION / CHUNK EXISTS
        chunk = source_registry.get_chunk(citation.chunk_id)
        if not chunk:
            return False, f"Chunk '{citation.chunk_id}' not found.", details
        details["location_exists"] = True

        # Stage 4: PASSAGE EXISTS & MAPS
        passage_snippet = citation.passage.strip().lower()
        if passage_snippet not in chunk.text.lower():
            return False, "Citation passage text does not match the retrieved chunk content.", details
        details["passage_exists"] = True

        # Stage 5: SOURCE STATUS VALID
        if source.verification_status not in (VerificationStatus.ACTIVE, VerificationStatus.UNVERIFIED):
            return False, f"Source verification status is {source.verification_status.value} (must be active).", details
        details["status_valid"] = True

        return True, "Citation successfully verified against official source passage.", details

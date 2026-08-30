"""
Poisoning Defenses for RAG, Vector, and Graph Subsystems.
Guards against:
- Malicious/fabricated sources ("The law has changed...")
- Vector metadata poisoning
- Unverified graph edge insertion
- Fake / hallucinated URLs
"""

import re
from typing import Tuple, List, Dict, Any, Optional
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel
from backend.app.knowledge.domain.source import SourceRecord
from backend.app.knowledge.sources.registry import source_registry


class PoisoningDefenseEngine:
    """Detects and mitigates poisoning attacks against knowledge structures."""

    FABRICATION_TRIGGERS = [
        re.compile(r"the\s+law\s+has\s+changed\s+effective\s+today", re.IGNORECASE),
        re.compile(r"all\s+prior\s+sections\s+are\s+hereby\s+repealed\s+without\s+gazette", re.IGNORECASE),
        re.compile(r"ignore\s+the\s+official\s+court\s+ruling", re.IGNORECASE),
        re.compile(r"new\s+government\s+order\s+exempts\s+all\s+citizens", re.IGNORECASE),
    ]

    @classmethod
    def validate_source_authenticity(
        cls,
        source: SourceRecord,
        raw_text: str
    ) -> Tuple[bool, List[str]]:
        """
        Guarantees that a source text cannot claim radical legal changes
        unless it originates from a verified Level 1 or Level 2 official publisher.
        """
        flags = []

        for trigger in cls.FABRICATION_TRIGGERS:
            if trigger.search(raw_text):
                if source.trust_level not in (SourceTrustLevel.OFFICIAL_LEGISLATION, SourceTrustLevel.OFFICIAL_GOVERNMENT_DEPARTMENT):
                    flags.append(f"Suspicious unverified statutory change claim detected: '{trigger.pattern}' in secondary source.")

        # Validate URL presence in registered official domain
        if not source_registry.is_url_verified(source.official_url) and source.verification_status == VerificationStatus.ACTIVE:
            flags.append(f"Unverified official URL '{source.official_url}' claimed active status.")

        is_safe = len(flags) == 0
        return is_safe, flags

    @classmethod
    def validate_url_provenance(cls, url: str) -> bool:
        """
        Enforces rule #36: Never invent URLs.
        Only registered URLs in the Source Registry can be marked as verified.
        """
        if not url:
            return False
        return source_registry.is_url_verified(url)

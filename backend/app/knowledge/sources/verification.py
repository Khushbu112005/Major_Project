"""
Source Verification and Trust Engine for CivicSphere.
Enforces domain validation, trusted publisher hierarchies, and state transitions (ACTIVE, SUPERSEDED, EXPIRED, UNVERIFIED, BLOCKED).
"""

from typing import Tuple, Optional, List
import re
from urllib.parse import urlparse
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel
from backend.app.knowledge.domain.source import SourceRecord


class VerificationEngine:
    """Verifies source authenticity, publisher legitimacy, and official status."""

    OFFICIAL_GOV_DOMAINS = [
        ".gov.in",
        ".nic.in",
        ".eci.gov.in",
        ".indiacode.nic.in",
        ".egazette.gov.in",
        ".main.sci.gov.in",
        ".judgments.ecourts.gov.in",
        ".parliamentofindia.nic.in",
    ]

    TRUSTED_ORGANIZATIONS = [
        "Ministry of Law and Justice",
        "Legislative Department",
        "Supreme Court of India",
        "High Court",
        "Government of India",
        "Election Commission of India",
        "National Informatics Centre",
    ]

    @classmethod
    def evaluate_trust_level(cls, url: str, publisher: str) -> SourceTrustLevel:
        """Determines the authoritative trust level based on domain and publisher."""
        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        # Level 1: Official Legislation (e.g. IndiaCode / eGazette)
        if any(dom in hostname for dom in [".indiacode.nic.in", ".egazette.gov.in"]):
            return SourceTrustLevel.OFFICIAL_LEGISLATION

        # Level 3: Official Judiciary (e.g. sci.gov.in, ecourts)
        if any(dom in hostname for dom in [".main.sci.gov.in", ".judgments.ecourts.gov.in"]):
            return SourceTrustLevel.OFFICIAL_COURT_JUDICIARY

        # Level 2: Official Government Departments
        if any(hostname.endswith(dom) for dom in cls.OFFICIAL_GOV_DOMAINS):
            return SourceTrustLevel.OFFICIAL_GOVERNMENT_DEPARTMENT

        # Level 4: Official Notification from verified state portal
        if ".gov" in hostname or ".nic" in hostname:
            return SourceTrustLevel.OFFICIAL_NOTIFICATION

        # Level 5: Trusted Secondary Source
        return SourceTrustLevel.TRUSTED_SECONDARY_SOURCE

    @classmethod
    def validate_source_verification(
        cls,
        source: SourceRecord
    ) -> Tuple[VerificationStatus, List[str]]:
        """Evaluates whether a source meets the criteria for ACTIVE verification."""
        warnings: List[str] = []

        # Check if explicitly blocked
        if source.verification_status == VerificationStatus.BLOCKED:
            return VerificationStatus.BLOCKED, ["Source is explicitly blocked by administrative policy."]

        # Check if expired
        if source.expiry_date:
            try:
                # Basic string comparison for ISO dates
                from datetime import datetime, timezone
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                if source.expiry_date < now_str:
                    return VerificationStatus.EXPIRED, [f"Source expired on {source.expiry_date}."]
            except Exception:
                pass

        # Check domain legitimacy
        parsed = urlparse(source.official_url)
        if not parsed.scheme or not parsed.netloc:
            return VerificationStatus.UNVERIFIED, ["Invalid or malformed official URL."]

        # Official trust assessment
        if source.trust_level in [
            SourceTrustLevel.OFFICIAL_LEGISLATION,
            SourceTrustLevel.OFFICIAL_GOVERNMENT_DEPARTMENT,
            SourceTrustLevel.OFFICIAL_COURT_JUDICIARY,
            SourceTrustLevel.OFFICIAL_NOTIFICATION
        ]:
            return VerificationStatus.ACTIVE, warnings

        # Secondary source: Must be marked unverified or secondary
        warnings.append("Source is a secondary or non-governmental source; verification is partial.")
        return VerificationStatus.UNVERIFIED, warnings

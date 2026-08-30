"""
Knowledge Freshness and Stale Source Evaluation.
Computes elapsed duration since verification and flags stale or potentially superseded knowledge.
"""

from typing import Dict, Any, Tuple
from datetime import datetime, timezone
from backend.app.knowledge.domain.source import SourceRecord
from packages.schemas.contracts import VerificationStatus


class FreshnessTracker:
    """Evaluates whether retrieved sources remain fresh or warrant re-verification."""

    DEFAULT_STALE_DAYS_OFFICIAL = 180  # 6 months
    DEFAULT_STALE_DAYS_SECONDARY = 60  # 2 months

    @classmethod
    def evaluate_freshness(cls, source: SourceRecord) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Returns (is_fresh, human_label, metadata)
        """
        now = datetime.now(timezone.utc)
        
        # Check explicit verification status
        if source.verification_status == VerificationStatus.SUPERSEDED:
            return False, "Superseded by newer statutory enactment", {"status": "SUPERSEDED"}
            
        if source.verification_status == VerificationStatus.EXPIRED:
            return False, f"Expired on {source.expiry_date}", {"status": "EXPIRED", "expiry_date": source.expiry_date}

        if source.verification_status == VerificationStatus.BLOCKED:
            return False, "Blocked by safety/security policy", {"status": "BLOCKED"}

        # Calculate time since last retrieval/verification
        ref_time_str = source.last_verified_at or source.retrieved_at
        try:
            ref_dt = datetime.fromisoformat(ref_time_str.replace("Z", "+00:00"))
            days_elapsed = (now - ref_dt).days
        except Exception:
            days_elapsed = 0

        max_days = cls.DEFAULT_STALE_DAYS_OFFICIAL if source.trust_level <= 3 else cls.DEFAULT_STALE_DAYS_SECONDARY
        
        is_fresh = days_elapsed <= max_days
        label = "Verified fresh" if is_fresh else f"Potentially stale ({days_elapsed} days since verification)"

        metadata = {
            "days_since_verification": days_elapsed,
            "is_fresh": is_fresh,
            "last_verified_at": ref_time_str,
            "effective_date": source.effective_date,
            "version": source.current_version,
            "trust_level": source.trust_level.value if hasattr(source.trust_level, 'value') else source.trust_level,
        }

        return is_fresh, label, metadata

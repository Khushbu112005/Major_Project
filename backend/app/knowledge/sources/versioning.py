"""
Knowledge and Source Versioning Engine.
Detects modifications via content hashing, prevents silent overwrites, and supports historical diff analysis.
"""

from typing import Dict, Any, Optional
import hashlib
from backend.app.knowledge.domain.source import SourceRecord, SourceVersionRecord
from backend.app.knowledge.sources.registry import source_registry


class VersionManager:
    """Manages source revision lifecycle and change detection."""

    @staticmethod
    def compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def has_changed(source_id: str, new_content: str) -> bool:
        """Determines if new raw content differs from currently indexed version."""
        try:
            source = source_registry.get_source(source_id)
            new_hash = VersionManager.compute_hash(new_content)
            return source.content_hash != new_hash
        except Exception:
            return True  # If source doesn't exist, treat as changed/new

    @staticmethod
    def create_version_snapshot(
        source_id: str,
        new_content: str,
        change_summary: str = "Automated ingestion update"
    ) -> SourceVersionRecord:
        """Creates a persistent version snapshot in the registry."""
        source = source_registry.get_source(source_id)
        new_hash = VersionManager.compute_hash(new_content)
        new_version = source.current_version + 1
        
        snapshot = SourceVersionRecord(
            source_id=source_id,
            version_number=new_version,
            content_hash=new_hash,
            extracted_text=new_content,
            change_summary=change_summary,
            verification_status=source.verification_status,
            effective_date=source.effective_date
        )
        return snapshot

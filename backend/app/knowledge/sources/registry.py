"""
First-Class Source Registry for CivicSphere.
Tracks all legal, civic, and governmental sources with their trust level, verification status, and provenance.
"""

from typing import Dict, List, Optional
import hashlib
from datetime import datetime, timezone

from packages.schemas.contracts import VerificationStatus, SourceTrustLevel, IngestionStatus
from backend.app.knowledge.domain.source import SourceRecord, SourceVersionRecord, ChunkRecord
from backend.app.common.errors import NotFoundException, IngestionValidationException


class SourceRegistry:
    """In-memory & persistent registry tracking trusted civic knowledge sources."""

    def __init__(self):
        self._sources: Dict[str, SourceRecord] = {}
        self._versions: Dict[str, List[SourceVersionRecord]] = {}
        self._chunks: Dict[str, List[ChunkRecord]] = {}
        self._verified_urls: set = set()

    def register_source(
        self,
        title: str,
        publisher: str,
        official_url: str,
        jurisdiction: str,
        source_type: str,
        content: str,
        trust_level: SourceTrustLevel = SourceTrustLevel.TRUSTED_SECONDARY_SOURCE,
        publication_date: Optional[str] = None,
        effective_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
        verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
        metadata: Optional[Dict] = None
    ) -> SourceRecord:
        """Registers a new source or increments version if content changed."""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        # Check if identical source title + publisher exists
        existing_source = None
        for s in self._sources.values():
            if s.title.strip().lower() == title.strip().lower() and s.publisher.strip().lower() == publisher.strip().lower():
                existing_source = s
                break

        if existing_source:
            # Check if content has changed
            if existing_source.content_hash == content_hash:
                # Idempotent: Same content, no new version needed
                return existing_source
            
            # Content changed -> create new version
            new_version_num = existing_source.current_version + 1
            existing_source.current_version = new_version_num
            existing_source.content_hash = content_hash
            existing_source.updated_at = datetime.now(timezone.utc).isoformat()
            
            # Record historical version
            version_rec = SourceVersionRecord(
                source_id=existing_source.source_id,
                version_number=new_version_num,
                content_hash=content_hash,
                extracted_text=content,
                effective_date=effective_date or existing_source.effective_date,
                verification_status=verification_status,
                change_summary=f"Updated to version {new_version_num}"
            )
            self._versions[existing_source.source_id].append(version_rec)
            return existing_source

        # Create brand new source
        source_id = f"src_{hashlib.md5(f'{title}_{publisher}_{jurisdiction}'.encode()).hexdigest()[:12]}"
        source_rec = SourceRecord(
            source_id=source_id,
            title=title,
            publisher=publisher,
            official_url=official_url,
            jurisdiction=jurisdiction,
            source_type=source_type,
            trust_level=trust_level,
            current_version=1,
            content_hash=content_hash,
            verification_status=verification_status,
            ingestion_status=IngestionStatus.PENDING,
            publication_date=publication_date,
            effective_date=effective_date,
            expiry_date=expiry_date,
            metadata=metadata or {}
        )

        version_rec = SourceVersionRecord(
            source_id=source_id,
            version_number=1,
            content_hash=content_hash,
            extracted_text=content,
            effective_date=effective_date,
            verification_status=verification_status,
            change_summary="Initial source registration"
        )

        self._sources[source_id] = source_rec
        self._versions[source_id] = [version_rec]
        self._chunks[source_id] = []
        
        if verification_status == VerificationStatus.ACTIVE:
            self._verified_urls.add(official_url)
            
        return source_rec

    def get_source(self, source_id: str) -> SourceRecord:
        if source_id not in self._sources:
            raise NotFoundException(f"Source with id '{source_id}' not found in registry.")
        return self._sources[source_id]

    def list_sources(
        self,
        jurisdiction: Optional[str] = None,
        verification_status: Optional[VerificationStatus] = None,
        limit: int = 50
    ) -> List[SourceRecord]:
        results = list(self._sources.values())
        if jurisdiction:
            results = [s for s in results if s.jurisdiction.lower() == jurisdiction.lower()]
        if verification_status:
            results = [s for s in results if s.verification_status == verification_status]
        return results[:limit]

    def get_versions(self, source_id: str) -> List[SourceVersionRecord]:
        if source_id not in self._sources:
            raise NotFoundException(f"Source with id '{source_id}' not found.")
        return self._versions.get(source_id, [])

    def store_chunks(self, source_id: str, chunks: List[ChunkRecord]) -> None:
        self._chunks[source_id] = chunks

    def get_chunks(self, source_id: str, version: Optional[int] = None) -> List[ChunkRecord]:
        all_chunks = self._chunks.get(source_id, [])
        if version is not None:
            return [c for c in all_chunks if c.source_version == version]
        return all_chunks

    def get_chunk(self, chunk_id: str) -> Optional[ChunkRecord]:
        for chunk_list in self._chunks.values():
            for c in chunk_list:
                if c.chunk_id == chunk_id:
                    return c
        return None

    def update_status(
        self,
        source_id: str,
        verification_status: Optional[VerificationStatus] = None,
        ingestion_status: Optional[IngestionStatus] = None
    ) -> SourceRecord:
        source = self.get_source(source_id)
        if verification_status:
            source.verification_status = verification_status
            source.last_verified_at = datetime.now(timezone.utc).isoformat()
            if verification_status == VerificationStatus.ACTIVE:
                self._verified_urls.add(source.official_url)
            elif source.official_url in self._verified_urls:
                self._verified_urls.discard(source.official_url)
        if ingestion_status:
            source.ingestion_status = ingestion_status
        source.updated_at = datetime.now(timezone.utc).isoformat()
        return source

    def is_url_verified(self, url: str) -> bool:
        """Strict check that a source URL is in the verified registry."""
        return url in self._verified_urls

    def clear(self) -> None:
        """Reset registry for testing."""
        self._sources.clear()
        self._versions.clear()
        self._chunks.clear()
        self._verified_urls.clear()


# Global Singleton Registry Instance
source_registry = SourceRegistry()

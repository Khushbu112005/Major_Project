"""
CivicSphere 13-Stage Knowledge Ingestion Pipeline.
Executes deterministic processing:
SOURCE -> FETCH -> VALIDATE -> PARSE -> CLEAN -> METADATA -> CHUNK -> ENTITY EXTRACTION ->
RELATIONSHIP EXTRACTION -> EMBEDDING -> GRAPH INSERTION -> VECTOR INSERTION -> REGISTRY UPDATE
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import logging

from packages.schemas.contracts import VerificationStatus, SourceTrustLevel, IngestionStatus
from backend.app.common.audit import AuditManager
from backend.app.common.errors import CivicSphereException, SecurityBlockedException, IngestionValidationException
from backend.app.knowledge.domain.source import SourceRecord, ChunkRecord
from backend.app.knowledge.domain.entities import EntityDomainModel
from backend.app.knowledge.domain.relationships import RelationshipDomainModel

from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.sources.verification import VerificationEngine
from backend.app.knowledge.sources.freshness import FreshnessTracker
from backend.app.knowledge.sources.versioning import VersionManager

from backend.app.knowledge.ingestion.validator import IngestionValidator
from backend.app.knowledge.ingestion.fetcher import SourceFetcher
from backend.app.knowledge.ingestion.cleaner import ContentCleaner, StructuralLegalParser
from backend.app.knowledge.ingestion.chunker import DeterministicChunker
from backend.app.knowledge.ingestion.entity_extractor import EntityExtractor
from backend.app.knowledge.ingestion.relationship_extractor import RelationshipExtractor
from backend.app.knowledge.ingestion.embedder import ChunkEmbedder
from backend.app.knowledge.ingestion.graph_writer import GraphWriter
from backend.app.knowledge.ingestion.vector_writer import vector_store

logger = logging.getLogger("civicsphere.ingestion")


class IngestionPipeline:
    """End-to-end knowledge ingestion orchestrator."""

    def __init__(self, embedder: Optional[ChunkEmbedder] = None):
        self.embedder = embedder or ChunkEmbedder()

    async def ingest_source(
        self,
        title: str,
        publisher: str,
        official_url: str,
        jurisdiction: str,
        source_type: str,
        raw_text: Optional[str] = None,
        fetch_remote: bool = False,
        trust_level: Optional[SourceTrustLevel] = None,
        publication_date: Optional[str] = None,
        effective_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
        actor_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Runs the full 13-stage ingestion sequence.
        """
        # Step 1 & 2: FETCH & VALIDATE URL
        source_content = raw_text or ""
        fetch_metadata = {}
        
        if fetch_remote:
            try:
                source_content, fetch_metadata = await SourceFetcher.fetch_source_content(official_url)
            except SecurityBlockedException as sbe:
                AuditManager.record_security_event(
                    threat_type="SSRF_INGESTION_ATTEMPT",
                    severity="HIGH",
                    endpoint="/knowledge/ingestion",
                    action_taken="BLOCKED",
                    actor_id=actor_id,
                    payload_sample=official_url
                )
                raise sbe

        if not source_content.strip():
            raise IngestionValidationException("Source content cannot be empty.")

        # Step 3: TRUST & VERIFICATION EVALUATION
        computed_trust = trust_level or VerificationEngine.evaluate_trust_level(official_url, publisher)
        
        # Step 4: REGISTER IN SOURCE REGISTRY
        source_rec = source_registry.register_source(
            title=title,
            publisher=publisher,
            official_url=official_url,
            jurisdiction=jurisdiction,
            source_type=source_type,
            content=source_content,
            trust_level=computed_trust,
            publication_date=publication_date,
            effective_date=effective_date,
            expiry_date=expiry_date,
            verification_status=VerificationStatus.UNVERIFIED,
            metadata=fetch_metadata
        )

        source_registry.update_status(source_rec.source_id, ingestion_status=IngestionStatus.PROCESSING)

        try:
            # Step 5: VERIFICATION STATUS DETERMINATION
            v_status, v_warnings = VerificationEngine.validate_source_verification(source_rec)
            source_registry.update_status(source_rec.source_id, verification_status=v_status)
            source_rec.verification_status = v_status

            # Step 6: CLEAN & PARSE
            cleaned_text = ContentCleaner.clean_text(source_content)

            # Step 7: DETERMINISTIC CHUNKING
            chunks = DeterministicChunker.chunk_source(source_rec, cleaned_text)
            source_registry.store_chunks(source_rec.source_id, chunks)

            # Step 8 & 9: ENTITY & RELATIONSHIP EXTRACTION
            all_entities: List[EntityDomainModel] = []
            all_relationships: List[RelationshipDomainModel] = []

            for chunk in chunks:
                chunk_entities = EntityExtractor.extract_entities_from_chunk(chunk)
                chunk_relationships = RelationshipExtractor.extract_relationships(chunk, chunk_entities)
                all_entities.extend(chunk_entities)
                all_relationships.extend(chunk_relationships)

            # Deduplicate entities across chunks for this source
            deduped_entities_map = {}
            for ent in all_entities:
                k = ent.canonical_id or ent.get_canonical_key()
                if k not in deduped_entities_map:
                    deduped_entities_map[k] = ent
                else:
                    for sid in ent.source_ids:
                        if sid not in deduped_entities_map[k].source_ids:
                            deduped_entities_map[k].source_ids.append(sid)
            unique_entities = list(deduped_entities_map.values())

            # Step 10: EMBEDDINGS
            source_registry.update_status(source_rec.source_id, ingestion_status=IngestionStatus.EMBEDDING)
            embedded_chunks = await self.embed_chunks_and_store(chunks)

            # Step 11: GRAPH INSERTION
            source_registry.update_status(source_rec.source_id, ingestion_status=IngestionStatus.INDEXING)
            nodes_written, edges_written = GraphWriter.write_extracted_graph(unique_entities, all_relationships)

            # Step 12: VECTOR INSERTION
            for chunk, vec in embedded_chunks:
                vector_store.store_chunk_mapping(chunk, vec)

            # Step 13: REGISTRY FINALIZATION & AUDIT
            source_registry.update_status(source_rec.source_id, ingestion_status=IngestionStatus.COMPLETED)

            AuditManager.record_event(
                event_type="KNOWLEDGE_INGESTION_COMPLETED",
                actor_id=actor_id,
                role="system",
                action="INGEST_SOURCE",
                resource_type="SOURCE",
                resource_id=source_rec.source_id,
                details={
                    "title": source_rec.title,
                    "version": source_rec.current_version,
                    "chunks_count": len(chunks),
                    "entities_count": nodes_written,
                    "relationships_count": edges_written,
                    "verification_status": v_status.value
                }
            )

            return {
                "source_id": source_rec.source_id,
                "version": source_rec.current_version,
                "verification_status": v_status.value,
                "chunks_indexed": len(chunks),
                "entities_indexed": nodes_written,
                "relationships_indexed": edges_written,
                "warnings": v_warnings
            }

        except Exception as exc:
            source_registry.update_status(source_rec.source_id, ingestion_status=IngestionStatus.FAILED)
            AuditManager.record_event(
                event_type="KNOWLEDGE_INGESTION_FAILED",
                actor_id=actor_id,
                role="system",
                action="INGEST_SOURCE",
                resource_type="SOURCE",
                resource_id=source_rec.source_id,
                details={"error": str(exc)}
            )
            raise exc

    async def embed_chunks_and_store(self, chunks: List[ChunkRecord]) -> List[Tuple[ChunkRecord, List[float]]]:
        return await self.embedder.embed_chunks(chunks)


# Global Singleton Pipeline Instance
ingestion_pipeline = IngestionPipeline()

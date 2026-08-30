"""
Evidence Pack Generator and Confidence Calculator.
Assembles ranked evidence items, computes evidence confidence, detects conflicts,
and enforces fail-safe states.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import logging

from packages.schemas.contracts import VerificationStatus, SourceTrustLevel, FailSafeState
from backend.app.common.config import settings
from backend.app.knowledge.domain.evidence import EvidenceItem, EvidencePack, EvidenceConflict, GraphContextItem
from backend.app.knowledge.domain.provenance import ProvenanceTrace
from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.graph.repository import graph_repository

logger = logging.getLogger("civicsphere.evidence")


class EvidencePackBuilder:
    """Builds formal Evidence Packs with provenance, confidence, and conflict detection."""

    @classmethod
    def build_evidence_pack(
        cls,
        query: str,
        reranked_items: List[Dict[str, Any]],
        retrieval_metadata: Optional[Dict[str, Any]] = None
    ) -> EvidencePack:
        warnings: List[str] = []
        conflicts: List[EvidenceConflict] = []
        evidence_items: List[EvidenceItem] = []

        if not reranked_items:
            return EvidencePack(
                query=query,
                query_summary="No matching evidence found in verified knowledge repository.",
                fail_safe_state=FailSafeState.INSUFFICIENT_EVIDENCE,
                items=[],
                conflicts=[],
                warnings=["No trusted civic sources matched the search criteria."],
                evidence_confidence=0.0,
                confidence_category="Insufficient",
                retrieval_metadata=retrieval_metadata or {}
            )

        # 1. Build Evidence Items with Provenance and Graph Context
        for item in reranked_items:
            cand = item["candidate"]
            lex_score = item["channel_scores"].get("lexical", 0.0)
            vec_score = item["channel_scores"].get("vector", 0.0)
            grp_score = item["channel_scores"].get("graph", 0.0)

            # Filter out spurious candidates with negligible relevance across all channels
            if lex_score < 2.0 and vec_score < 0.12 and grp_score == 0.0:
                continue

            chunk = source_registry.get_chunk(cand.chunk_id)
            if not chunk:
                continue

            try:
                source = source_registry.get_source(chunk.source_id)
            except Exception:
                continue

            # Graph context expansion for this chunk
            graph_ctx: List[GraphContextItem] = []
            if chunk.section_number:
                # Look for relationships connected to section
                sec_entities = graph_repository.find_entities_by_name(f"Section {chunk.section_number}")
                for ent in sec_entities:
                    _, rels = graph_repository.get_neighborhood(ent.entity_id, max_depth=1)
                    for r in rels:
                        src_node = graph_repository._nodes.get(r.source_entity_id)
                        tgt_node = graph_repository._nodes.get(r.target_entity_id)
                        if src_node and tgt_node:
                            graph_ctx.append(
                                GraphContextItem(
                                    relationship_id=r.relationship_id,
                                    source_entity_name=src_node.name,
                                    source_entity_type=src_node.entity_type.value,
                                    relation_type=r.relation_type.value,
                                    target_entity_name=tgt_node.name,
                                    target_entity_type=tgt_node.entity_type.value,
                                    confidence=r.confidence
                                )
                            )

            provenance_trace = ProvenanceTrace(
                source_id=source.source_id,
                source_title=source.title,
                source_version=source.current_version,
                chunk_id=chunk.chunk_id,
                official_url=source.official_url,
                publisher=source.publisher,
                jurisdiction=source.jurisdiction,
                trust_level=source.trust_level,
                verification_status=source.verification_status,
                content_hash=chunk.content_hash,
                section_number=chunk.section_number,
                section_title=chunk.section_title,
                page_number=chunk.page_number
            )

            evidence_items.append(
                EvidenceItem(
                    source_id=source.source_id,
                    source_version=source.current_version,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    source_title=source.title,
                    source_url=source.official_url,
                    source_type=source.source_type,
                    trust_level=source.trust_level,
                    verification_status=source.verification_status,
                    jurisdiction=source.jurisdiction,
                    effective_date=source.effective_date,
                    section_number=chunk.section_number,
                    section_title=chunk.section_title,
                    lexical_score=item["channel_scores"].get("lexical", 0.0),
                    vector_score=item["channel_scores"].get("vector", 0.0),
                    graph_score=item["channel_scores"].get("graph", 0.0),
                    rrf_score=item["rrf_score"],
                    rerank_score=item["final_rerank_score"],
                    graph_context=graph_ctx[:5],
                    provenance=provenance_trace.model_dump(),
                    metadata=chunk.metadata
                )
            )

        if not evidence_items:
            return EvidencePack(
                query=query,
                query_summary="No matching evidence found in verified knowledge repository.",
                fail_safe_state=FailSafeState.INSUFFICIENT_EVIDENCE,
                items=[],
                conflicts=[],
                warnings=["Insufficient verified evidence to provide a reliable answer."],
                evidence_confidence=0.0,
                confidence_category="Insufficient",
                retrieval_metadata=retrieval_metadata or {}
            )

        # 2. Conflict Detection across retrieved items
        conflicts = cls._detect_source_conflicts(evidence_items)
        if conflicts:
            warnings.append(f"Detected {len(conflicts)} conflicting provision(s) across retrieved sources.")

        # 3. Compute Evidence Confidence
        confidence_score, confidence_category = cls._compute_confidence(evidence_items, conflicts)

        # 4. Fail-Safe State Evaluation
        fail_safe_state = FailSafeState.VERIFIED
        if confidence_score < settings.EVIDENCE_CONFIDENCE_THRESHOLD_LIMITED:
            fail_safe_state = FailSafeState.INSUFFICIENT_EVIDENCE
            warnings.append("Insufficient verified evidence to provide a reliable answer.")
        elif conflicts:
            fail_safe_state = FailSafeState.CONFLICT
        elif all(i.verification_status == VerificationStatus.UNVERIFIED for i in evidence_items):
            fail_safe_state = FailSafeState.UNVERIFIED_SOURCE
            warnings.append("Evidence retrieved from unverified secondary sources only.")
        elif any(i.verification_status == VerificationStatus.SUPERSEDED for i in evidence_items):
            warnings.append("Some retrieved sources are superseded by newer statutory notifications.")
            fail_safe_state = FailSafeState.PARTIALLY_VERIFIED
        elif confidence_category == "Good" or confidence_category == "Limited":
            fail_safe_state = FailSafeState.PARTIALLY_VERIFIED

        return EvidencePack(
            query=query,
            query_summary=f"Retrieved {len(evidence_items)} evidence item(s) across official sources.",
            fail_safe_state=fail_safe_state,
            items=evidence_items,
            conflicts=conflicts,
            warnings=warnings,
            evidence_confidence=confidence_score,
            confidence_category=confidence_category,
            retrieval_metadata=retrieval_metadata or {}
        )

    @classmethod
    def _compute_confidence(
        cls,
        items: List[EvidenceItem],
        conflicts: List[EvidenceConflict]
    ) -> Tuple[float, str]:
        """Calculates evidence support confidence based on official trust, verification status, and multi-modal agreement."""
        if not items:
            return 0.0, "Insufficient"

        # Factors:
        # 1. Authority level of top item
        top_item = items[0]
        base_score = 0.50

        if top_item.trust_level == SourceTrustLevel.OFFICIAL_LEGISLATION:
            base_score += 0.30
        elif top_item.trust_level in (SourceTrustLevel.OFFICIAL_GOVERNMENT_DEPARTMENT, SourceTrustLevel.OFFICIAL_COURT_JUDICIARY):
            base_score += 0.25
        elif top_item.trust_level == SourceTrustLevel.OFFICIAL_NOTIFICATION:
            base_score += 0.20
        else:
            base_score += 0.05

        # 2. Verification status
        if top_item.verification_status == VerificationStatus.ACTIVE:
            base_score += 0.15
        elif top_item.verification_status == VerificationStatus.SUPERSEDED:
            base_score -= 0.30

        # 3. Multi-modal channel reinforcement
        channels_active = sum(1 for ch in [top_item.lexical_score > 0, top_item.vector_score > 0, top_item.graph_score > 0] if ch)
        if channels_active >= 2:
            base_score += 0.05

        # 4. Penalty for unresolved conflicts
        if conflicts:
            base_score -= 0.20

        # Clamp between 0.0 and 0.99
        final_confidence = round(max(0.05, min(0.98, base_score)), 2)

        if final_confidence >= settings.EVIDENCE_CONFIDENCE_THRESHOLD_STRONG:
            category = "Strong"
        elif final_confidence >= settings.EVIDENCE_CONFIDENCE_THRESHOLD_GOOD:
            category = "Good"
        elif final_confidence >= settings.EVIDENCE_CONFIDENCE_THRESHOLD_LIMITED:
            category = "Limited"
        else:
            category = "Insufficient"

        return final_confidence, category

    @classmethod
    def _detect_source_conflicts(cls, items: List[EvidenceItem]) -> List[EvidenceConflict]:
        """Identifies conflicting statements on common topics (e.g. fees, deadlines, penalties)."""
        conflicts: List[EvidenceConflict] = []
        if len(items) < 2:
            return conflicts

        # Compare pairs of items from different sources
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                item_a = items[i]
                item_b = items[j]

                if item_a.source_id != item_b.source_id:
                    # Check if one is marked superseded by the other or conflicting effective dates
                    if item_a.verification_status == VerificationStatus.SUPERSEDED and item_b.verification_status == VerificationStatus.ACTIVE:
                        conflicts.append(
                            EvidenceConflict(
                                topic="Statutory Version Amendment",
                                source_a_id=item_a.source_id,
                                source_a_version=item_a.source_version,
                                source_a_text=item_a.text[:150],
                                source_b_id=item_b.source_id,
                                source_b_version=item_b.source_version,
                                source_b_text=item_b.text[:150],
                                explanation=f"Source '{item_a.source_title}' is superseded by newer enactment '{item_b.source_title}'.",
                                severity="HIGH"
                            )
                        )

        return conflicts

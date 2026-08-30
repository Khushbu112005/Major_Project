"""
Cross-Feature Reranker with Reciprocal Rank Fusion (RRF).
Merges candidates from Lexical, Vector, and Graph retrieval channels,
incorporating source trust levels, verification status, freshness, and structural precision.
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict
from backend.app.common.config import settings
from backend.app.knowledge.domain.retrieval import RetrievalCandidate
from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.sources.freshness import FreshnessTracker
from packages.schemas.contracts import VerificationStatus, SourceTrustLevel


class RRFHybridReranker:
    """Combines multi-modal candidate rankings using RRF and domain trust weighting."""

    RRF_K = settings.RRF_K  # 60 by default

    @classmethod
    def reciprocal_rank_fusion(
        cls,
        channel_candidates: Dict[str, List[RetrievalCandidate]]
    ) -> List[Tuple[str, float, RetrievalCandidate, Dict[str, float]]]:
        """
        Applies RRF across lexical, vector, and graph candidate lists.
        Returns sorted list of (chunk_id, rrf_score, primary_candidate, channel_scores)
        """
        rrf_scores: Dict[str, float] = defaultdict(float)
        channel_scores: Dict[str, Dict[str, float]] = defaultdict(dict)
        candidate_map: Dict[str, RetrievalCandidate] = {}

        for channel, candidates in channel_candidates.items():
            for rank, cand in enumerate(candidates, start=1):
                chunk_id = cand.chunk_id
                # Standard RRF formula
                score_contribution = 1.0 / (cls.RRF_K + rank)
                rrf_scores[chunk_id] += score_contribution
                channel_scores[chunk_id][channel] = cand.score
                if chunk_id not in candidate_map or channel == "lexical":
                    candidate_map[chunk_id] = cand

        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for chunk_id, rrf_score in sorted_chunks:
            results.append((
                chunk_id,
                rrf_score,
                candidate_map[chunk_id],
                channel_scores[chunk_id]
            ))

        return results

    @classmethod
    def rerank_candidates(
        cls,
        query: str,
        channel_candidates: Dict[str, List[RetrievalCandidate]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Applies RRF followed by domain authority and freshness boosting.
        """
        fused = cls.reciprocal_rank_fusion(channel_candidates)
        reranked_items: List[Dict[str, Any]] = []

        for chunk_id, rrf_score, cand, ch_scores in fused:
            # 1. Base score normalized from RRF
            final_score = rrf_score * 100.0

            # 2. Fetch authoritative source metadata
            try:
                source = source_registry.get_source(cand.source_id)
                trust_level = source.trust_level
                v_status = source.verification_status
                is_fresh, _, _ = FreshnessTracker.evaluate_freshness(source)
            except Exception:
                trust_level = SourceTrustLevel.TRUSTED_SECONDARY_SOURCE
                v_status = VerificationStatus.UNVERIFIED
                is_fresh = True

            # 3. Source Trust Multiplier
            if trust_level == SourceTrustLevel.OFFICIAL_LEGISLATION:
                final_score *= 1.35
            elif trust_level in (SourceTrustLevel.OFFICIAL_GOVERNMENT_DEPARTMENT, SourceTrustLevel.OFFICIAL_COURT_JUDICIARY):
                final_score *= 1.20
            elif trust_level == SourceTrustLevel.OFFICIAL_NOTIFICATION:
                final_score *= 1.10
            else:
                final_score *= 0.85

            # 4. Verification Status Multiplier
            if v_status == VerificationStatus.ACTIVE:
                final_score *= 1.25
            elif v_status == VerificationStatus.UNVERIFIED:
                final_score *= 0.70
            elif v_status in (VerificationStatus.SUPERSEDED, VerificationStatus.EXPIRED):
                final_score *= 0.20  # Heavily penalize outdated or superseded law

            # 5. Freshness penalty
            if not is_fresh:
                final_score *= 0.80

            # 6. Multi-channel agreement bonus (if retrieved by both vector AND lexical/graph)
            if len(ch_scores) >= 2:
                final_score *= 1.15

            reranked_items.append({
                "chunk_id": chunk_id,
                "candidate": cand,
                "rrf_score": rrf_score,
                "final_rerank_score": final_score,
                "channel_scores": ch_scores,
                "trust_level": trust_level,
                "verification_status": v_status,
                "is_fresh": is_fresh
            })

        # Sort descending by final score
        reranked_items.sort(key=lambda x: x["final_rerank_score"], reverse=True)
        return reranked_items[:top_k]

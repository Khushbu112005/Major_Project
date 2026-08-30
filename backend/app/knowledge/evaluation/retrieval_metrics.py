"""
Evaluation Metrics for Retrieval and Evidence Systems.
Computes:
- Precision@K, Recall@K, MRR, NDCG@K
- Groundedness Score
- Citation Completeness & Citation Correctness
- Hallucination Rate
"""

from typing import List, Set, Dict, Any, Tuple
import math
import numpy as np


class RetrievalMetricsCalculator:
    """Calculates retrieval, ranking, and groundedness evaluation metrics."""

    @staticmethod
    def precision_at_k(retrieved_chunk_ids: List[str], ground_truth_chunk_ids: Set[str], k: int) -> float:
        if k <= 0 or not retrieved_chunk_ids:
            return 0.0
        top_k = retrieved_chunk_ids[:k]
        hits = sum(1 for cid in top_k if cid in ground_truth_chunk_ids)
        return float(hits / k)

    @staticmethod
    def recall_at_k(retrieved_chunk_ids: List[str], ground_truth_chunk_ids: Set[str], k: int) -> float:
        if not ground_truth_chunk_ids or not retrieved_chunk_ids or k <= 0:
            return 0.0
        top_k = retrieved_chunk_ids[:k]
        hits = sum(1 for cid in top_k if cid in ground_truth_chunk_ids)
        return float(hits / len(ground_truth_chunk_ids))

    @staticmethod
    def mean_reciprocal_rank(retrieved_chunk_ids: List[str], ground_truth_chunk_ids: Set[str]) -> float:
        for rank, cid in enumerate(retrieved_chunk_ids, start=1):
            if cid in ground_truth_chunk_ids:
                return float(1.0 / rank)
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved_chunk_ids: List[str], relevance_scores: Dict[str, float], k: int) -> float:
        """Computes Normalized Discounted Cumulative Gain at rank K."""
        if k <= 0 or not retrieved_chunk_ids:
            return 0.0

        top_k = retrieved_chunk_ids[:k]
        dcg = 0.0
        for i, cid in enumerate(top_k):
            rel = relevance_scores.get(cid, 0.0)
            dcg += (2.0**rel - 1.0) / math.log2(i + 2)

        # Ideal DCG
        ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
        idcg = 0.0
        for i, rel in enumerate(ideal_scores):
            idcg += (2.0**rel - 1.0) / math.log2(i + 2)

        if idcg == 0.0:
            return 0.0
        return float(dcg / idcg)

    @staticmethod
    def compute_groundedness(claims: List[str], evidence_text: str) -> Tuple[float, float]:
        """
        Computes Groundedness and Hallucination Rate.
        Groundedness = supported_claims / total_claims
        Hallucination Rate = 1.0 - Groundedness
        """
        if not claims:
            return 1.0, 0.0

        evidence_lower = evidence_text.lower()
        supported = 0

        for claim in claims:
            claim_words = [w for w in claim.lower().split() if len(w) > 3]
            if not claim_words:
                continue
            # If significant portion of key words exist in evidence
            matches = sum(1 for w in claim_words if w in evidence_lower)
            if matches / len(claim_words) >= 0.5:
                supported += 1

        groundedness = supported / len(claims)
        hallucination_rate = 1.0 - groundedness
        return round(groundedness, 4), round(hallucination_rate, 4)

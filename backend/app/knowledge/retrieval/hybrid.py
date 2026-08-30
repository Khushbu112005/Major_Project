"""
Hybrid Retrieval Orchestrator for CivicSphere.
Coordinates Parallel Multi-Modal Retrieval:
LEXICAL SEARCH + VECTOR SEARCH + GRAPH TRAVERSAL + METADATA FILTERING -> RRF -> RERANK -> EVIDENCE PACK
"""

import asyncio
from typing import Dict, Any, Optional
import uuid
import logging

from backend.app.common.telemetry import LatencyTimer, RetrievalMetrics
from backend.app.common.audit import AuditManager
from backend.app.knowledge.domain.retrieval import RetrievalRequest, RetrievalCandidate, FilterCriteria
from backend.app.knowledge.domain.evidence import EvidencePack
from backend.app.knowledge.retrieval.keyword import LexicalRetriever
from backend.app.knowledge.retrieval.vector import VectorRetriever
from backend.app.knowledge.retrieval.graph import GraphRetriever
from backend.app.knowledge.retrieval.reranker import RRFHybridReranker
from backend.app.knowledge.retrieval.evidence_pack import EvidencePackBuilder

logger = logging.getLogger("civicsphere.retrieval")


class HybridRetrievalService:
    """Orchestrates multi-channel retrieval and evidence pack compilation."""

    def __init__(self, vector_retriever: Optional[VectorRetriever] = None):
        self.vector_retriever = vector_retriever or VectorRetriever()

    async def retrieve(
        self,
        request: RetrievalRequest,
        actor_id: str = "anonymous"
    ) -> EvidencePack:
        request_id = str(uuid.uuid4())
        metrics = RetrievalMetrics(request_id=request_id)
        channel_candidates: Dict[str, list[RetrievalCandidate]] = {}

        with LatencyTimer() as total_timer:
            # 1. Lexical Search
            if request.include_lexical:
                with LatencyTimer() as lex_timer:
                    lex_cands = LexicalRetriever.search(
                        query=request.query,
                        filters=request.filters,
                        top_k=request.top_k * 2
                    )
                metrics.lexical_latency_ms = lex_timer.elapsed_ms
                metrics.lexical_candidates_count = len(lex_cands)
                channel_candidates["lexical"] = lex_cands

            # 2. Vector Search
            if request.include_vector:
                with LatencyTimer() as vec_timer:
                    vec_cands = await self.vector_retriever.search(
                        query=request.query,
                        filters=request.filters,
                        top_k=request.top_k * 2
                    )
                metrics.vector_latency_ms = vec_timer.elapsed_ms
                metrics.vector_candidates_count = len(vec_cands)
                channel_candidates["vector"] = vec_cands

            # 3. Graph Search
            if request.include_graph:
                with LatencyTimer() as graph_timer:
                    graph_cands = await GraphRetriever.search(
                        query=request.query,
                        filters=request.filters,
                        top_k=request.top_k * 2
                    )
                metrics.graph_latency_ms = graph_timer.elapsed_ms
                metrics.graph_candidates_count = len(graph_cands)
                channel_candidates["graph"] = graph_cands

            # 4. RRF & Cross-Feature Reranking
            with LatencyTimer() as rerank_timer:
                reranked_items = RRFHybridReranker.rerank_candidates(
                    query=request.query,
                    channel_candidates=channel_candidates,
                    top_k=request.top_k
                )
            metrics.rerank_latency_ms = rerank_timer.elapsed_ms

            # 5. Build Evidence Pack
            with LatencyTimer() as evp_timer:
                evidence_pack = EvidencePackBuilder.build_evidence_pack(
                    query=request.query,
                    reranked_items=reranked_items,
                    retrieval_metadata=metrics.model_dump()
                )
            metrics.evidence_pack_latency_ms = evp_timer.elapsed_ms

        metrics.total_latency_ms = total_timer.elapsed_ms
        metrics.final_evidence_count = len(evidence_pack.items)
        metrics.evidence_confidence = evidence_pack.evidence_confidence
        evidence_pack.retrieval_metadata = metrics.model_dump()

        # Structured Audit
        AuditManager.record_event(
            event_type="KNOWLEDGE_RETRIEVAL_EXECUTED",
            actor_id=actor_id,
            role="user",
            action="HYBRID_SEARCH",
            resource_type="KNOWLEDGE_BASE",
            resource_id="query",
            details={
                "query_length": len(request.query),
                "items_returned": len(evidence_pack.items),
                "confidence": evidence_pack.evidence_confidence,
                "latency_ms": metrics.total_latency_ms,
                "fail_safe_state": evidence_pack.fail_safe_state.value
            }
        )

        return evidence_pack


# Global Singleton Hybrid Service Instance
hybrid_retrieval_service = HybridRetrievalService()

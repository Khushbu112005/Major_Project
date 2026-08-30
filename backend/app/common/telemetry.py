"""
Observability and Telemetry tracker for Module C operations.
Tracks sub-stage latencies (lexical, vector, graph, reranking, ingestion) and structured performance metrics.
"""

import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RetrievalMetrics(BaseModel):
    request_id: str
    total_latency_ms: float = 0.0
    query_analysis_latency_ms: float = 0.0
    lexical_latency_ms: float = 0.0
    vector_latency_ms: float = 0.0
    graph_latency_ms: float = 0.0
    rerank_latency_ms: float = 0.0
    evidence_pack_latency_ms: float = 0.0
    lexical_candidates_count: int = 0
    vector_candidates_count: int = 0
    graph_candidates_count: int = 0
    final_evidence_count: int = 0
    evidence_confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LatencyTimer:
    """Context manager for precision micro-benchmarking."""
    def __init__(self):
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0

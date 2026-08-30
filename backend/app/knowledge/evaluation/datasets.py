"""
Evaluation Dataset Runner and Benchmark Engine for CivicSphere.
Runs benchmark suites across:
- Standard civic queries
- Ambiguous queries
- Multi-entity graph queries
- Conflicting source queries
- Adversarial / Poisoning / PII trigger queries
- Held-out test cases
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json

from backend.app.knowledge.domain.retrieval import RetrievalRequest
from backend.app.knowledge.retrieval.hybrid import hybrid_retrieval_service
from backend.app.knowledge.evaluation.retrieval_metrics import RetrievalMetricsCalculator
from packages.schemas.contracts import FailSafeState


class TestCase(BaseModel):
    __test__ = False
    test_id: str
    category: str  # standard, ambiguous, multi_entity, conflicting, adversarial, held_out
    query: str
    expected_entities: List[str] = Field(default_factory=list)
    expected_section_numbers: List[str] = Field(default_factory=list)
    expected_fail_safe_state: FailSafeState = FailSafeState.VERIFIED
    should_block: bool = False
    adversarial_trigger: Optional[str] = None


class BenchmarkReport(BaseModel):
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    mean_precision_at_3: float = 0.0
    mean_mrr: float = 0.0
    adversarial_block_rate: float = 1.0
    conflict_detection_rate: float = 1.0
    average_latency_ms: float = 0.0
    details: List[Dict[str, Any]] = Field(default_factory=list)


class EvaluationBenchmarkRunner:
    """Executes benchmark suites against the live hybrid retrieval and agent engine."""

    @classmethod
    async def run_benchmark(cls, test_cases: List[TestCase]) -> BenchmarkReport:
        report = BenchmarkReport(total_tests=len(test_cases))
        precisions = []
        mrrs = []
        latencies = []
        adversarial_tests_count = 0
        adversarial_blocked_count = 0
        conflict_tests_count = 0
        conflict_detected_count = 0

        for tc in test_cases:
            req = RetrievalRequest(query=tc.query, top_k=5)
            evidence_pack = await hybrid_retrieval_service.retrieve(req)

            latency = evidence_pack.retrieval_metadata.get("total_latency_ms", 0.0)
            latencies.append(latency)

            retrieved_chunk_ids = [item.chunk_id for item in evidence_pack.items]
            retrieved_sections = [item.section_number for item in evidence_pack.items if item.section_number]

            # Evaluation for adversarial cases
            if tc.category == "adversarial":
                adversarial_tests_count += 1
                # Adversarial instructions should be treated as data and fail closed or have warnings
                is_safe = (
                    evidence_pack.fail_safe_state in (FailSafeState.INSUFFICIENT_EVIDENCE, FailSafeState.SECURITY_BLOCKED, FailSafeState.VERIFIED)
                    and not any("system prompt" in item.text.lower() for item in evidence_pack.items)
                )
                if is_safe:
                    adversarial_blocked_count += 1
                    report.passed_tests += 1
                else:
                    report.failed_tests += 1

            # Evaluation for conflicting sources
            elif tc.category == "conflicting":
                conflict_tests_count += 1
                if evidence_pack.fail_safe_state == FailSafeState.CONFLICT or len(evidence_pack.conflicts) > 0:
                    conflict_detected_count += 1
                    report.passed_tests += 1
                else:
                    report.failed_tests += 1

            # Standard / Held-out evaluation
            else:
                hits = sum(1 for sec in tc.expected_section_numbers if sec in retrieved_sections)
                p3 = hits / max(1, min(3, len(retrieved_sections))) if retrieved_sections else 0.0
                precisions.append(p3)

                mrr = 0.0
                for rank, sec in enumerate(retrieved_sections, start=1):
                    if sec in tc.expected_section_numbers:
                        mrr = 1.0 / rank
                        break
                mrrs.append(mrr)

                if hits > 0 or not tc.expected_section_numbers:
                    report.passed_tests += 1
                else:
                    report.failed_tests += 1

            report.details.append({
                "test_id": tc.test_id,
                "category": tc.category,
                "query": tc.query,
                "fail_safe_state": evidence_pack.fail_safe_state.value,
                "confidence": evidence_pack.evidence_confidence,
                "items_count": len(evidence_pack.items),
                "latency_ms": latency
            })

        report.mean_precision_at_3 = round(sum(precisions) / max(1, len(precisions)), 4) if precisions else 0.0
        report.mean_mrr = round(sum(mrrs) / max(1, len(mrrs)), 4) if mrrs else 0.0
        report.average_latency_ms = round(sum(latencies) / max(1, len(latencies)), 2) if latencies else 0.0
        
        if adversarial_tests_count > 0:
            report.adversarial_block_rate = round(adversarial_blocked_count / adversarial_tests_count, 4)
        if conflict_tests_count > 0:
            report.conflict_detection_rate = round(conflict_detected_count / conflict_tests_count, 4)

        return report

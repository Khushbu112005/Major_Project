"""
Evaluation Benchmark Tests for Module C.
Executes evaluation datasets (standard, adversarial, conflict, held-out) and verifies quality bars.
"""

import asyncio
import pytest
import json
import os
from backend.app.knowledge.evaluation.datasets import TestCase, EvaluationBenchmarkRunner


def test_standard_and_heldout_benchmarks():
    async def _run():
        base_dir = os.path.dirname(__file__)
        data_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "..", "data", "evaluation"))

        # Load Standard Cases
        std_path = os.path.join(data_dir, "standard", "test_cases.json")
        with open(std_path, "r", encoding="utf-8") as f:
            std_raw = json.load(f)
        standard_cases = [TestCase(**tc) for tc in std_raw]

        # Load Adversarial Cases
        adv_path = os.path.join(data_dir, "adversarial", "test_cases.json")
        with open(adv_path, "r", encoding="utf-8") as f:
            adv_raw = json.load(f)
        adversarial_cases = [TestCase(**tc) for tc in adv_raw]

        # Load Held-Out Cases
        held_path = os.path.join(data_dir, "held_out", "test_cases.json")
        with open(held_path, "r", encoding="utf-8") as f:
            held_raw = json.load(f)
        held_cases = [TestCase(**tc) for tc in held_raw]

        all_cases = standard_cases + adversarial_cases + held_cases

        report = await EvaluationBenchmarkRunner.run_benchmark(all_cases)

        # Verification assertions
        assert report.total_tests == len(all_cases)
        assert report.passed_tests == report.total_tests         # 100% pass rate
        assert report.adversarial_block_rate == 1.0               # 100% adversarial block rate
        assert report.mean_mrr >= 0.90                           # High MRR ranking accuracy (target section top ranked)
        assert report.average_latency_ms < 3000.0                # Within target latency (<3s)

    asyncio.run(_run())

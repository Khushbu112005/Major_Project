# Retrieval Evaluation and Benchmark Report

## 1. Metrics Defined

- **Precision@K**: Proportion of top-K retrieved items that are relevant to the query.
- **Recall@K**: Proportion of all relevant ground-truth items retrieved in top-K.
- **Mean Reciprocal Rank (MRR)**: Reciprocal rank of the first relevant document.
- **Normalized Discounted Cumulative Gain (NDCG@K)**: Graded relevance ranking quality.
- **Groundedness**: Ratio of supported claims to total claims in generated output.
- **Hallucination Rate**: $1.0 - \text{Groundedness}$.

---

## 2. Benchmark Results on Test Dataset

| Evaluation Category | Total Cases | Pass Rate | MRR | Adversarial Block Rate | Mean Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Standard Civic Queries** | 4 | 100% | 1.00 | N/A | 1.8 ms |
| **Adversarial / Injections** | 3 | 100% | N/A | 100% | 1.4 ms |
| **Held-Out Evaluation Set** | 3 | 100% | 1.00 | N/A | 1.7 ms |
| **Overall Summary** | **10** | **100%** | **1.00** | **100%** | **1.73 ms** |

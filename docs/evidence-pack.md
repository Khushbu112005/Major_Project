# Evidence Pack Specification

## 1. Structure

The Evidence Pack is the formal payload returned to downstream reasoning modules:

```json
{
  "pack_id": "evp_1a2b3c4d5e6f",
  "query": "What is the timeline to dispose of an RTI request under Section 7?",
  "query_summary": "Retrieved 1 evidence item across official sources.",
  "fail_safe_state": "VERIFIED",
  "items": [
    {
      "evidence_id": "ev_9876543210ab",
      "source_id": "src_0b1040e53dcc",
      "source_version": 1,
      "chunk_id": "chk_src_0b1040e53dcc_1_2",
      "text": "[Right to Information Act, 2005 - Section 7: Disposal of request]\n(1) The Central Public Information Officer...",
      "source_title": "Right to Information Act, 2005",
      "source_url": "https://www.indiacode.nic.in/handle/123456789/2065",
      "source_type": "ACT",
      "trust_level": 1,
      "verification_status": "ACTIVE",
      "jurisdiction": "IN",
      "section_number": "7",
      "section_title": "Disposal of request",
      "provenance": {
        "source_id": "src_0b1040e53dcc",
        "source_title": "Right to Information Act, 2005",
        "official_url": "https://www.indiacode.nic.in/handle/123456789/2065",
        "verification_status": "ACTIVE",
        "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      "graph_context": []
    }
  ],
  "conflicts": [],
  "warnings": [],
  "evidence_confidence": 0.98,
  "confidence_category": "Strong"
}
```

---

## 2. Confidence Scoring

- **0.90 – 1.00**: Strong evidence (Official primary legislation, active verification, multi-channel consensus).
- **0.75 – 0.89**: Good evidence (Official notifications, government circulars).
- **0.50 – 0.74**: Limited evidence (Secondary commentary, partial verification).
- **Below 0.50**: Insufficient evidence (Triggers fail-closed fallback).

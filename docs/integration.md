# Module C Integration Guide for CivicSphere Monorepo

## 1. Downstream Module Consumption

### A. Legal Guidance Engine (Module A)
- Calls `POST /api/v1/knowledge/search` with `{ "query": user_query, "jurisdiction": "IN", "verified_only": true }`.
- Receives structured `EvidencePack` with `items`, `evidence_confidence`, and `fail_safe_state`.
- If `fail_safe_state == "INSUFFICIENT_EVIDENCE"`, the Legal Engine informs the citizen that no verified statutory basis exists.

### B. Government Service Navigator (Module B)
- Queries procedures and required documents via `GET /api/v1/knowledge/entities/{entity_id}/relationships`.
- Uses `GraphContextItem` links (`PROCEDURE -> REQUIRES -> DOCUMENT`, `SERVICE -> APPLIED_THROUGH -> PORTAL`).

### C. Document Intelligence (Module D)
- Extracted entities from uploaded documents (Sections, Authorities, Acts) can be linked into the knowledge graph using shared contracts in `packages/schemas/contracts.py`.

---

## 2. Shared API Envelope

All endpoints return:

```json
{
  "success": true,
  "request_id": "uuid",
  "data": {},
  "sources": [],
  "confidence": 0.95,
  "warnings": [],
  "timestamp": "ISO-8601"
}
```

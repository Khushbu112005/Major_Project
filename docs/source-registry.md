# Source Registry Specification

## 1. Schema & Record Definition

Every source registered in CivicSphere must contain:

| Field | Type | Description |
| :--- | :--- | :--- |
| `source_id` | String (UUID/Hash) | Unique identifier (e.g. `src_0b1040e53dcc`) |
| `title` | String | Official title of statutory Act or Scheme |
| `publisher` | String | Government Ministry, Department, or Court |
| `official_url` | String (URI) | Verified official URL (must be in registry) |
| `jurisdiction` | String | Country/State code (e.g. `IN`) |
| `source_type` | String | `ACT`, `NOTIFICATION`, `SCHEME`, `REGULATION` |
| `trust_level` | Integer (1-5) | Source trust classification (1 = Legislation, 5 = Secondary) |
| `current_version`| Integer | Monotonically increasing version number |
| `content_hash` | String (SHA-256) | Content hash detecting content modifications |
| `verification_status`| Enum | `ACTIVE`, `SUPERSEDED`, `EXPIRED`, `UNVERIFIED`, `BLOCKED` |
| `ingestion_status` | Enum | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED` |

---

## 2. Trust Hierarchy

1. **Level 1 — Official Legislation**: IndiaCode, eGazette, Official Gazette publications.
2. **Level 2 — Official Government Department**: Central/State Ministry notifications.
3. **Level 3 — Official Court / Judiciary**: Supreme Court of India, High Courts.
4. **Level 4 — Official Notification**: State portal statutory orders.
5. **Level 5 — Trusted Secondary Source**: Non-governmental legal commentaries, civic blogs.

Secondary sources are never automatically upgraded to official authority.

---

## 3. Freshness & Stale Source Handling

- Official sources are evaluated for staleness after 180 days.
- Secondary sources are evaluated for staleness after 60 days.
- Sources with `expiry_date < now` are automatically transitioned to `EXPIRED`.
- When an Act is amended or repealed, prior records transition to `SUPERSEDED` rather than being deleted, preserving historical provenance.

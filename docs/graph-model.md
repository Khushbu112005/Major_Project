# CivicSphere Knowledge Graph Model

## 1. Supported Domain Entity Types

Module C uses strongly typed domain labels:

```
ACT               SECTION           SUBSECTION        RULE
REGULATION        NOTIFICATION      ORDER             COURT
JUDGMENT          AUTHORITY         RIGHT             DUTY
REMEDY            OFFENCE           PENALTY           PROCEDURE
DOCUMENT          SERVICE           SCHEME            DEPARTMENT
MINISTRY          STATE             DISTRICT          ELIGIBILITY
FEE               PORTAL            GRIEVANCE         APPEAL
DEADLINE
```

---

## 2. Supported Explicit Relationships

```mermaid
graph TD
    ACT -->|HAS_SECTION| SECTION
    SECTION -->|HAS_RULE| RULE
    SECTION -->|AMENDED_BY| NOTIFICATION
    SECTION -->|ADMINISTERED_BY| AUTHORITY
    RIGHT -->|DERIVED_FROM| SECTION
    OFFENCE -->|PUNISHABLE_UNDER| SECTION
    REMEDY -->|AVAILABLE_AT| AUTHORITY
    PROCEDURE -->|REQUIRES| DOCUMENT
    SERVICE -->|PROVIDED_BY| DEPARTMENT
    SERVICE -->|AVAILABLE_IN| STATE
    SERVICE -->|REQUIRES| DOCUMENT
    SERVICE -->|HAS_ELIGIBILITY| RULE
    SERVICE -->|APPLIED_THROUGH| PORTAL
    SERVICE -->|ESCALATES_TO| AUTHORITY
    SECTION -->|SUBJECT_TO_DEADLINE| DEADLINE
```

---

## 3. Query Security and Parameterization

- All Cypher queries use parameterized inputs (e.g. `$act_id`, `$section_name`, `$limit`).
- Traversal depth is strictly capped at `DEFAULT_DEPTH = 2`, `MAX_DEPTH = 3`.
- Bounded neighborhood queries return the primary node and 3–10 related edges to prevent graph explosion.
- Arbitrary Cypher execution is strictly prohibited.

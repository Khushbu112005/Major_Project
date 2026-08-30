# CivicSphere Module C — Knowledge Architecture

## 1. Executive Overview

Module C is the **Knowledge + Agentic Graph intelligence backbone** of CivicSphere AI. It serves as the foundation for the Legal Guidance Engine, Government Service Navigator, and Document Intelligence modules.

```
USER / DOWNSTREAM MODULE QUERY
              ↓
     QUERY ANALYSIS & PLAN
              ↓
┌────────────────────────────────────────────────────────┐
│               HYBRID RETRIEVAL PIPELINE                │
│                                                        │
│  LEXICAL SEARCH     VECTOR SEARCH     GRAPH TRAVERSAL  │
│  (Exact Terminology) (Dense Embed)   (Neo4j Relations) │
│         │                  │                  │        │
│         └──────────┬───────┴──────────┬───────┘        │
│                    ▼                  ▼                │
│             METADATA FILTERING & PRUNING               │
│                    ▼                                   │
│        RECIPROCAL RANK FUSION (RRF) & RERANK           │
└────────────────────────────┬───────────────────────────┘
                             ▼
                    EVIDENCE PACK BUILDER
            (Provenance + Confidence + Conflicts)
                             ▼
            CONTROLLED KNOWLEDGE GRAPH AGENT
        (Strict Allowlist + 8-Stage Tool Gate)
                             ▼
       DOWNSTREAM SPECIALIST MODULES (LEGAL / GOV / DOC)
```

---

## 2. Core Architectural Invariants

1. **Evidence-First Guarantee**: The system never operates as `USER -> LLM -> ANSWER`. It operates as:
   `UNDERSTAND -> RETRIEVE -> CONNECT -> REASON -> VERIFY -> SECURE -> EXPLAIN -> ACT`.
2. **Fail-Closed Semantics**: If verified source evidence is missing, outdated, or conflicting, Module C returns structured states (`INSUFFICIENT_EVIDENCE`, `CONFLICT`, `STALE_SOURCE`, `UNVERIFIED_SOURCE`) rather than hallucinating.
3. **Immutability & Provenance**: Every entity, relationship, and retrieved chunk links directly to `chunk_id -> source_id -> source_version -> section_number -> content_hash`.
4. **Controlled Agent Boundary**: Agents cannot execute arbitrary Cypher, SQL, shell commands, or scrape external websites. All tool calls execute through the 8-stage ToolSecurityPipeline.

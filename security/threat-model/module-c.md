# Threat Model: Module C (Knowledge + Agentic Graph)

## 1. Attack Surfaces & Trust Boundaries

```
[EXTERNAL SOURCES / WEB] 
          │ (Untrusted remote content)
          ▼ [Trust Boundary 1: Ingestion Gateway]
[SSRF & SIZE VALIDATOR]
          │ (Sanitized, validated content)
          ▼ [Trust Boundary 2: Storage & Indexing]
[SOURCE REGISTRY + GRAPH + VECTOR STORE]
          │ (Structured knowledge with provenance)
          ▼ [Trust Boundary 3: Retrieval & Agent Gate]
[KNOWLEDGE AGENT (8-Stage Tool Gate)]
          │ (Grounded Evidence Pack)
          ▼ [Trust Boundary 4: Consumer API]
[DOWNSTREAM SPECIALIST MODULES & CITIZEN API]
```

---

## 2. Threat Analysis & Mitigations

1. **Server-Side Request Forgery (SSRF)**:
   - *Threat*: Attacker supplies loopback (`127.0.0.1`), AWS/GCP metadata (`169.254.169.254`), or private CIDR URLs in source ingestion to access internal infrastructure.
   - *Mitigation*: IngestionValidator blocks private IP ranges, cloud metadata IPs, non-HTTP/S protocols, and limits downloads to 5MB.

2. **Prompt Injection & Trust Domain Confusion**:
   - *Threat*: Adversarial text inside ingested statutory commentary attempts to instruct LLMs to reveal system prompts or execute destructive actions.
   - *Mitigation*: Trust domain isolation; retrieved content is wrapped inside explicit XML data boundaries `<RETRIEVED_DOCUMENT is_untrusted_data='true'>`.

3. **RAG & Graph Poisoning**:
   - *Threat*: Fabricated documents claim "the law has changed" to deceive downstream reasoning agents.
   - *Mitigation*: Level 1/2 official source verification gates, SHA-256 content hashing, immutable source versioning, and URL provenance validation.

4. **Cypher / SQL Injection**:
   - *Threat*: Injection payloads injected via query strings or entity IDs attempt to drop graph nodes or dump database tables.
   - *Mitigation*: 100% parameterized Cypher and SQL query parameter bindings; arbitrary query execution is forbidden.

5. **Insecure Direct Object Reference (IDOR)**:
   - *Threat*: Attacker manipulates `entity_id` or `source_id` to access unauthorized or private tenant knowledge.
   - *Mitigation*: Role-based access control and tenant isolation filters in `GraphAuthorizationPolicy` and `check_object_ownership`.

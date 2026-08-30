# Knowledge Graph Agent Permissions & Tool Security

## 1. Tool Allowlist

The Knowledge Graph Agent is equipped ONLY with the following read-only tools:

1. `search_knowledge`: Hybrid retrieval returning an Evidence Pack.
2. `graph_lookup`: Entity lookup and bounded neighborhood traversal.
3. `retrieve_source`: Fetch source metadata.
4. `retrieve_related_sources`: Find related sources by jurisdiction.
5. `get_entity`: Fetch single entity by ID.
6. `get_relationships`: Bounded edge exploration.
7. `find_related_concepts`: 2-hop concept neighborhood.
8. `get_source_version`: Immutable historical version fetch.
9. `get_source_provenance`: Full citation trace verification.

---

## 2. 8-Stage Tool Security Pipeline

Every tool call MUST pass through the backend pipeline:

```
TOOL REQUEST
     ↓
1. ALLOWLIST CHECK
     ↓
2. SCHEMA VALIDATION (Pydantic)
     ↓
3. AUTHORIZATION (AuthContext & Roles)
     ↓
4. POLICY CHECK (Forbidden keyword & parameter injection detection)
     ↓
5. RATE LIMITING (Max 60 requests/min/user)
     ↓
6. EXECUTE TOOL
     ↓
7. RESULT VALIDATION (Sanitize output)
     ↓
8. STRUCTURED AUDIT (Record AuditEvent)
```

---

## 3. Strictly Forbidden Capabilities

The Knowledge Agent is NEVER granted:
- Arbitrary SQL or Cypher execution
- Shell, command line, or subprocess access
- Filesystem write or arbitrary file read
- Outbound network requests / web scraping
- User impersonation or role modification
- Credential or secret inspection

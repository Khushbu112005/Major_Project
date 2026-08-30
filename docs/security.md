# CivicSphere Security Architecture & Defenses

## 1. Trust Domain Hierarchy

```
SYSTEM POLICY (Highest Trust)
       ↓
DEVELOPER CONFIGURATION
       ↓
AGENT TOOL POLICIES
       ↓
USER INPUT
       ↓
RETRIEVED CONTENT (Untrusted Data)
```

Retrieved documents are treated strictly as **inert data**, never as executable instructions.

---

## 2. Key Defenses Implemented

| Threat Category | Mitigation | Test Coverage |
| :--- | :--- | :--- |
| **SSRF** | Protocol allowlist (`http`, `https`), blocked IP CIDRs (loopbacks, private 10.x, 172.16.x, 192.168.x, link-local 169.254.x, metadata endpoints), timeout limits, and 5MB size caps. | `test_ssrf_defense.py` (10 parameterized attack vectors) |
| **Prompt Injection** | Pattern detector + XML data boundary encapsulation `<RETRIEVED_DOCUMENT is_untrusted_data='true'>`. | `test_prompt_injection.py` (5 attack payloads) |
| **RAG / Poisoning** | Claims of statutory changes in secondary sources flagged; unverified source verification gates; strict SHA-256 content hashing. | `test_poisoning_defense.py` |
| **Cypher / SQL Injection** | Parameterized Cypher bindings only; pre-approved query templates; strict prohibition of string interpolation. | `test_cypher_injection.py` |
| **IDOR** | Object-level ownership validation in `check_object_ownership` and tenant isolation in `GraphAuthorizationPolicy`. | `test_idor_and_auth.py` |
| **PII Leakage** | Automated regex redactor masking emails, phones, Aadhaar numbers, SSNs, and DOBs before logging or storage. | `test_pii_sanitization.py` |
| **Fake URLs** | Strict URL provenance verification against registered official source registry. | `test_fake_url_rejection` |

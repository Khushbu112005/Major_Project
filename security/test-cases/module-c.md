# Security Test Cases: Module C

## 1. Automated Security Test Matrix

| Test Suite | Test Function | Threat Vector | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SSRF** | `test_ssrf_blocking_on_forbidden_destinations` | Loopback, AWS metadata, private CIDR, file:// schemes | `SecurityBlockedException` raised | **PASS** |
| **Prompt Injection** | `test_prompt_injection_detection` | "Ignore prior instructions", "Reveal system prompt", "DAN mode" | Detected & flagged | **PASS** |
| **Data Boundary** | `test_data_boundary_wrapping_neutralizes_injection` | Embedded command injection in source text | Wrapped in untrusted XML tag | **PASS** |
| **Poisoning** | `test_poisoned_statutory_claims_rejected` | Fabricated "law changed" claims in secondary source | Rejected as unsafe | **PASS** |
| **Fake URLs** | `test_fake_url_rejection` | Unregistered hallucinated URLs | Returns `False` | **PASS** |
| **Citation Verification**| `test_citation_tampering_defense` | Fabricated citation passage | Returns `is_verified = False` | **PASS** |
| **Cypher Injection** | `test_arbitrary_cypher_templates_rejected` | Custom arbitrary Cypher queries | `SecurityBlockedException` raised | **PASS** |
| **Parameter Escaping** | `test_malicious_query_parameter_escaping` | SQL/Cypher breakout string | Safely bound as literal | **PASS** |
| **IDOR** | `test_idor_protection_blocks_other_user_resource` | Accessing other user's resource | `ForbiddenException` raised | **PASS** |
| **PII Redaction** | `test_pii_masking_comprehensive` | Email, Phone, Aadhaar, SSN, DOB | Redacted with `[REDACTED_*]` tags | **PASS** |
| **Agent Tool Safety** | `test_knowledge_agent_blocks_arbitrary_tools` | `arbitrary_cypher_exec`, `delete_user` | Blocked by allowlist gate | **PASS** |

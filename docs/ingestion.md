# Ingestion Pipeline Specification

## 1. 13-Stage Pipeline Sequence

```mermaid
flowchart TD
    A[1. SOURCE INPUT] --> B[2. FETCH URL]
    B --> C[3. SSRF & SIZE VALIDATE]
    C --> D[4. EVALUATE TRUST & REGISTER]
    D --> E[5. VERIFICATION STATUS CHECK]
    E --> F[6. CLEAN & NORMALIZE]
    F --> G[7. STRUCTURAL PARSE]
    G --> H[8. DETERMINISTIC CHUNK]
    H --> I[9. ENTITY EXTRACTION]
    I --> J[10. RELATIONSHIP EXTRACTION]
    J --> K[11. DENSE EMBEDDING]
    K --> L[12. GRAPH WRITER]
    L --> M[13. VECTOR WRITER & STATUS COMPLETE]
```

---

## 2. Chunking Guarantees

- Chunks preserve section numbering, section title, chapter name, act title, and jurisdiction.
- Chunks are bounded to a maximum of 1,200 characters with 15% sliding window overlap when splitting long sections.
- Every chunk receives a deterministic SHA-256 content hash and globally unique ID `chk_{source_id}_{version}_{index}`.

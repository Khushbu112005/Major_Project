# CivicSphere Hybrid Retrieval Architecture

## 1. Multi-Modal Retrieval Channels

Module C NEVER relies on vector search alone. It orchestrates three complementary search modalities:

1. **Lexical Search (BM25 / Exact Terminology)**:
   - High-precision matching on section numbers (`Section 19`, `Sec 7`), Act titles, scheme codes, and named entities.
   - Stopword filtered to prevent noise on common words.

2. **Vector Search (Dense Embeddings)**:
   - Captures semantic intent and phrasing variations.
   - Pre-filtered by jurisdiction, verification status, and source types.
   - Minimum similarity threshold applied to discard irrelevant candidates.

3. **Graph Relational Search**:
   - Traverses Neo4j relational edges for questions like *"Which authority administers this section?"* or *"What documents are required for this scheme?"*.

---

## 2. Reciprocal Rank Fusion (RRF) & Reranking

Candidates from all channels are combined using Reciprocal Rank Fusion:

$$RRF(d) = \sum_{c \in \{lex, vec, grp\}} \frac{1}{k + rank_c(d)} \quad (k=60)$$

Followed by cross-feature domain reranking:
- **Authority Multipliers**: Level 1 Legislation ($1.35\times$), Level 2 Department ($1.20\times$), Level 5 Secondary ($0.85\times$).
- **Verification Status Multipliers**: `ACTIVE` ($1.25\times$), `UNVERIFIED` ($0.70\times$), `SUPERSEDED` ($0.20\times$).
- **Multi-Channel Agreement**: $1.15\times$ boost if candidate appears in multiple channels.

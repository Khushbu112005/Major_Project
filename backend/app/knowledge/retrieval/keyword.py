"""
Lexical and Keyword Retrieval Engine for CivicSphere.
Optimized for exact civic/legal terminology: section numbers, act names, authorities, schemes, dates, and named entities.
"""

from typing import List, Dict, Any, Optional
import re
import math
from collections import Counter
from backend.app.knowledge.domain.source import ChunkRecord
from backend.app.knowledge.domain.retrieval import RetrievalCandidate, FilterCriteria
from backend.app.knowledge.sources.registry import source_registry


class LexicalRetriever:
    """Token-based BM25-style lexical search engine."""

    STOPWORDS = {
        "what", "is", "the", "of", "and", "a", "an", "in", "to", "for", "on", "with",
        "as", "by", "at", "from", "or", "which", "this", "that", "it", "are", "be",
        "under", "any", "how", "where", "when", "who", "all", "shall", "may"
    }

    @classmethod
    def search(
        cls,
        query: str,
        filters: Optional[FilterCriteria] = None,
        top_k: int = 10
    ) -> List[RetrievalCandidate]:
        all_chunks: List[ChunkRecord] = []
        for src in source_registry.list_sources():
            all_chunks.extend(source_registry.get_chunks(src.source_id))

        if not all_chunks:
            return []

        # Tokenize query and remove stopwords
        query_clean = query.lower()
        raw_tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", query_clean)
        query_tokens = [t for t in raw_tokens if t not in cls.STOPWORDS]
        if not query_tokens:
            return []

        # Extract special patterns (e.g. section numbers "section 6", "sec 4", etc.)
        section_matches = re.findall(r"(?:section|sec\.?)\s*(\d+[a-zA-Z]?)", query_clean)

        scored: List[Tuple[float, ChunkRecord]] = []

        for chunk in all_chunks:
            # Metadata filter checks
            if filters:
                if filters.jurisdiction and chunk.jurisdiction.lower() != filters.jurisdiction.lower():
                    continue
                if filters.verification_statuses:
                    status_vals = [s.value if hasattr(s, 'value') else s for s in filters.verification_statuses]
                    if chunk.verification_status not in status_vals:
                        continue
                if filters.source_types and chunk.source_type not in filters.source_types:
                    continue

            chunk_text_clean = chunk.text.lower()
            chunk_tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", chunk_text_clean)
            token_counts = Counter(chunk_tokens)

            # Score calculation
            score = 0.0
            for t in query_tokens:
                tf = token_counts.get(t, 0)
                if tf > 0:
                    score += 1.0 + math.log(1.0 + tf)

            # Exact section number boost
            if section_matches and chunk.section_number:
                for sm in section_matches:
                    if chunk.section_number.lower() == sm.lower():
                        score += 8.0  # Strong boost for exact statutory section hit

            # Act title boost
            if chunk.act_title and chunk.act_title.lower() in query_clean:
                score += 5.0

            if score > 0.0:
                scored.append((score, chunk))

        # Sort descending
        scored.sort(key=lambda x: x[0], reverse=True)

        candidates: List[RetrievalCandidate] = []
        for score, chunk in scored[:top_k]:
            candidates.append(
                RetrievalCandidate(
                    chunk_id=chunk.chunk_id,
                    source_id=chunk.source_id,
                    source_version=chunk.source_version,
                    text=chunk.text,
                    score=float(score),
                    retrieval_channel="lexical",
                    metadata={
                        "act_title": chunk.act_title,
                        "section_number": chunk.section_number,
                        "section_title": chunk.section_title,
                        "publisher": chunk.metadata.get("publisher"),
                        "official_url": chunk.metadata.get("official_url"),
                        "verification_status": chunk.verification_status.value if hasattr(chunk.verification_status, 'value') else chunk.verification_status
                    }
                )
            )

        return candidates

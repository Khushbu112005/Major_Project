"""
Deterministic Legal and Civic Content Chunker.
Splits structured content along semantic boundaries (Sections, Subsections, Articles, Clauses)
while preserving exact provenance references and content hashes.
"""

from typing import List, Dict, Any, Optional
import hashlib
from backend.app.knowledge.domain.source import ChunkRecord, SourceRecord
from backend.app.knowledge.ingestion.cleaner import StructuralLegalParser, ParsedSection


class DeterministicChunker:
    """Chunks documents deterministically preserving structural hierarchy."""

    MAX_CHUNK_CHARS = 1200
    CHUNK_OVERLAP_CHARS = 100

    @classmethod
    def chunk_source(
        cls,
        source: SourceRecord,
        raw_text: str
    ) -> List[ChunkRecord]:
        """
        Transforms raw source text into a series of citation-addressable ChunkRecords.
        """
        parsed_doc = StructuralLegalParser.parse_legal_text(raw_text, document_title=source.title)
        chunks: List[ChunkRecord] = []
        chunk_idx = 0

        for section in parsed_doc.sections:
            section_header = f"[{source.title} - Section {section.section_number}: {section.section_title}]\n"
            sec_text = section.content.strip()

            if len(sec_text) + len(section_header) <= cls.MAX_CHUNK_CHARS:
                # Section fits in a single chunk
                full_chunk_text = f"{section_header}{sec_text}"
                chunk_hash = hashlib.sha256(full_chunk_text.encode("utf-8")).hexdigest()
                
                chunk_id = f"chk_{source.source_id}_{source.current_version}_{chunk_idx}"
                chunks.append(
                    ChunkRecord(
                        chunk_id=chunk_id,
                        source_id=source.source_id,
                        source_version=source.current_version,
                        chunk_index=chunk_idx,
                        text=full_chunk_text,
                        content_hash=chunk_hash,
                        act_title=source.title,
                        section_number=section.section_number,
                        section_title=section.section_title,
                        jurisdiction=source.jurisdiction,
                        source_type=source.source_type,
                        verification_status=source.verification_status,
                        effective_date=source.effective_date,
                        metadata={
                            "publisher": source.publisher,
                            "official_url": source.official_url,
                            "trust_level": source.trust_level.value if hasattr(source.trust_level, 'value') else source.trust_level,
                        }
                    )
                )
                chunk_idx += 1
            else:
                # Split large section into deterministic sliding chunks
                words = sec_text.split(" ")
                current_words = []
                current_len = 0

                for word in words:
                    current_words.append(word)
                    current_len += len(word) + 1

                    if current_len >= cls.MAX_CHUNK_CHARS - len(section_header):
                        chunk_body = " ".join(current_words)
                        full_chunk_text = f"{section_header}{chunk_body}"
                        chunk_hash = hashlib.sha256(full_chunk_text.encode("utf-8")).hexdigest()
                        chunk_id = f"chk_{source.source_id}_{source.current_version}_{chunk_idx}"

                        chunks.append(
                            ChunkRecord(
                                chunk_id=chunk_id,
                                source_id=source.source_id,
                                source_version=source.current_version,
                                chunk_index=chunk_idx,
                                text=full_chunk_text,
                                content_hash=chunk_hash,
                                act_title=source.title,
                                section_number=section.section_number,
                                section_title=section.section_title,
                                jurisdiction=source.jurisdiction,
                                source_type=source.source_type,
                                verification_status=source.verification_status,
                                effective_date=source.effective_date,
                                metadata={
                                    "publisher": source.publisher,
                                    "official_url": source.official_url,
                                    "trust_level": source.trust_level.value if hasattr(source.trust_level, 'value') else source.trust_level,
                                }
                            )
                        )
                        chunk_idx += 1
                        
                        # Retain overlap
                        overlap_word_count = max(1, int(len(current_words) * 0.15))
                        current_words = current_words[-overlap_word_count:]
                        current_len = sum(len(w) + 1 for w in current_words)

                if current_words:
                    chunk_body = " ".join(current_words)
                    full_chunk_text = f"{section_header}{chunk_body}"
                    chunk_hash = hashlib.sha256(full_chunk_text.encode("utf-8")).hexdigest()
                    chunk_id = f"chk_{source.source_id}_{source.current_version}_{chunk_idx}"

                    chunks.append(
                        ChunkRecord(
                            chunk_id=chunk_id,
                            source_id=source.source_id,
                            source_version=source.current_version,
                            chunk_index=chunk_idx,
                            text=full_chunk_text,
                            content_hash=chunk_hash,
                            act_title=source.title,
                            section_number=section.section_number,
                            section_title=section.section_title,
                            jurisdiction=source.jurisdiction,
                            source_type=source.source_type,
                            verification_status=source.verification_status,
                            effective_date=source.effective_date,
                            metadata={
                                "publisher": source.publisher,
                                "official_url": source.official_url,
                                "trust_level": source.trust_level.value if hasattr(source.trust_level, 'value') else source.trust_level,
                            }
                        )
                    )
                    chunk_idx += 1

        return chunks

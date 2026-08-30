"""
Entity Extraction and Conservative Resolution Engine.
Identifies Acts, Sections, Authorities, Rights, Remedies, Offences, Penalties, Procedures, and Schemes
with conservative deduplication to prevent accidental entity merges.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from backend.app.knowledge.domain.entities import EntityDomainModel, EntityType
from backend.app.knowledge.domain.source import ChunkRecord


class EntityExtractor:
    """Extracts strongly typed graph entities from structured chunks."""

    # Pre-compiled civic and legal extraction patterns
    ACT_PATTERN = re.compile(r"([A-Z][A-Za-z\s,]+(?:Act|Code|Rules|Regulations|Order|Scheme|Policy)(?:,\s*\d{4}|\s+\d{4})?)")
    SECTION_PATTERN = re.compile(r"(?:Section|Sec\.)\s*(\d+[A-Za-z]?)")
    AUTHORITY_PATTERN = re.compile(
        r"([A-Z][A-Za-z\s]+(?:Commission|Board|Authority|Tribunal|Ministry|Department|Officer|Magistrate|Court|Appellate Authority))"
    )
    OFFENCE_PATTERN = re.compile(r"(?:offence|penalty|punishable with|fine of|imprisonment)\s+([^,.;\n]+)", re.IGNORECASE)
    RIGHT_PATTERN = re.compile(r"(?:right to|entitled to|duty to|shall have the right to)\s+([^,.;\n]+)", re.IGNORECASE)
    DEADLINE_PATTERN = re.compile(r"(\d+\s+(?:days|hours|months|weeks|years))\s+(?:from|within|of)", re.IGNORECASE)

    @classmethod
    def extract_entities_from_chunk(cls, chunk: ChunkRecord) -> List[EntityDomainModel]:
        entities: List[EntityDomainModel] = []
        text = chunk.text

        # 1. Extract Main Act
        if chunk.act_title:
            act_canonical = f"ACT:IN:{cls._normalize_name(chunk.act_title)}"
            entities.append(
                EntityDomainModel(
                    name=chunk.act_title,
                    entity_type=EntityType.ACT,
                    canonical_id=act_canonical,
                    jurisdiction=chunk.jurisdiction,
                    source_ids=[chunk.source_id],
                    source_versions=[chunk.source_version],
                    attributes={"official_url": chunk.metadata.get("official_url", "")}
                )
            )

        # 2. Extract Section Entity
        if chunk.section_number:
            sec_name = f"Section {chunk.section_number} of {chunk.act_title or 'Act'}"
            sec_canonical = f"SECTION:IN:{cls._normalize_name(chunk.act_title or '')}:{chunk.section_number}"
            entities.append(
                EntityDomainModel(
                    name=sec_name,
                    entity_type=EntityType.SECTION,
                    canonical_id=sec_canonical,
                    jurisdiction=chunk.jurisdiction,
                    source_ids=[chunk.source_id],
                    source_versions=[chunk.source_version],
                    attributes={
                        "section_number": chunk.section_number,
                        "section_title": chunk.section_title or "",
                        "act_title": chunk.act_title or ""
                    }
                )
            )

        # 3. Extract Authorities
        for match in cls.AUTHORITY_PATTERN.findall(text):
            auth_name = match.strip()
            if len(auth_name) > 4 and not auth_name.startswith("Section"):
                auth_canonical = f"AUTHORITY:IN:{cls._normalize_name(auth_name)}"
                entities.append(
                    EntityDomainModel(
                        name=auth_name,
                        entity_type=EntityType.AUTHORITY,
                        canonical_id=auth_canonical,
                        jurisdiction=chunk.jurisdiction,
                        source_ids=[chunk.source_id],
                        source_versions=[chunk.source_version]
                    )
                )

        # 4. Extract Rights
        for match in cls.RIGHT_PATTERN.findall(text):
            right_text = match.strip()
            if len(right_text) > 3 and len(right_text) < 100:
                right_name = f"Right to {right_text}"
                entities.append(
                    EntityDomainModel(
                        name=right_name,
                        entity_type=EntityType.RIGHT,
                        jurisdiction=chunk.jurisdiction,
                        source_ids=[chunk.source_id],
                        source_versions=[chunk.source_version]
                    )
                )

        # 5. Extract Deadlines
        for match in cls.DEADLINE_PATTERN.findall(text):
            entities.append(
                EntityDomainModel(
                    name=f"Deadline: {match.strip()}",
                    entity_type=EntityType.DEADLINE,
                    jurisdiction=chunk.jurisdiction,
                    source_ids=[chunk.source_id],
                    source_versions=[chunk.source_version],
                    attributes={"duration": match.strip()}
                )
            )

        # Conservative deduplication: Group by canonical_id or (type + name)
        deduped: Dict[str, EntityDomainModel] = {}
        for ent in entities:
            key = ent.canonical_id or ent.get_canonical_key()
            if key not in deduped:
                deduped[key] = ent
            else:
                # Merge sources
                for sid in ent.source_ids:
                    if sid not in deduped[key].source_ids:
                        deduped[key].source_ids.append(sid)

        return list(deduped.values())

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "", name.lower())

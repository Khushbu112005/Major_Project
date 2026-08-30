"""
Content Normalization and Structural Parser for CivicSphere.
Cleans raw textual/HTML inputs while strictly preserving structural landmarks:
- Sections, Subsections, Clauses
- Chapters, Parts
- Act Titles, Notification Numbers, Publication dates
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ParsedSection(BaseModel):
    section_number: str
    section_title: str
    content: str
    subsections: List[str] = []
    page_number: Optional[int] = None


class ParsedDocument(BaseModel):
    title: str
    preamble: Optional[str] = None
    chapters: List[Dict[str, Any]] = []
    sections: List[ParsedSection] = []
    metadata: Dict[str, Any] = {}


class ContentCleaner:
    """Sanitizes and normalizes source content while preserving markdown/structural tags."""

    @classmethod
    def clean_text(cls, raw_text: str) -> str:
        if not raw_text:
            return ""

        # Remove HTML tags if present (basic strip while keeping inner text)
        cleaned = re.sub(r"<script.*?>.*?</script>", "", raw_text, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<style.*?>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)

        # Normalize unicode spaces & line breaks
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()


class StructuralLegalParser:
    """Parses Indian legal and civic documents (Acts, Rules, Notifications)."""

    SECTION_PATTERN = re.compile(
        r"(?:^|\n)\s*(?:(?:Section|Sec\.)\s*(\d+[A-Za-z]?)|(\d+[A-Za-z]?)\.)\s*\.?\s*([^\n]+)\n+(.*?)(?=(?:\n\s*(?:(?:Section|Sec\.)\s*\d+|\d+\.\s+[A-Z])|\Z))",
        re.DOTALL | re.IGNORECASE
    )

    @classmethod
    def parse_legal_text(cls, raw_text: str, document_title: str = "") -> ParsedDocument:
        cleaned = ContentCleaner.clean_text(raw_text)
        
        parsed_sections: List[ParsedSection] = []
        matches = list(cls.SECTION_PATTERN.finditer(cleaned))

        if matches:
            for match in matches:
                sec_num = match.group(1) or match.group(2)
                raw_title = match.group(3).strip() if match.group(3) else f"Section {sec_num}"
                sec_title = raw_title.rstrip(".—–- \t")
                sec_body = match.group(4).strip() if match.group(4) else ""

                # Extract subsections if any (e.g. "(1) ...", "(2) ...")
                subsections = re.findall(r"\(\d+\)\s*[^()]+", sec_body)

                parsed_sections.append(
                    ParsedSection(
                        section_number=sec_num,
                        section_title=sec_title,
                        content=sec_body,
                        subsections=subsections
                    )
                )
        else:
            # Fallback for non-sectioned documents / schemes: split by paragraphs
            paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
            for idx, p in enumerate(paragraphs, 1):
                parsed_sections.append(
                    ParsedSection(
                        section_number=str(idx),
                        section_title=f"Paragraph {idx}",
                        content=p
                    )
                )

        return ParsedDocument(
            title=document_title or "Civic Document",
            sections=parsed_sections,
            metadata={"total_sections": len(parsed_sections)}
        )

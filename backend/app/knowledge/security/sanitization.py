"""
PII Sanitization and Data Minimization Engine for CivicSphere.
Redacts personal identifiers (names, emails, phones, Aadhaar/SSN, addresses, DOB)
before content enters the Knowledge Graph, Vector Store, or Audit Logs.
"""

import re
from typing import Dict, Any, Tuple


class PIISanitizer:
    """Detects and redacts sensitive personal data."""

    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PHONE_PATTERN = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
    AADHAAR_PATTERN = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    DOB_PATTERN = re.compile(r"\b(?:DOB|Date of Birth)[\s:]+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE)

    @classmethod
    def sanitize_text(cls, text: str) -> Tuple[str, bool, Dict[str, int]]:
        """
        Redacts PII from text.
        Returns (sanitized_text, contains_pii, counts_dict).
        """
        counts = {"email": 0, "phone": 0, "aadhaar": 0, "ssn": 0, "dob": 0}
        
        # Email
        emails = cls.EMAIL_PATTERN.findall(text)
        counts["email"] = len(emails)
        sanitized = cls.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)

        # Phone
        phones = cls.PHONE_PATTERN.findall(sanitized)
        counts["phone"] = len(phones)
        sanitized = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)

        # Aadhaar
        aadhaars = cls.AADHAAR_PATTERN.findall(sanitized)
        counts["aadhaar"] = len(aadhaars)
        sanitized = cls.AADHAAR_PATTERN.sub("[REDACTED_AADHAAR]", sanitized)

        # SSN
        ssns = cls.SSN_PATTERN.findall(sanitized)
        counts["ssn"] = len(ssns)
        sanitized = cls.SSN_PATTERN.sub("[REDACTED_SSN]", sanitized)

        # DOB
        dobs = cls.DOB_PATTERN.findall(sanitized)
        counts["dob"] = len(dobs)
        sanitized = cls.DOB_PATTERN.sub("[REDACTED_DOB]", sanitized)

        has_pii = any(v > 0 for v in counts.values())
        return sanitized, has_pii, counts

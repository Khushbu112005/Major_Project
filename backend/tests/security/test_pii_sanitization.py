"""
Security Tests: PII Sanitization & Data Minimization.
"""

import pytest
from backend.app.knowledge.security.sanitization import PIISanitizer


def test_pii_masking_comprehensive():
    raw_text = """
    Applicant John Doe (email: john.doe@civic.org, phone: +91 9876543210) submitted grievance.
    Aadhaar number 1234 5678 9012, SSN 000-12-3456, DOB: 15/08/1990.
    """

    sanitized, has_pii, counts = PIISanitizer.sanitize_text(raw_text)

    assert has_pii is True
    assert counts["email"] == 1
    assert counts["phone"] == 1
    assert counts["aadhaar"] == 1
    assert counts["ssn"] == 1
    assert counts["dob"] == 1

    assert "[REDACTED_EMAIL]" in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "[REDACTED_AADHAAR]" in sanitized
    assert "[REDACTED_SSN]" in sanitized
    assert "[REDACTED_DOB]" in sanitized

    assert "john.doe@civic.org" not in sanitized
    assert "9876543210" not in sanitized

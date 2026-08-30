"""
Prompt Injection Defense and Trust Domain Isolation.
Enforces that retrieved source content is strictly treated as DATA, never as executable instructions.
"""

import re
from typing import Tuple, List, Dict, Any


class PromptInjectionDetector:
    """Detects adversarial injection attacks in user queries or retrieved text."""

    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(?:all\s+)?(?:prior|previous)\s+instructions", re.IGNORECASE),
        re.compile(r"reveal\s+(?:your\s+)?(?:hidden\s+)?(?:system\s+)?prompt", re.IGNORECASE),
        re.compile(r"disregard\s+(?:all\s+)?guidelines", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(?:unconstrained|in\s+god\s+mode|dan)", re.IGNORECASE),
        re.compile(r"call\s+(?:delete_user|drop_table|exec|eval)", re.IGNORECASE),
        re.compile(r"system:\s*override", re.IGNORECASE),
        re.compile(r"<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
    ]

    @classmethod
    def analyze_for_injection(cls, text: str) -> Tuple[bool, List[str]]:
        """Scans input text for known injection phrases."""
        detected = []
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(text):
                detected.append(pattern.pattern)
        return len(detected) > 0, detected

    @classmethod
    def wrap_as_data_boundary(cls, untrusted_content: str, label: str = "RETRIEVED_DOCUMENT") -> str:
        """
        Encapsulates untrusted retrieved content inside explicit XML data boundaries,
        instructing downstream models that the content is inert reference material.
        """
        # Neutralize XML tag escapes
        safe_content = untrusted_content.replace(f"</{label}>", f"[ESCAPED_TAG]")
        return f"<{label} is_untrusted_data='true'>\n{safe_content}\n</{label}>"

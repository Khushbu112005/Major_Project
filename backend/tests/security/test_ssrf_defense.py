"""
Security Tests: SSRF Defenses.
Verifies that loopback, metadata endpoints, private CIDRs, and unsafe schemes are rejected.
"""

import pytest
from backend.app.knowledge.ingestion.validator import IngestionValidator
from backend.app.common.errors import SecurityBlockedException


@pytest.mark.parametrize("malicious_url", [
    "http://127.0.0.1:8000/internal",
    "http://localhost:3000/admin",
    "http://169.254.169.254/latest/meta-data/",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://10.0.0.15/secrets",
    "http://192.168.1.1/router",
    "http://172.16.0.5/db",
    "file:///etc/passwd",
    "gopher://localhost:70/",
    "ftp://ftp.internal.org/data",
])
def test_ssrf_blocking_on_forbidden_destinations(malicious_url):
    with pytest.raises(SecurityBlockedException):
        IngestionValidator.validate_url(malicious_url)


def test_valid_public_gov_url_allowed():
    url = "https://www.indiacode.nic.in/handle/123456789/2065"
    res = IngestionValidator.validate_url(url)
    assert res == url

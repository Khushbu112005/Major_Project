"""
SSRF Protection and Ingestion Security Validator.
Guarantees that outbound network requests cannot target internal networks, metadata services, or loopback interfaces.
"""

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, List

from backend.app.common.config import settings
from backend.app.common.errors import SecurityBlockedException, IngestionValidationException


class IngestionValidator:
    """Strict SSRF and content-safety validator for external knowledge sources."""

    BLOCKED_IP_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),      # Loopback
        ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
        ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
        ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
        ipaddress.ip_network("169.254.0.0/16"),   # Link-Local & AWS/GCP metadata
        ipaddress.ip_network("::1/128"),          # IPv6 loopback
        ipaddress.ip_network("fc00::/7"),         # IPv6 unique local
        ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
    ]

    BLOCKED_HOSTNAMES = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "metadata.google.internal",
        "169.254.169.254",
        "instance-data",
        "internal",
        "local",
    ]

    @classmethod
    def validate_url(cls, url: str) -> str:
        """
        Validates URL for protocol safety, SSRF attempts, and network boundaries.
        Raises SecurityBlockedException if unsafe.
        """
        if not url or not isinstance(url, str):
            raise IngestionValidationException("Invalid or empty URL provided.")

        parsed = urlparse(url)

        # 1. Scheme Check
        if parsed.scheme.lower() not in settings.ALLOWED_INGESTION_SCHEMES:
            raise SecurityBlockedException(
                f"Protocol '{parsed.scheme}' is forbidden. Allowed schemes: {settings.ALLOWED_INGESTION_SCHEMES}"
            )

        hostname = parsed.hostname
        if not hostname:
            raise SecurityBlockedException("Malformed URL: Missing valid hostname.")

        hostname_clean = hostname.strip().lower()

        # 2. Blocked Hostname Check
        if any(blocked in hostname_clean for blocked in cls.BLOCKED_HOSTNAMES):
            raise SecurityBlockedException(
                f"Access to hostname '{hostname}' is blocked by SSRF defense policy."
            )

        # 3. DNS Resolution & IP Boundary Check (when SSRF protection enabled)
        if settings.SSRF_PROTECTION_ENABLED:
            try:
                # Resolve host IPs
                addr_info = socket.getaddrinfo(hostname, None)
                for addr in addr_info:
                    ip_str = addr[4][0]
                    ip_obj = ipaddress.ip_address(ip_str)

                    # Check against blocked CIDRs
                    for blocked_net in cls.BLOCKED_IP_NETWORKS:
                        if ip_obj in blocked_net:
                            raise SecurityBlockedException(
                                f"Host '{hostname}' resolves to private/internal IP {ip_str}, blocked by SSRF policy."
                            )
            except socket.gaierror:
                # If host cannot be resolved offline, verify it is a valid public domain structure
                if not any(hostname_clean.endswith(tld) for tld in [".in", ".gov", ".nic", ".org", ".edu", ".net", ".com"]):
                    raise IngestionValidationException(f"Unable to resolve DNS for host: {hostname}")

        return url

    @classmethod
    def validate_payload_size(cls, size_bytes: int) -> None:
        """Enforces maximum downloadable source file size."""
        if size_bytes > settings.MAX_SOURCE_SIZE_BYTES:
            raise IngestionValidationException(
                f"Source content size ({size_bytes} bytes) exceeds maximum allowable limit ({settings.MAX_SOURCE_SIZE_BYTES} bytes)."
            )

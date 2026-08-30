"""
SSRF-Safe Source Fetcher.
Retrieves remote legal/civic content over HTTP/HTTPS with strict timeout, size, and redirect controls.
"""

import httpx
from typing import Tuple, Dict, Any
from backend.app.common.config import settings
from backend.app.common.errors import SecurityBlockedException, IngestionValidationException
from backend.app.knowledge.ingestion.validator import IngestionValidator


class SourceFetcher:
    """Safely fetches remote content adhering to SSRF and resource limits."""

    @classmethod
    async def fetch_source_content(cls, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Validates URL, follows up to max redirects with re-validation, and fetches content.
        Returns (raw_content, metadata).
        """
        validated_url = IngestionValidator.validate_url(url)

        headers = {
            "User-Agent": "CivicSphere-Knowledge-Engine/1.0 (+https://civicsphere.org)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.5",
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.FETCH_TIMEOUT_SECONDS, connect=5.0),
            follow_redirects=False,
            headers=headers
        ) as client:
            current_url = validated_url
            redirects_followed = 0

            while True:
                response = await client.get(current_url)

                # Check redirect safety
                if response.status_code in (301, 302, 303, 307, 308):
                    redirect_url = response.headers.get("Location")
                    if not redirect_url:
                        raise IngestionValidationException("Redirect response missing Location header.")

                    redirects_followed += 1
                    if redirects_followed > settings.MAX_REDIRECTS:
                        raise IngestionValidationException(f"Exceeded maximum allowed redirects ({settings.MAX_REDIRECTS}).")

                    # Re-validate destination URL against SSRF policy
                    current_url = IngestionValidator.validate_url(redirect_url)
                    continue

                if response.status_code != 200:
                    raise IngestionValidationException(
                        f"Failed to fetch source from {url}. HTTP Status: {response.status_code}"
                    )

                # Content length verification
                content_length_header = response.headers.get("Content-Length")
                if content_length_header:
                    IngestionValidator.validate_payload_size(int(content_length_header))

                raw_bytes = response.content
                IngestionValidator.validate_payload_size(len(raw_bytes))

                content_type = response.headers.get("Content-Type", "text/plain")
                text_content = response.text

                metadata = {
                    "final_url": str(response.url),
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": len(raw_bytes),
                    "redirects_followed": redirects_followed,
                }

                return text_content, metadata

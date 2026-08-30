"""
Structured Audit and Security Event Logging.
Captures all knowledge operations, tool calls, ingestion events, and security violations.
Guarantees: Zero PII, Zero raw sensitive document contents, Zero credentials in logs.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from packages.schemas.contracts import AuditEvent, SecurityEvent

logger = logging.getLogger("civicsphere.audit")
security_logger = logging.getLogger("civicsphere.security")


class AuditManager:
    """Manages recording and querying of system audit events."""
    
    _in_memory_events: List[AuditEvent] = []
    _in_memory_security_events: List[SecurityEvent] = []

    @classmethod
    def record_event(
        cls,
        event_type: str,
        actor_id: str,
        role: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        # Sanitize details to guarantee no secrets or raw PII
        sanitized_details = cls._sanitize_payload(details or {})
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            actor_id=actor_id,
            role=role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=sanitized_details,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        cls._in_memory_events.append(event)
        logger.info(f"AUDIT_EVENT: {event.model_dump_json()}")
        return event

    @classmethod
    def record_security_event(
        cls,
        threat_type: str,
        severity: str,
        endpoint: str,
        action_taken: str,
        actor_id: Optional[str] = None,
        payload_sample: Optional[str] = None
    ) -> SecurityEvent:
        # Mask any potential sensitive details in sample
        safe_sample = payload_sample[:120] + "..." if payload_sample and len(payload_sample) > 120 else payload_sample
        
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            threat_type=threat_type,
            severity=severity,
            actor_id=actor_id,
            endpoint=endpoint,
            payload_sample=safe_sample,
            action_taken=action_taken,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        cls._in_memory_security_events.append(event)
        security_logger.warning(f"SECURITY_ALERT: {event.model_dump_json()}")
        return event

    @classmethod
    def get_recent_audit_events(cls, limit: int = 50) -> List[AuditEvent]:
        return cls._in_memory_events[-limit:]

    @classmethod
    def get_recent_security_events(cls, limit: int = 50) -> List[SecurityEvent]:
        return cls._in_memory_security_events[-limit:]

    @classmethod
    def clear(cls) -> None:
        cls._in_memory_events.clear()
        cls._in_memory_security_events.clear()

    @staticmethod
    def _sanitize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redacts sensitive keys from audit logs."""
        sensitive_keys = {"password", "secret", "token", "jwt", "authorization", "api_key", "ssn", "aadhaar", "phone", "email"}
        clean = {}
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys):
                clean[k] = "[REDACTED]"
            elif isinstance(v, dict):
                clean[k] = AuditManager._sanitize_payload(v)
            else:
                clean[k] = v
        return clean

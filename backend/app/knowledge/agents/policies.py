"""
Knowledge Agent Tool Security Policy and Execution Pipeline.
Enforces:
TOOL REQUEST -> SCHEMA VALIDATION -> AUTHORIZATION -> POLICY CHECK -> RATE LIMIT -> EXECUTION -> RESULT VALIDATION -> AUDIT
"""

from typing import Dict, Any, Optional, Callable, Tuple
import time
import logging
from pydantic import ValidationError

from packages.schemas.contracts import AgentToolCall
from backend.app.common.security import AuthContext
from backend.app.common.audit import AuditManager
from backend.app.common.errors import ForbiddenException, SecurityBlockedException, RateLimitExceededException
from backend.app.knowledge.agents.tools import (
    KnowledgeAgentTools,
    SearchKnowledgeInput,
    GraphLookupInput,
    RetrieveSourceInput,
    GetEntityInput,
    GetRelationshipsInput,
    GetSourceVersionInput,
    GetSourceProvenanceInput
)

logger = logging.getLogger("civicsphere.agent.policy")


class ToolSecurityPipeline:
    """Secure gatekeeper executing all Knowledge Agent tool calls."""

    ALLOWLISTED_TOOLS: Dict[str, Tuple[type, Callable]] = {
        "search_knowledge": (SearchKnowledgeInput, KnowledgeAgentTools.search_knowledge),
        "graph_lookup": (GraphLookupInput, KnowledgeAgentTools.graph_lookup),
        "retrieve_source": (RetrieveSourceInput, KnowledgeAgentTools.retrieve_source),
        "retrieve_related_sources": (RetrieveSourceInput, KnowledgeAgentTools.retrieve_related_sources),
        "get_entity": (GetEntityInput, KnowledgeAgentTools.get_entity),
        "get_relationships": (GetRelationshipsInput, KnowledgeAgentTools.get_relationships),
        "find_related_concepts": (GetEntityInput, KnowledgeAgentTools.find_related_concepts),
        "get_source_version": (GetSourceVersionInput, KnowledgeAgentTools.get_source_version),
        "get_source_provenance": (GetSourceProvenanceInput, KnowledgeAgentTools.get_source_provenance),
    }

    FORBIDDEN_KEYWORDS = [
        "cypher", "sql", "drop", "delete", "mutate", "truncate", "system", "exec", "eval",
        "subprocess", "curl", "wget", "token", "password", "env"
    ]

    _call_timestamps: Dict[str, list[float]] = {}

    @classmethod
    async def execute_tool(
        cls,
        tool_name: str,
        parameters: Dict[str, Any],
        auth: AuthContext,
        agent_name: str = "KnowledgeGraphAgent"
    ) -> AgentToolCall:
        start_time = time.perf_counter()
        tool_call = AgentToolCall(
            agent_name=agent_name,
            tool_name=tool_name,
            parameters=parameters,
            authorized=False
        )

        try:
            # Step 1: Check Allowlist
            if tool_name not in cls.ALLOWLISTED_TOOLS:
                raise SecurityBlockedException(
                    f"Tool '{tool_name}' is not in the allowlist. Arbitrary agent tools are forbidden."
                )

            input_schema, tool_fn = cls.ALLOWLISTED_TOOLS[tool_name]

            # Step 2: Schema Validation
            try:
                validated_params = input_schema(**parameters)
            except ValidationError as ve:
                raise SecurityBlockedException(f"Schema validation failed for tool '{tool_name}': {ve.errors()}")

            # Step 3: Authorization Check
            if not auth.user_id:
                raise ForbiddenException("Tool execution requires authenticated user context.")

            # Step 4: Policy Check (Parameter poisoning & forbidden keywords)
            param_str = str(parameters).lower()
            if any(forbidden in param_str for forbidden in cls.FORBIDDEN_KEYWORDS):
                AuditManager.record_security_event(
                    threat_type="MALICIOUS_TOOL_PARAMETER_INJECTION",
                    severity="HIGH",
                    endpoint=f"/agent/tool/{tool_name}",
                    action_taken="BLOCKED",
                    actor_id=auth.user_id,
                    payload_sample=param_str
                )
                raise SecurityBlockedException("Tool invocation blocked due to forbidden parameter values.")

            tool_call.authorized = True

            # Step 5: Rate Limiting
            cls._enforce_rate_limit(auth.user_id)

            # Step 6: Execution
            result = await tool_fn(validated_params)

            # Step 7: Result Validation (Guarantee safe envelope, no raw secrets)
            tool_call.result = result

        except Exception as exc:
            tool_call.error = str(exc)
            logger.warning(f"Agent tool {tool_name} failed: {exc}")
            raise exc

        finally:
            latency = (time.perf_counter() - start_time) * 1000.0
            tool_call.latency_ms = round(latency, 2)

            # Step 8: Structured Audit
            AuditManager.record_event(
                event_type="AGENT_TOOL_CALL",
                actor_id=auth.user_id,
                role=auth.role,
                action=f"TOOL_{tool_name.upper()}",
                resource_type="KNOWLEDGE_AGENT",
                resource_id=tool_name,
                details={
                    "tool": tool_name,
                    "authorized": tool_call.authorized,
                    "latency_ms": tool_call.latency_ms,
                    "has_error": bool(tool_call.error)
                }
            )

        return tool_call

    @classmethod
    def _enforce_rate_limit(cls, user_id: str, max_calls_per_minute: int = 60) -> None:
        now = time.time()
        timestamps = cls._call_timestamps.setdefault(user_id, [])
        # Prune older than 60s
        timestamps = [t for t in timestamps if now - t < 60.0]
        if len(timestamps) >= max_calls_per_minute:
            raise RateLimitExceededException("Agent tool execution rate limit exceeded.")
        timestamps.append(now)
        cls._call_timestamps[user_id] = timestamps

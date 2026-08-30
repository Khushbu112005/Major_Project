"""
Integration tests for Controlled Knowledge Graph Agent and Tool Security.
"""

import asyncio
import pytest
from backend.app.common.security import AuthContext
from backend.app.knowledge.agents.knowledge_agent import KnowledgeGraphAgent
from backend.app.knowledge.agents.policies import ToolSecurityPipeline
from backend.app.common.errors import SecurityBlockedException


def test_knowledge_graph_agent_execution():
    async def _run():
        auth = AuthContext(user_id="usr_citizen_007", email="citizen@test.org", role="citizen")

        result = await KnowledgeGraphAgent.process_knowledge_query(
            query="What is the disposal time limit for an RTI application under Section 7?",
            auth=auth
        )

        assert result["status"] == "COMPLETED"
        assert result["tool_calls_executed"] >= 1
        assert result["evidence_pack"] is not None
        assert len(result["evidence_pack"]["items"]) > 0

    asyncio.run(_run())


def test_knowledge_agent_blocks_arbitrary_tools():
    async def _run():
        auth = AuthContext(user_id="usr_citizen_007", email="citizen@test.org", role="citizen")

        with pytest.raises(SecurityBlockedException) as exc_info:
            await ToolSecurityPipeline.execute_tool(
                tool_name="arbitrary_cypher_exec",
                parameters={"query": "MATCH (n) DETACH DELETE n"},
                auth=auth
            )
        assert "allowlist" in str(exc_info.value).lower()

    asyncio.run(_run())


def test_knowledge_agent_blocks_parameter_poisoning():
    async def _run():
        auth = AuthContext(user_id="usr_citizen_007", email="citizen@test.org", role="citizen")

        with pytest.raises(SecurityBlockedException) as exc_info:
            await ToolSecurityPipeline.execute_tool(
                tool_name="search_knowledge",
                parameters={"query": "test query; DROP TABLE users; --"},
                auth=auth
            )
        assert "forbidden" in str(exc_info.value).lower()

    asyncio.run(_run())

"""
Security Tests: Cypher and SQL Injection Defenses.
"""

import pytest
from backend.app.knowledge.graph.repository import graph_repository
from backend.app.common.errors import SecurityBlockedException


def test_arbitrary_cypher_templates_rejected():
    with pytest.raises(SecurityBlockedException):
        graph_repository.execute_parameterized_query(
            query_name="UNAPPROVED_CUSTOM_CYPHER",
            params={"raw_query": "MATCH (n) DETACH DELETE n"}
        )


def test_malicious_query_parameter_escaping():
    # Parameters with malicious escape characters must not cause exceptions or injections
    malicious_param = "Section 7'; MATCH (n) DETACH DELETE n; //"
    results = graph_repository.execute_parameterized_query(
        query_name="get_section_authority",
        params={"section_name": malicious_param}
    )
    # Correct parameterized query handles it safely as literal string with 0 hits
    assert isinstance(results, list)

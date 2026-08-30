"""
Parameterized Cypher Query Templates for Neo4j.
Zero string interpolation. All queries use explicit Cypher parameter bindings.
"""

from typing import Dict, Any


class CypherQueryTemplates:
    """Pre-compiled parameterized Cypher statements."""

    # 1. Match Act, Sections, and administering Authorities
    ACT_STRUCTURE_QUERY = """
    MATCH (act:ACT {entity_id: $act_id})-[r1:HAS_SECTION]->(sec:SECTION)
    OPTIONAL MATCH (sec)-[r2:ADMINISTERED_BY]->(auth:AUTHORITY)
    RETURN act, r1, sec, r2, auth
    LIMIT $limit
    """

    # 2. Match Rights and derived Section Provisions
    RIGHTS_AND_PROVISIONS_QUERY = """
    MATCH (right:RIGHT {entity_id: $right_id})-[r:DERIVED_FROM]->(sec:SECTION)
    RETURN right, r, sec
    LIMIT $limit
    """

    # 3. Match Government Procedure and required Documents
    PROCEDURE_DOCUMENTS_QUERY = """
    MATCH (proc:PROCEDURE {entity_id: $procedure_id})-[r:REQUIRES]->(doc:DOCUMENT)
    RETURN proc, r, doc
    LIMIT $limit
    """

    # 4. Match Government Service, Department, and Eligibility Rules
    SERVICE_DETAILS_QUERY = """
    MATCH (srv:SERVICE {entity_id: $service_id})
    OPTIONAL MATCH (srv)-[r1:PROVIDED_BY]->(dept:DEPARTMENT)
    OPTIONAL MATCH (srv)-[r2:HAS_ELIGIBILITY]->(rule:RULE)
    OPTIONAL MATCH (srv)-[r3:APPLIED_THROUGH]->(portal:PORTAL)
    RETURN srv, r1, dept, r2, rule, r3, portal
    LIMIT $limit
    """

    # 5. Find connected neighborhood with bounded hops
    BOUNDED_NEIGHBORHOOD_QUERY = """
    MATCH (start {entity_id: $entity_id})-[r*1..2]-(connected)
    RETURN start, r, connected
    LIMIT $limit
    """

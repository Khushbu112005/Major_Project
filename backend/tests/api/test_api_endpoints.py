"""
API Endpoint Integration Tests for FastAPI Knowledge Server.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check_endpoint(test_client: TestClient):
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "module_c_knowledge_graph"


def test_search_api_endpoint(test_client: TestClient, citizen_auth_headers: dict):
    payload = {
        "query": "What is the procedure to file an RTI request under Section 6?",
        "jurisdiction": "IN",
        "top_k": 3
    }
    resp = test_client.post("/api/v1/knowledge/search", json=payload, headers=citizen_auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["success"] is True
    assert "request_id" in body
    assert body["confidence"] > 0.50
    assert len(body["data"]["items"]) > 0

    item = body["data"]["items"][0]
    assert "Section 6" in item["text"]
    assert item["source_title"] == "Right to Information Act, 2005"


def test_list_sources_endpoint(test_client: TestClient, citizen_auth_headers: dict):
    resp = test_client.get("/api/v1/knowledge/sources", headers=citizen_auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["success"] is True
    assert len(body["data"]) >= 3


def test_admin_overview_forbidden_for_citizen(test_client: TestClient, citizen_auth_headers: dict):
    resp = test_client.get("/api/v1/knowledge/admin/overview", headers=citizen_auth_headers)
    assert resp.status_code == 403


def test_admin_overview_allowed_for_admin(test_client: TestClient, admin_auth_headers: dict):
    resp = test_client.get("/api/v1/knowledge/admin/overview", headers=admin_auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["total_sources"] >= 3
    assert body["data"]["total_graph_entities"] > 0

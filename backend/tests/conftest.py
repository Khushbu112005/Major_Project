"""
Pytest Test Fixtures for CivicSphere Module C.
Configures test environment, initializes seed data, and provides test client.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.common.security import AuthContext
from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.graph.repository import graph_repository
from backend.app.knowledge.ingestion.vector_writer import vector_store
from backend.app.common.audit import AuditManager
from data.seed.seed_data import seed_knowledge_base


@pytest.fixture(autouse=True)
def setup_test_knowledge_base():
    """Seeds the knowledge base before tests and clears on teardown."""
    source_registry.clear()
    graph_repository.clear()
    vector_store.clear()
    AuditManager.clear()

    # Seed verified sources synchronously
    asyncio.run(seed_knowledge_base())
    yield


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def citizen_auth_headers():
    return {
        "X-User-Id": "usr_citizen_101",
        "X-User-Email": "citizen@civicsphere.org",
        "X-User-Role": "citizen"
    }


@pytest.fixture
def admin_auth_headers():
    return {
        "X-User-Id": "usr_admin_999",
        "X-User-Email": "admin@civicsphere.org",
        "X-User-Role": "admin"
    }

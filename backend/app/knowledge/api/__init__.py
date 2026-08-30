"""Knowledge API package."""

from backend.app.knowledge.api.search import router as search_router
from backend.app.knowledge.api.graph import router as graph_router
from backend.app.knowledge.api.sources import router as sources_router
from backend.app.knowledge.api.ingestion import router as ingestion_router
from backend.app.knowledge.api.admin import router as admin_router

__all__ = [
    "search_router",
    "graph_router",
    "sources_router",
    "ingestion_router",
    "admin_router",
]

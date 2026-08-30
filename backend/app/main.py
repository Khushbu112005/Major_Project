"""
CivicSphere Main Application Entrypoint.
Exposes Module C Knowledge + Agentic Graph Engine APIs.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
import time
import logging

from packages.schemas.contracts import ApiResponse
from backend.app.common.config import settings
from backend.app.common.errors import (
    CivicSphereException,
    civicsphere_exception_handler,
    generic_exception_handler
)
from backend.app.knowledge.api.search import router as search_router
from backend.app.knowledge.api.graph import router as graph_router
from backend.app.knowledge.api.sources import router as sources_router
from backend.app.knowledge.api.ingestion import router as ingestion_router
from backend.app.knowledge.api.admin import router as admin_router

logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("civicsphere.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Initializing {settings.APP_NAME} in [{settings.ENVIRONMENT}] mode...")
    # Initialize seed data if available
    from backend.app.knowledge.sources.registry import source_registry
    logger.info(f"Knowledge Engine ready. Currently holding {len(source_registry.list_sources())} registered sources.")
    yield
    logger.info("Shutting down CivicSphere Knowledge Engine...")


app = FastAPI(
    title="CivicSphere AI — Module C (Knowledge + Agentic Graph)",
    version="1.0.0",
    description="Production-quality, secure, evidence-grounded intelligence backbone for CivicSphere AI.",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation / Request ID and Latency Middleware
@app.middleware("http")
async def request_correlation_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    request.state.request_id = req_id
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-Id"] = req_id
    response.headers["X-Process-Time-Ms"] = str(round(process_time_ms, 2))
    return response


# Exception Handlers
app.add_exception_handler(CivicSphereException, civicsphere_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register API Routers
app.include_router(search_router, prefix=settings.API_PREFIX)
app.include_router(graph_router, prefix=settings.API_PREFIX)
app.include_router(sources_router, prefix=settings.API_PREFIX)
app.include_router(ingestion_router, prefix=settings.API_PREFIX)
app.include_router(admin_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for liveness probes."""
    return {"status": "HEALTHY", "service": "module_c_knowledge_graph", "timestamp": time.time()}


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe verifying vector and graph repository availability."""
    from backend.app.knowledge.graph.repository import graph_repository
    from backend.app.knowledge.ingestion.vector_writer import vector_store
    return {
        "ready": True,
        "graph_nodes": len(graph_repository._nodes),
        "vector_records": len(vector_store._vectors)
    }

"""
Graph Exploration and Entity Traversal APIs.
Exposes bounded neighborhood retrieval for frontend visualizers and specialist agents.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from packages.schemas.contracts import ApiResponse
from backend.app.common.security import AuthContext, get_current_user_context
from backend.app.knowledge.graph.repository import graph_repository
from backend.app.knowledge.graph.traversal import GraphTraversalService, GraphExplorationResponse
from backend.app.knowledge.graph.authorization import GraphAuthorizationPolicy

router = APIRouter(prefix="/knowledge", tags=["Knowledge Graph"])


class GraphQueryRequest(BaseModel):
    query_template: str = Field(description="Name of the pre-approved parameterized query")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters bound to query template")


@router.get("/entities/{entity_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_graph_entity(
    entity_id: str,
    auth: AuthContext = Depends(get_current_user_context)
) -> ApiResponse[Dict[str, Any]]:
    """Fetches a single entity with its verified attributes and source IDs."""
    entity = graph_repository.get_entity(entity_id)
    authorized_list = GraphAuthorizationPolicy.filter_entities([entity], auth)
    if not authorized_list:
        return ApiResponse(success=False, warnings=["Entity access restricted by policy."])

    return ApiResponse(
        success=True,
        data=entity.model_dump(),
        sources=[{"source_id": sid} for sid in entity.source_ids]
    )


@router.get("/entities/{entity_id}/relationships", response_model=ApiResponse[Dict[str, Any]])
async def get_entity_relationships(
    entity_id: str,
    depth: int = Query(default=1, ge=1, le=2, description="Bounded traversal depth"),
    limit_per_node: int = Query(default=8, ge=1, le=15),
    auth: AuthContext = Depends(get_current_user_context)
) -> ApiResponse[Dict[str, Any]]:
    """Explores the bounded neighborhood surrounding a graph entity."""
    exploration = GraphTraversalService.explore_entity(
        entity_id=entity_id,
        depth=depth,
        limit_per_node=limit_per_node
    )

    # Authorization filtering
    auth_entities = GraphAuthorizationPolicy.filter_entities(
        [exploration.selected_entity] + exploration.neighborhood_entities,
        auth
    )
    auth_ids = {e.entity_id for e in auth_entities}
    auth_rels = GraphAuthorizationPolicy.filter_relationships(exploration.relationships, auth_ids)

    result_data = {
        "selected_entity": exploration.selected_entity.model_dump(),
        "neighborhood": [e.model_dump() for e in auth_entities if e.entity_id != entity_id],
        "relationships": [r.model_dump() for r in auth_rels],
        "total_nodes": len(auth_entities),
        "total_edges": len(auth_rels)
    }

    return ApiResponse(
        success=True,
        data=result_data,
        sources=[{"source_id": sid} for sid in exploration.sources]
    )


@router.post("/graph/query", response_model=ApiResponse[Dict[str, Any]])
async def execute_parameterized_graph_query(
    payload: GraphQueryRequest,
    auth: AuthContext = Depends(get_current_user_context)
) -> ApiResponse[Dict[str, Any]]:
    """Executes a pre-compiled parameterized query against the knowledge graph."""
    results = graph_repository.execute_parameterized_query(
        query_name=payload.query_template,
        params=payload.parameters
    )

    return ApiResponse(
        success=True,
        data={"results": results, "count": len(results)}
    )

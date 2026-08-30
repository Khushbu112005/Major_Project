"""
Controlled Knowledge Graph Agent Tools.
Strict allowlist of read-only tools with strongly typed Pydantic input and output schemas.
Explicitly FORBIDS arbitrary SQL, Cypher, shell commands, filesystem access, or external network requests.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time

from backend.app.common.errors import NotFoundException, SecurityBlockedException
from backend.app.knowledge.domain.entities import EntityType
from backend.app.knowledge.domain.retrieval import RetrievalRequest, FilterCriteria
from backend.app.knowledge.sources.registry import source_registry
from backend.app.knowledge.graph.repository import graph_repository
from backend.app.knowledge.graph.traversal import GraphTraversalService
from backend.app.knowledge.retrieval.hybrid import hybrid_retrieval_service


# --- Tool Input Schemas ---

class SearchKnowledgeInput(BaseModel):
    query: str = Field(description="Search query string regarding civic/legal provisions")
    jurisdiction: Optional[str] = Field(default="IN", description="Jurisdiction filter (e.g. 'IN')")
    top_k: int = Field(default=5, ge=1, le=15, description="Maximum number of evidence items")


class GraphLookupInput(BaseModel):
    entity_name: str = Field(description="Name or alias of entity (e.g. 'RTI Act', 'Section 6')")
    max_depth: int = Field(default=2, ge=1, le=3, description="Traversal depth")


class RetrieveSourceInput(BaseModel):
    source_id: str = Field(description="Unique ID of source")


class GetEntityInput(BaseModel):
    entity_id: str = Field(description="Unique entity ID in graph")


class GetRelationshipsInput(BaseModel):
    entity_id: str = Field(description="Unique entity ID in graph")
    limit: int = Field(default=10, ge=1, le=25)


class GetSourceVersionInput(BaseModel):
    source_id: str = Field(description="Unique ID of source")
    version_number: Optional[int] = Field(default=None, description="Specific version number or latest")


class GetSourceProvenanceInput(BaseModel):
    chunk_id: str = Field(description="Unique chunk ID to trace provenance")


# --- Tool Executor Implementation ---

class KnowledgeAgentTools:
    """Implementations for all allowlisted tools."""

    @staticmethod
    async def search_knowledge(params: SearchKnowledgeInput) -> Dict[str, Any]:
        filters = FilterCriteria(jurisdiction=params.jurisdiction)
        req = RetrievalRequest(query=params.query, filters=filters, top_k=params.top_k)
        pack = await hybrid_retrieval_service.retrieve(req)
        return pack.model_dump()

    @staticmethod
    async def graph_lookup(params: GraphLookupInput) -> Dict[str, Any]:
        entities = graph_repository.find_entities_by_name(params.entity_name, limit=5)
        if not entities:
            return {"found": False, "message": f"No graph entities matched '{params.entity_name}'"}

        primary = entities[0]
        exploration = GraphTraversalService.explore_entity(primary.entity_id, depth=params.max_depth)
        return {"found": True, "exploration": exploration.model_dump()}

    @staticmethod
    async def retrieve_source(params: RetrieveSourceInput) -> Dict[str, Any]:
        source = source_registry.get_source(params.source_id)
        return source.model_dump()

    @staticmethod
    async def retrieve_related_sources(params: RetrieveSourceInput) -> Dict[str, Any]:
        source = source_registry.get_source(params.source_id)
        # Find sources sharing jurisdiction and domain
        related = source_registry.list_sources(jurisdiction=source.jurisdiction, limit=5)
        return {"related_sources": [s.model_dump() for s in related if s.source_id != source.source_id]}

    @staticmethod
    async def get_entity(params: GetEntityInput) -> Dict[str, Any]:
        entity = graph_repository.get_entity(params.entity_id)
        return entity.model_dump()

    @staticmethod
    async def get_relationships(params: GetRelationshipsInput) -> Dict[str, Any]:
        _, rels = graph_repository.get_neighborhood(params.entity_id, max_depth=1, limit_per_node=params.limit)
        return {"relationships": [r.model_dump() for r in rels]}

    @staticmethod
    async def find_related_concepts(params: GetEntityInput) -> Dict[str, Any]:
        exploration = GraphTraversalService.explore_entity(params.entity_id, depth=2)
        return {"concepts": [e.model_dump() for e in exploration.neighborhood_entities]}

    @staticmethod
    async def search_by_metadata(params: Dict[str, Any]) -> Dict[str, Any]:
        sources = source_registry.list_sources(
            jurisdiction=params.get("jurisdiction"),
            limit=params.get("limit", 10)
        )
        return {"sources": [s.model_dump() for s in sources]}

    @staticmethod
    async def get_source_version(params: GetSourceVersionInput) -> Dict[str, Any]:
        versions = source_registry.get_versions(params.source_id)
        if params.version_number:
            match = next((v for v in versions if v.version_number == params.version_number), None)
            if not match:
                raise NotFoundException(f"Version {params.version_number} of source {params.source_id} not found.")
            return match.model_dump()
        return {"versions": [v.model_dump() for v in versions]}

    @staticmethod
    async def get_source_provenance(params: GetSourceProvenanceInput) -> Dict[str, Any]:
        chunk = source_registry.get_chunk(params.chunk_id)
        if not chunk:
            raise NotFoundException(f"Chunk '{params.chunk_id}' not found.")
        source = source_registry.get_source(chunk.source_id)
        return {
            "chunk": chunk.model_dump(),
            "source": source.model_dump(),
            "provenance_verified": source.verification_status.value == "ACTIVE"
        }

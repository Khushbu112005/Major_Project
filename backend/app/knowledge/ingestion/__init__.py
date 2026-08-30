"""Ingestion package."""

from backend.app.knowledge.ingestion.validator import IngestionValidator
from backend.app.knowledge.ingestion.fetcher import SourceFetcher
from backend.app.knowledge.ingestion.cleaner import ContentCleaner, StructuralLegalParser
from backend.app.knowledge.ingestion.chunker import DeterministicChunker
from backend.app.knowledge.ingestion.entity_extractor import EntityExtractor
from backend.app.knowledge.ingestion.relationship_extractor import RelationshipExtractor
from backend.app.knowledge.ingestion.embedder import ChunkEmbedder
from backend.app.knowledge.ingestion.graph_writer import GraphWriter
from backend.app.knowledge.ingestion.vector_writer import InMemoryVectorStore, vector_store
from backend.app.knowledge.ingestion.pipeline import IngestionPipeline, ingestion_pipeline

__all__ = [
    "IngestionValidator",
    "SourceFetcher",
    "ContentCleaner",
    "StructuralLegalParser",
    "DeterministicChunker",
    "EntityExtractor",
    "RelationshipExtractor",
    "ChunkEmbedder",
    "GraphWriter",
    "InMemoryVectorStore",
    "vector_store",
    "IngestionPipeline",
    "ingestion_pipeline",
]

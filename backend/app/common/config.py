"""
Configuration management for CivicSphere Module C.
Loads settings from environment variables with strong typing and security defaults.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "CivicSphere-Knowledge-Engine"
    API_PREFIX: str = "/api/v1"

    # Security & Access
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    JWT_SECRET_KEY: str = "development-secret-key-32-chars-long-minimum!"
    JWT_ALGORITHM: str = "HS256"
    MAX_SOURCE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB max payload

    # Ingestion & SSRF Protections
    SSRF_PROTECTION_ENABLED: bool = True
    ALLOWED_INGESTION_SCHEMES: List[str] = ["http", "https"]
    FETCH_TIMEOUT_SECONDS: float = 10.0
    MAX_REDIRECTS: int = 3

    # Database & Graph
    DATABASE_URL: str = "sqlite+aiosqlite:///./civicsphere_knowledge.db"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "civicsphere_secret"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_MAX_DEPTH: int = 3
    NEO4J_DEFAULT_DEPTH: int = 2
    NEO4J_MAX_NEIGHBORS: int = 10

    # AI Providers
    EMBEDDING_PROVIDER: str = "mock"  # mock, openai, voyage, huggingface
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 384
    LLM_PROVIDER: str = "mock"  # mock, anthropic, openai
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    RERANKER_PROVIDER: str = "heuristic"  # heuristic, cohere, cross-encoder

    # Retrieval Engine Config
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 25
    RRF_K: int = 60
    EVIDENCE_CONFIDENCE_THRESHOLD_STRONG: float = 0.90
    EVIDENCE_CONFIDENCE_THRESHOLD_GOOD: float = 0.75
    EVIDENCE_CONFIDENCE_THRESHOLD_LIMITED: float = 0.50


settings = Settings()

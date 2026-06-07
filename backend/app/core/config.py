"""
Centralised, type-safe application configuration.

All settings are read from environment variables (or a local ``.env`` file)
and validated at startup. Nothing in the codebase should read ``os.environ``
directly — import ``settings`` from here instead.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    APP_NAME: str = "PriceWise AI Engine"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False  # set True in production for structured logs

    # ---- Security / Auth ----
    # MUST be overridden in production. Generate with: openssl rand -hex 32
    SECRET_KEY: str = "dev-insecure-change-me-please-0000000000000000000000000000"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    ALGORITHM: str = "HS256"

    # Comma-separated list of allowed CORS origins.
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # ---- Database ----
    # async SQLAlchemy URL. Defaults to local SQLite so the app runs with zero setup.
    DATABASE_URL: str = "sqlite+aiosqlite:///./pricewise.db"

    # ---- Cache / Redis ----
    # If empty, an in-process cache is used (fine for a single instance / dev).
    REDIS_URL: str = ""
    CACHE_TTL_SECONDS: int = 60 * 60 * 24  # 24h price/review caching per the spec

    # ---- Rate limiting ----
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_CHAT: str = "20/minute"

    # ---- AI / LLM cost control ----
    # Provider for the conversational layer. "none" = pure rule-based (zero cost).
    LLM_PROVIDER: Literal["none", "anthropic", "ollama"] = "none"
    LLM_MODEL: str = "claude-haiku-4-5-20251001"
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MAX_TOKENS: int = 512
    # Hard monthly token budget across all users. 0 = unlimited (rule-based only anyway).
    LLM_MONTHLY_TOKEN_BUDGET: int = 2_000_000
    # Per-user daily LLM call cap (defence-in-depth against cost blow-ups).
    LLM_USER_DAILY_CALL_CAP: int = 50

    # ---- External data providers (all optional; mock data by default) ----
    DATA_PROVIDER: Literal["mock", "google_cse"] = "mock"
    GOOGLE_CSE_API_KEY: str = ""
    GOOGLE_CSE_ENGINE_ID: str = ""

    # ---- LLM Orchestration ----
    OPENAI_API_KEY: str = ""
    # Tiered model routing. The router picks a tier by task complexity/cost.
    LLM_MODEL_CHEAP: str = "claude-haiku-4-5-20251001"      # classification, routing, short replies
    LLM_MODEL_STANDARD: str = "claude-haiku-4-5-20251001"   # default generation
    LLM_MODEL_DEEP: str = "claude-sonnet-4-6"               # planning / hard reasoning
    # Context & memory budgets (token estimates; 1 token ~= 4 chars heuristic).
    MAX_CONTEXT_TOKENS: int = 8000
    SUMMARIZE_THRESHOLD_TOKENS: int = 3000   # roll older turns into summary past this
    WORKING_MEMORY_TURNS: int = 8            # recent turns kept verbatim
    RAG_TOP_K: int = 5
    # Reliability
    LLM_MAX_RETRIES: int = 2
    LLM_RETRY_BASE_DELAY: float = 0.5
    # Vector / embeddings (pluggable)
    VECTOR_BACKEND: str = "memory"           # memory | pgvector
    EMBEDDING_PROVIDER: str = "local"        # local (hash, $0) | openai
    EMBEDDING_DIM: int = 256
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

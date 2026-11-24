"""Centralized, Pydantic-validated application settings."""

from pathlib import Path
from urllib.parse import quote, urlunsplit

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load the project-root .env, no matter which folder the app is started from.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Load and validate environment variables from `.env`.

    - `extra="ignore"` lets `.env` keep unused keys (e.g. GROQ_FALLBACK_API_KEY)
      without failing startup.
    - Required fields raise a clear validation error at import time if missing.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- REASONING ENGINE (GROQ) ---
    GROQ_API_KEY: str
    GROQ_FALLBACK_API_KEY: str | None = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"  # main model (planner + responder)
    GROQ_FAST_MODEL: str = "openai/gpt-oss-20b"  # fast model (guardrails + fallback)

    # --- EVAL JUDGE (separate Groq key so evals don't use up the main key) ---
    JUDGE_GROQ: str | None = None

    # --- LLM GATEWAY (CLOUDFLARE AI GATEWAY) ---
    CF_ACCOUNT_ID: str
    CF_GATEWAY_ID: str
    CF_AIG_TOKEN: str

    # --- EMBEDDINGS (GEMINI) ---
    GEMINI_API_KEY: str

    # --- JINA AI (embeddings + reranker) — optional, not used yet ---
    JINA_API_KEY: str | None = None

    # --- QDRANT VECTOR DB ---
    QDRANT_URL: str = Field(
        validation_alias=AliasChoices("QDRANT_URL", "QDRANT_CLUSTER_ENDPOINT")
    )
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "enterprise_rag"

    # --- NEON SERVERLESS POSTGRES (LangGraph checkpointer) ---
    NEON_DB_URL: str | None = None

    # --- UPSTASH REDIS (rate limiting) ---
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None

    # --- UI ---
    BACKEND_URL: str = "http://localhost:8000"

    # --- API SAFETY ---
    API_KEY: str | None = Field(default=None, alias="RAG_API_KEY")
    RATE_LIMIT_PER_MINUTE: int = 20
    STRICT_STARTUP: bool = False

    # --- OBSERVABILITY ---
    LOGFIRE_TOKEN: str | None = None
    LOGFIRE_BASE_URL: str | None = (
        None  # e.g. https://logfire-eu.pydantic.dev for EU tokens
    )

    @field_validator(
        "QDRANT_API_KEY",
        "JINA_API_KEY",
        "JUDGE_GROQ",
        "GROQ_FALLBACK_API_KEY",
        "NEON_DB_URL",
        "UPSTASH_REDIS_REST_URL",
        "UPSTASH_REDIS_REST_TOKEN",
        "LOGFIRE_TOKEN",
        mode="before",
    )
    @classmethod
    def _empty_as_none(cls, v):
        """Treat empty values in .env (e.g. `JINA_API_KEY=`) as unset."""
        if v == "" or v is None:
            return None
        return v

    @field_validator("BACKEND_URL", mode="before")
    @classmethod
    def _empty_backend_url_as_default(cls, v):
        """`BACKEND_URL=` (empty) in .env falls back to the local backend."""
        return v or "http://localhost:8000"

    @property
    def judge_api_key(self) -> str:
        """Dedicated eval judge key, falling back to the main Groq key."""
        return self.JUDGE_GROQ or self.GROQ_API_KEY

    @property
    def postgres_uri(self) -> str:
        """LangGraph Postgres checkpointer URI (Neon).

        Serverless Postgres closes idle connections, so append TCP keepalive
        options to keep the connection pool healthy between requests.
        """
        if not self.NEON_DB_URL:
            raise ValueError("NEON_DB_URL is not set in .env")
        base = self.NEON_DB_URL.rstrip("/")
        keepalive = (
            "keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5"
        )
        if "?" in base:
            return f"{base}&{keepalive}"
        return f"{base}?{keepalive}"

    @property
    def redis_url(self) -> str:
        """TLS Redis URL derived from Upstash REST credentials.

        Upstash exposes the same host for REST and TLS Redis. The REST token is
        used as the Redis password under the default username. The result is
        passed to `limits` for rate limiting and to the health checker.
        """
        if not (self.UPSTASH_REDIS_REST_URL and self.UPSTASH_REDIS_REST_TOKEN):
            raise ValueError(
                "UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN are not set in .env"
            )
        host = self.UPSTASH_REDIS_REST_URL.replace("https://", "").rstrip("/")
        token = quote(self.UPSTASH_REDIS_REST_TOKEN, safe="")
        netloc = f"default:{token}@{host}"
        return urlunsplit(("rediss", netloc, "/0", "ssl_cert_reqs=required", ""))


# Singleton used across the app.
settings = Settings()

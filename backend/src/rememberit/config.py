"""Application configuration via environment variables."""

from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/rememberit"
    DATABASE_REQUIRE_SSL: bool = False

    # LLM (OpenRouter)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-haiku-4.5"
    LLM_MAX_RETRIES: int = 3

    # Embedding
    EMBEDDING_MODEL_NAME: str = "paraphrase-multilingual-mpnet-base-v2"
    EMBEDDING_CACHE_DIR: str = "./models"

    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 6789
    API_PREFIX: str = "/api/v1"

    # Retrieval tuning
    SCORE_WEIGHT_SEMANTIC: float = 0.5
    SCORE_WEIGHT_IMPORTANCE: float = 0.3
    SCORE_WEIGHT_TIME: float = 0.2
    TIME_DECAY_LAMBDA: float = 0.1
    MAX_RESULTS_PER_QUERY: int = 5
    MAX_TOKENS_PER_QUERY: int = 2000
    SIMILARITY_THRESHOLD: float = 0.3

    # Extraction
    DEDUP_SIMILARITY_THRESHOLD: float = 0.9
    MAX_SEGMENTS_PER_CONVERSATION: int = 3  # Cap LLM calls per conversation for cost control

    model_config = {"env_file": ".env", "case_sensitive": True}

    @model_validator(mode="after")
    def _fix_asyncpg_sslmode(self):
        """Strip sslmode from asyncpg URLs and set DATABASE_REQUIRE_SSL."""
        url = self.DATABASE_URL
        if "+asyncpg" not in url:
            return self
        parts = urlsplit(url)
        params = parse_qs(parts.query)
        if "sslmode" not in params:
            return self
        sslmode = params.pop("sslmode")[0]
        new_query = urlencode(params, doseq=True)
        self.DATABASE_URL = urlunsplit(parts._replace(query=new_query))
        if sslmode in ("require", "verify-ca", "verify-full"):
            self.DATABASE_REQUIRE_SSL = True
        return self


settings = Settings()
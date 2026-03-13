"""Embedding model management - singleton pattern for efficiency."""

import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from rememberit.config import settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Get or load the sentence-transformers model (singleton)."""
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL_NAME)
        _model = SentenceTransformer(
            settings.EMBEDDING_MODEL_NAME,
            cache_folder=settings.EMBEDDING_CACHE_DIR,
        )
        logger.info("Embedding model loaded successfully (dim=%d)", _model.get_sentence_embedding_dimension())
    return _model


def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a single text string."""
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for multiple texts (batched)."""
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=32)
    return [e.tolist() for e in embeddings]


def is_model_loaded() -> bool:
    """Check if the embedding model is currently loaded."""
    return _model is not None

"""Vector embedding service for MTG card similarity search.

- Generate vector embeddings using sentence-transformers
"""

import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_cache: dict[str, SentenceTransformer] = {}


def get_model() -> SentenceTransformer:
    """Load and cache the sentence-transformer model."""
    if "model" not in _cache:
        logger.info("Loading sentence-transformer model '%s'...", MODEL_NAME)
        _cache["model"] = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded.")
    return _cache["model"]


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Batch-encode a list of text strings into embedding vectors.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each a list of floats).
    """
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


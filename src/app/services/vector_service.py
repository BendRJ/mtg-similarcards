"""Vector embedding service for MTG card similarity search.

Provides functions to:
- Build text representations of cards for embedding
- Generate vector embeddings using sentence-transformers
- Query for similar cards using cosine distance (pgvector)
"""

import logging
from typing import Any

from sentence_transformers import SentenceTransformer

from database.db import get_cursor

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


def build_card_text(card: dict[str, Any]) -> str:
    """Assemble a text representation of a card for embedding.

    Combines the most semantically relevant fields into a single string.

    Args:
        card: A dict with card column values (from a DB row or similar).
    """
    parts: list[str] = []

    if type_line := card.get("type_line"):
        parts.append(type_line)

    if oracle_text := card.get("oracle_text"):
        parts.append(oracle_text)

    if keywords := card.get("keywords"):
        if isinstance(keywords, list) and keywords:
            parts.append(f"Keywords: {', '.join(keywords)}")

    if colors := card.get("colors"):
        if isinstance(colors, list) and colors:
            parts.append(f"Colors: {', '.join(colors)}")

    return ". ".join(parts)


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


def find_similar_cards(card_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Find cards most similar to the given card using cosine distance.

    Args:
        card_id: The id of the reference card.
        limit: Number of similar cards to return.

    Returns:
        List of dicts with name, type_line, oracle_text, and distance.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT c.name, c.type_line, c.oracle_text,
                   c.embedding <=> (SELECT embedding FROM cards WHERE id = %s) AS distance
            FROM cards c
            WHERE c.embedding IS NOT NULL
              AND c.id != %s
            ORDER BY distance
            LIMIT %s
            """,
            (card_id, card_id, limit),
        )
        rows = cur.fetchall()

    return [
        {
            "name": row[0],
            "type_line": row[1],
            "oracle_text": row[2],
            "distance": row[3],
        }
        for row in rows
    ]

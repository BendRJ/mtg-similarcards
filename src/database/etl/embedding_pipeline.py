"""Embedding pipeline for generating and storing card vector embeddings.

Runs as a separate step after the card ETL pipeline. Embeds every card that doesn't
have an embedding yet. Printings share their rules text, so each distinct text is
encoded once and its vector written to every card with that text.
"""

import argparse
import datetime
import logging
import time
from collections import defaultdict
from typing import Any, Callable

import psycopg
from psycopg.rows import dict_row

from app.config.logging_config import setup_logging
from database.db import get_db_connection
from utils.vector_helper import build_card_text

logger = logging.getLogger(__name__)

# Distinct texts per model call and per commit.
BATCH_SIZE = 256

CARDS_WITHOUT_EMBEDDING_SQL = """
    SELECT c.id, c.oracle_text, c.keywords, c.released_at
    FROM cards c
    WHERE c.embedding IS NULL
"""

# One statement per distinct text, covering all its printings.
WRITE_EMBEDDING_SQL = "UPDATE cards SET embedding = %s::vector WHERE id = ANY(%s)"

Encoder = Callable[[list[str]], list[list[float]]]


def embed_missing(cur: psycopg.Cursor[dict[str, Any]], encode: Encoder,
                  batch_size: int = BATCH_SIZE, after_batch: Callable[[], None] = lambda: None,
                  released_after: datetime.date | None = None) -> int:
    """Embed every card without an embedding, one model call per batch of distinct texts.

    Args:
        cur: A dict_row cursor.
        encode: Turns a list of texts into one vector each (the sentence-transformer).
        batch_size: Distinct texts per encode call.
        after_batch: Called after each batch is written, e.g. to commit, so an
            interrupted run keeps its progress and the next run picks up the rest.
        released_after: Only embed texts that have at least one printing released after
            this date. The vector then goes to all printings with that text, older ones
            included, so the card is comparable from any of its pages. None = all cards.

    Returns:
        Number of cards (printings) that got an embedding.
    """
    cur.execute(CARDS_WITHOUT_EMBEDDING_SQL)
    ids_by_text: dict[str, list[str]] = defaultdict(list)
    recent_texts: set[str] = set()
    for card in cur.fetchall():
        # Cards with neither rules text nor keywords have nothing to compare; they stay NULL.
        if text := build_card_text(card):
            ids_by_text[text].append(card["id"])
            released = card["released_at"]
            if released_after is None or (released is not None and released > released_after):
                recent_texts.add(text)

    texts = [text for text in ids_by_text if text in recent_texts]
    logger.info("Found %d distinct texts for %d cards without embeddings.",
                len(texts), sum(len(ids_by_text[text]) for text in texts))

    embedded = 0
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        vectors = encode(batch)
        cur.executemany(WRITE_EMBEDDING_SQL,
                        [(str(vector), ids_by_text[text]) for text, vector in zip(batch, vectors)])
        after_batch()
        embedded += sum(len(ids_by_text[text]) for text in batch)
        logger.info("Progress: %d / %d texts embedded.", start + len(batch), len(texts))
    return embedded


def run_embedding_pipeline(released_after: datetime.date | None = None) -> int:
    """Embed all cards that don't have one yet, against the configured database.

    Args:
        released_after: See embed_missing; None embeds cards from all years.

    Returns:
        Number of cards embedded.
    """
    setup_logging()
    logger.info("Starting embedding pipeline...")
    start_time = time.monotonic()

    # Imported here: loading sentence-transformers takes seconds and isn't needed to import this module.
    from app.services.vector_service import generate_embeddings

    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            embedded = embed_missing(cur, generate_embeddings, after_batch=conn.commit,
                                     released_after=released_after)

    elapsed = time.monotonic() - start_time
    minutes, seconds = divmod(elapsed, 60)
    logger.info(
        "Embedding pipeline complete. %d cards embedded in %dm %.1fs.",
        embedded, int(minutes), seconds,
    )
    return embedded


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed cards that don't have an embedding yet")
    parser.add_argument("--released-after", type=datetime.date.fromisoformat, default=None,
                        help="Only cards with a printing released after this date (YYYY-MM-DD)")
    run_embedding_pipeline(released_after=parser.parse_args().released_after)

"""Embedding pipeline for generating and storing card vector embeddings.

Runs as a separate step after the card ETL pipeline. Queries cards that
don't yet have embeddings, generates them in batches, and writes them back.
"""

import logging
import time

from app.config.logging_config import setup_logging
from app.services.vector_service import build_card_text, generate_embeddings
from database.db import get_cursor

logger = logging.getLogger(__name__)

BATCH_SIZE = 256

CARD_FIELDS_SQL = """
    SELECT id, name, type_line, mana_cost, oracle_text,
           keywords, colors, power, toughness
    FROM cards
    WHERE embedding IS NULL
    LIMIT 200
"""


def run_embedding_pipeline() -> int:
    """Generate embeddings for all cards that don't have one yet.

    Returns:
        Number of cards embedded.
    """
    setup_logging()
    logger.info("Starting embedding pipeline...")
    start_time = time.monotonic()

    # Fetch all cards without embeddings
    with get_cursor() as cur:
        cur.execute(CARD_FIELDS_SQL)
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    total = len(rows)
    if total == 0:
        logger.info("No cards without embeddings found. Nothing to do.")
        return 0

    logger.info("Found %d cards without embeddings.", total)
    embedded_count = 0

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        texts = [build_card_text(card) for card in batch]
        embeddings = generate_embeddings(texts)

        # Write embeddings back to the database
        with get_cursor() as cur:
            for card, embedding in zip(batch, embeddings):
                cur.execute(
                    "UPDATE cards SET embedding = %s WHERE id = %s",
                    (str(embedding), card["id"]),
                )

        embedded_count += len(batch)
        logger.info("Progress: %d / %d cards embedded.", embedded_count, total)

    elapsed = time.monotonic() - start_time
    minutes, seconds = divmod(elapsed, 60)
    logger.info(
        "Embedding pipeline complete. %d cards embedded in %dm %.1fs.",
        embedded_count, int(minutes), seconds,
    )
    return embedded_count


if __name__ == "__main__":
    run_embedding_pipeline()

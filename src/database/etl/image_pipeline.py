"""Image pipeline for downloading and storing card images as BYTEA.

Runs as a separate step after the card ETL pipeline. Queries cards that have
an image URL but no stored image yet, downloads each image, and writes the
bytes into the card_images table. Mirrors the structure of embedding_pipeline.py.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import LiteralString, cast

from app.config.logging_config import setup_logging
from database.db import get_cursor
from database.etl.session_manager import SessionManager

logger = logging.getLogger(__name__)

# Scryfall asks for 50-100 ms between requests (see cards_retrieval_svc.py).
REQUEST_DELAY_SECONDS = 0.1
# Which Scryfall image_uris variant to store for offline display.
IMAGE_SIZE = "normal"

SQL_FILE = Path(__file__).parents[1] / "sql" / "upsert" / "card_images_upsert.sql"
CARD_IMAGES_UPSERT_SQL = cast(LiteralString, SQL_FILE.read_text())

# Cards that have image URLs but no stored image yet. Same set scoping as the
# embedding pipeline so both operate on the same working set.
CARDS_WITHOUT_IMAGES_SQL = """
    SELECT c.id, c.image_uris
    FROM cards c
    LEFT JOIN card_images ci ON ci.card_id = c.id
    JOIN sets ON c.set_code = sets.code
    WHERE ci.card_id IS NULL
      AND c.image_uris IS NOT NULL
      AND sets.released_at >= '2025-01-01'
"""


@dataclass
class FetchedImage:
    """A downloaded card image ready to be stored."""
    content: bytes
    content_type: str | None
    source_url: str


def fetch_card_image(
    session: SessionManager,
    image_uris: dict[str, str],
) -> FetchedImage | None:
    """Download a card's image and return it, or None to skip this card.

    Args:
        session: shared SessionManager. Perform the request with
            ``session.session.get(url, timeout=session.timeout)``.
        image_uris: Scryfall image_uris dict, e.g.
            ``{"small": ..., "normal": ..., "large": ..., "png": ...}``.

    Returns:
        A FetchedImage with the raw bytes, or None if the image should be skipped.
    """
    # Prefer normal (lower quality, less storage size), fall back to png.
    source_url = image_uris.get("normal") or image_uris.get("png")
    if source_url is None:
        logger.warning("No png/normal image in image_uris. Skipping card.")
        return None

    try:
        resp = session.session.get(source_url, timeout=session.timeout)
    except Exception as error:
        logger.error("Couldn't download image from %s: %s", source_url, error)
        return None

    content_type = resp.headers.get("Content-Type", "")
    if not resp.ok or not content_type.startswith("image/"):
        logger.warning(
            "Bad image response (%s, %s) from %s. Skipping.",
            resp.status_code, content_type, source_url,
        )
        return None

    return FetchedImage(resp.content, content_type, source_url)


def run_image_pipeline() -> int:
    """Download and store images for all cards that don't have one yet.

    Returns:
        Number of images stored.
    """
    setup_logging()
    logger.info("Starting image pipeline...")
    start_time = time.monotonic()

    # Fetch all cards without a stored image.
    with get_cursor() as cur:
        cur.execute(CARDS_WITHOUT_IMAGES_SQL)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    total = len(rows)
    if total == 0:
        logger.info("No cards without images found. Nothing to do.")
        return 0

    logger.info("Found %d cards without images.", total)
    session = SessionManager()
    stored_count = 0
    failed: list[str] = []

    for idx, card in enumerate(rows, start=1):
        fetched = fetch_card_image(session, card["image_uris"])
        if fetched is None:
            failed.append(card["id"])
            continue

        with get_cursor() as cur:
            cur.execute(CARD_IMAGES_UPSERT_SQL, (
                card["id"],
                IMAGE_SIZE,
                fetched.content_type,
                fetched.source_url,
                len(fetched.content),
                fetched.content,  # bytes -> bytea (psycopg v3 adapts natively)
            ))

        stored_count += 1
        if idx % 20 == 0:
            logger.info("Progress: %d / %d images stored.", stored_count, total)

        time.sleep(REQUEST_DELAY_SECONDS)

    if failed:
        logger.warning("%d cards could not be fetched: %s", len(failed), failed)

    elapsed = time.monotonic() - start_time
    minutes, seconds = divmod(elapsed, 60)
    logger.info(
        "Image pipeline complete. %d images stored in %dm %.1fs.",
        stored_count, int(minutes), seconds,
    )
    return stored_count


if __name__ == "__main__":
    run_image_pipeline()

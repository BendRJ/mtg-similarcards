"""
Main module for mtg-similarcards application
"""
import logging
from typing import Optional

import psycopg

from app.config.logging_config import setup_logging
from database.db import get_cursor, test_connection
from database.etl.sets.sets_etl import run_sets_etl

logger = logging.getLogger(__name__)

def main(insert_sets: Optional[bool]):
    """
    Main entry point for the application
    """
    # Configure logging
    setup_logging()

    logger.info("Hello from mtg-similarcards!")
    logger.info("Testing database connection...")

    if test_connection():
        logger.info("✓ Database connection successful!")

        # sets table check and insert
        logger.info("Querying sets table...")
        try:
            with get_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sets")
                result = cur.fetchone()
                if result and insert_sets: #sets table gets created on app boot, so should always exist
                    logging.info("✓ Sets table exists! Full insert was chosen!")
                    _failed_inserts = run_sets_etl()
                elif result and result[0] > 0:
                    count = result[0]
                    logger.info(f"✓ Sets table exists with {count} records")
                else:
                    logger.warning("✓ Sets table exists but query returned no results")
                    logger.info("Inserting into sets table now...")
                    _failed_inserts = run_sets_etl()

        except psycopg.Error as e:
            logger.error(f"✗ Error querying sets table: {e}")
    else:
        logger.error("✗ Database connection failed!")
        logger.error("Make sure the database is running: docker compose up -d")


if __name__ == "__main__":
    main(insert_sets=None)

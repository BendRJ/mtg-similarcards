"""
Main module for mtg-similarcards application
"""
import logging
import psycopg
from src.database.db import test_connection, get_cursor
from src.app.config.logging_config import setup_logging

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the application
    """
    # Configure logging
    setup_logging()
    
    logger.info("Hello from mtg-similarcards!")
    logger.info("Testing database connection...")

    if test_connection():
        logger.info("✓ Database connection successful!")

        # Example: Query the sets table
        logger.info("Querying sets table...")
        try:
            with get_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sets")
                result = cur.fetchone()
                if result:
                    count = result[0]
                    logger.info(f"✓ Sets table exists with {count} records")
                else:
                    logger.warning("✓ Sets table exists but query returned no results")
        except psycopg.Error as e:
            logger.error(f"✗ Error querying sets table: {e}")
    else:
        logger.error("✗ Database connection failed!")
        logger.error("Make sure the database is running: docker compose up -d")


if __name__ == "__main__":
    main()

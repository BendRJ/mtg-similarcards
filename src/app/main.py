"""
Main module for mtg-similarcards application
"""
import logging

from app.config.logging_config import setup_logging
from database.db import test_connection
from database.etl.pipeline import DataPipeline

logger = logging.getLogger(__name__)

def main(set_codes: list[str] | None = None, run_pipeline_on_start: bool = True):
    """
    Main entry point for the application
    """
    # Configure logging
    setup_logging()

    logger.info("Hello from mtg-similarcards!")
    logger.info("Testing database connection...")

    if test_connection() and run_pipeline_on_start:
        logger.info("✓ Database connection successful!")

        # sets table check and insert
        logger.info("Starting DataPipeline...")
        pipeline = DataPipeline()
        pipeline.run(set_codes=set_codes)

    else:
        logger.error("✗ Database connection failed!")
        logger.error("Make sure the database is running: docker compose up -d")


if __name__ == "__main__":
    main()

"""
Main module for mtg-similarcards application
"""
import argparse
import logging

from app.config.logging_config import setup_logging
from app.backend.backend import app
from database.db import test_connection
from database.etl.pipeline import DataPipeline
import uvicorn

logger = logging.getLogger(__name__)

def main(set_codes: list[str] | None = None, run_pipeline_on_start: bool = False, force: bool = False, release_year: int | None = None):
    """
    Main entry point for the application
    """
    # Configure logging
    setup_logging()

    logger.info("Hello from mtg-similarcards!")
    logger.info("Testing database connection...")

    if test_connection():
        logger.info("✓ Database connection successful!")
        if run_pipeline_on_start:
        # sets table check and insert
            logger.info("Starting DataPipeline...")
            pipeline = DataPipeline()
            pipeline.run(set_codes=set_codes, force=force, release_year=release_year)

    else:
        logger.error("✗ Database connection failed!")
        logger.error("Make sure the database is running: docker compose up -d")

    logger.info("Booting up backend-for-frontend.")
    uvicorn.run(app)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MTG Similar Cards pipeline")
    parser.add_argument("--sets", nargs="*", help="Set codes to process (e.g. MH3 DMU BLB)")
    parser.add_argument("--run-pipeline", action="store_true", help="Run pipeline execution")
    parser.add_argument("--force", action="store_true", help="Force piepline run")
    parser.add_argument("--release-year", type=int)
    args = parser.parse_args()

    main(
        set_codes=args.sets or None,
        run_pipeline_on_start=args.run_pipeline,
        force=args.force,
        release_year=args.release_year,
    )

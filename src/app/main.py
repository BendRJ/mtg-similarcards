"""
Main module for mtg-similarcards application
"""
import argparse
import logging
import os

from app.config.logging_config import setup_logging
from app.backend.backend import app
from database.db import test_connection
from database.etl.pipeline import DataPipeline
import uvicorn

logger = logging.getLogger(__name__)


# Compose passes unset variables as empty strings (SETS: ${SETS:-}), so "" means "not set".
TRUTHY = {"1", "true", "yes", "on"}


def env_sets(name: str) -> list[str] | None:
    """Read a space-separated list of set codes, e.g. "MH3 DMU" -> ["MH3", "DMU"]."""
    # Bare split() collapses whitespace runs and drops empty fields, so "" yields [].
    # None rather than [] signals "discover all sets" to DataPipeline.run().
    return os.getenv(name, "").split() or None


def env_flag(name: str) -> bool:
    """Read a boolean switch. Unrecognised values (including "0") are False."""
    return os.getenv(name, "").strip().lower() in TRUTHY


def env_int(name: str) -> int | None:
    """Read an optional integer; malformed input must not crash startup."""
    # int() rejects "" and garbage with the same ValueError, so one handler covers both.
    try:
        return int(os.getenv(name, ""))
    except ValueError:
        return None


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
    # Default to loopback so a local `make run-main` is not exposed on the network.
    # Compose sets API_HOST=0.0.0.0 so the container accepts traffic from the bridge.
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MTG Similar Cards pipeline")
    # Defaults come from the environment so `docker-compose up` can configure the run;
    # an explicit CLI flag still wins for local `uv run` / `make run-main` invocations.
    parser.add_argument("--sets", nargs="*", default=env_sets("SETS"),
                        help="Set codes to process (e.g. MH3 DMU BLB)")
    parser.add_argument("--run-pipeline", action="store_true", default=env_flag("RUN_PIPELINE"),
                        help="Run pipeline execution")
    parser.add_argument("--force", action="store_true", default=env_flag("FORCE"),
                        help="Force piepline run")
    parser.add_argument("--release-year", type=int, default=env_int("RELEASE_YEAR"))
    args = parser.parse_args()

    main(
        set_codes=args.sets or None,
        run_pipeline_on_start=args.run_pipeline,
        force=args.force,
        release_year=args.release_year,
    )

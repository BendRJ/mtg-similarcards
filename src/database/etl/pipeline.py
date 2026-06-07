"""Data pipeline module to orchestrate the ETL process for all data sources."""

import logging
import time
from dataclasses import dataclass, field

import psycopg
import requests

from app.config.logging_config import setup_logging
from database.etl.cards.cards_etl import run_cards_etl
from database.etl.sets.sets_etl import run_sets_etl
from src.utils.etl_helper import _set_has_cards

logger = logging.getLogger(__name__)


@dataclass # decorator to automatically generate init, repr, etc. for the PipelineResult class
class PipelineResult:
    """Summary of a pipeline run."""
    failed_sets: list[dict] = field(default_factory=list)
    failed_cards: dict[str, list[dict]] = field(default_factory=dict)
    processed_cards: dict[str, list[dict]] = field(default_factory=dict)
    skipped_sets: list[str] = field(default_factory=list)
    errored_sets: list[str] = field(default_factory=list)
    sets_processed: int = 0


class DataPipeline:
    """Data pipeline class to orchestrate the ETL process for all data sources."""

    def run(
        self,
        set_codes: list[str] | None = None,
        force: bool = False,
        release_year: int | None = None,
    ) -> PipelineResult:
        """Run the ETL process for all data sources.

        Args:
            set_codes: Optional list of specific set codes to process.
                       If None, runs sets ETL first, then cards ETL for all sets.
                       If provided, skips sets ETL and runs cards ETL for given codes only.
            force: When True, reload cards even if the set already exists in the cards table.
        """
        result = PipelineResult() #intantiate result object to track pipeline outcomes

        # Step 1: Sets ETL (unless specific set_codes were provided)
        if set_codes is None:
            logger.info("Running sets ETL...")
            sets_result = run_sets_etl(release_year)
            result.failed_sets = sets_result.failed_sets
            set_codes = sets_result.processed_set_codes
            logger.info(
                "Sets ETL complete. %d sets total, %d failed validation.",
                len(set_codes), len(result.failed_sets),
            )

        # Step 2: Cards ETL for each set
        logger.info("Running cards ETL for %d sets...", len(set_codes))
        start_time = time.monotonic()
        for code in set_codes:
            if not force and _set_has_cards(code):
                logger.info("Skipping set '%s' — cards already loaded.", code)
                result.skipped_sets.append(code)
                continue

            try:
                cards_result = run_cards_etl(code)
            except (requests.RequestException, psycopg.Error, ValueError):
                logger.exception("Cards ETL failed for set '%s'", code)
                result.errored_sets.append(code)
                continue

            if cards_result is None:
                logger.warning("No search_uri for set '%s' — skipping.", code)
                result.skipped_sets.append(code)
                continue

            if cards_result.failed_cards:
                result.failed_cards[code] = cards_result.failed_cards
            if cards_result.processed_cards:
                result.processed_cards[code] = cards_result.processed_cards

            result.sets_processed += 1

        total_processed_cards = sum(len(cards) for cards in result.processed_cards.values())
        total_failed_cards = sum(len(cards) for cards in result.failed_cards.values())
        logger.info(
            "Pipeline complete. Sets processed: %d, "
            "Cards processed: %d, "
            "Cards failed validation: %d (across %d sets), "
            "Sets skipped: %d, "
            "Sets errored: %d",
            result.sets_processed,
            total_processed_cards,
            total_failed_cards,
            len(result.failed_cards),
            len(result.skipped_sets),
            len(result.errored_sets),
        )
        if result.errored_sets:
            logger.error("Errored sets: %s", result.errored_sets)

        elapsed = time.monotonic() - start_time
        minutes, seconds = divmod(elapsed, 60)
        logger.info("Total time processed: %dm %.1fs", int(minutes), seconds)

        return result


if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run()

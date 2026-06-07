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

setup_logging(log_level=logging.INFO)


@dataclass # decorator to automatically generate init, repr, etc. for the PipelineResult class
class PipelineResult:
    """Summary of a pipeline run."""
    failed_sets: list[dict] = field(default_factory=list)
    failed_cards: dict[str, list[dict]] = field(default_factory=dict)
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
            logging.info("Running sets ETL...")
            sets_result = run_sets_etl(release_year)
            result.failed_sets = sets_result.failed_sets
            set_codes = sets_result.all_set_codes
            logging.info(
                "Sets ETL complete. %d sets total, %d failed validation.",
                len(set_codes), len(result.failed_sets),
            )

        # Step 2: Cards ETL for each set
        logging.info("Running cards ETL for %d sets...", len(set_codes))
        start_time = time.monotonic()
        for code in set_codes:
            if not force and _set_has_cards(code):
                logging.info("Skipping set '%s' — cards already loaded.", code)
                result.skipped_sets.append(code)
                continue

            try:
                failed_cards = run_cards_etl(code)
            except (requests.RequestException, psycopg.Error, ValueError):
                logging.exception("Cards ETL failed for set '%s'", code)
                result.errored_sets.append(code)
                continue

            if failed_cards is None:
                logging.warning("No search_uri for set '%s' — skipping.", code)
                result.skipped_sets.append(code)
            elif failed_cards:
                result.failed_cards[code] = failed_cards

            result.sets_processed += 1

        logging.info(
            "Pipeline complete. Sets processed: %d, "
            "Sets with card validation failures: %d, "
            "Sets skipped: %d, "
            "Sets errored: %d",
            result.sets_processed,
            len(result.failed_cards),
            len(result.skipped_sets),
            len(result.errored_sets),
        )
        if result.errored_sets:
            logging.error("Errored sets: %s", result.errored_sets)

        elapsed = time.monotonic() - start_time
        minutes, seconds = divmod(elapsed, 60)
        logging.info("Total time processed: %dm %.1fs", int(minutes), seconds)

        return result


if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run()

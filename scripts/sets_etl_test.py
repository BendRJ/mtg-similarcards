"""Quick smoke test for Scryfall sets and cards retrieval services."""

import logging

from app.config.logging_config import setup_logging
from database.etl.schema_validation import SetsValidation
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService

setup_logging(log_level=logging.DEBUG)

sets_svc = SetsRetrievalService()

# test get_sets (all sets)
sets = sets_svc.get_sets()

# test get_set (single set)
df = sets_svc.get_set("tdm")
logging.info(f"Single set: {df['name']} ({df['code']})")
logging.info(f"  set_type: {df['set_type']}")
logging.info(f"  released_at: {df['released_at']}")
logging.info(f"  digital: {df['digital']}")

try:
    loaded_df = SetsValidation.model_validate(df) #only validates
    cleaned_df = loaded_df.model_dump() #model_config with extra="ignore" will drop any fields not defined in the model here!
    logging.info(f"After pydantic validation: {cleaned_df}")
except Exception as e:
    logging.error(f"Validation failed: {e}")

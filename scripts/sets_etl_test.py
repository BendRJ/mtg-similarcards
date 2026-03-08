"""Quick smoke test for Scryfall sets and cards retrieval services."""

import logging

from app.config.logging_config import setup_logging
from database.etl.schema_validation import SetsValidation
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService
from pydantic import ValidationError

setup_logging(log_level=logging.DEBUG)

sets_svc = SetsRetrievalService()


# test get_set (single set)
df = sets_svc.get_set("tdm")
logging.info(f"Single set: {df['name']} ({df['code']})")
logging.info(f"  set_type: {df['set_type']}")
logging.info(f"  released_at: {df['released_at']}")

try:
    df["extra_field"] = "this field is not defined in the pydantic model and should be ignored"
    #df["code"] = 123 # this should cause a validation error as code is defined as str in the pydantic model
    loaded_dict = SetsValidation.model_validate(df) #only validates
    cleaned_dict = loaded_dict.model_dump() #model_config with extra="ignore" will drop any fields not defined in the model here!
    logging.info(f"After pydantic validation: {cleaned_dict.keys()}")
except ValidationError as e:
    logging.error(f"Validation failed: {e}")


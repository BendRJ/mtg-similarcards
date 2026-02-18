import logging
from app.config.logging_config import setup_logging
from database.etl.sets.sets_retrieval_svc import SetsRetrievalService

setup_logging(log_level=logging.DEBUG)

svc = SetsRetrievalService()

# test get_sets
sets = svc.get_sets()
print(f"Got {len(sets)} sets")
print(f"First set: {sets[0]['name']}")
print(f"Full payload: {sets[0]}")

# test get_set
ktk = svc.get_set("KTK")
print(f"Single set: {ktk['name']}")
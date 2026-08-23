# Documentation Index

A Python application for finding similar Magic: The Gathering cards. This page is the
entry point to the project's documentation and an annotated map of the repository.

## Documentation

| Doc | What it covers |
|---|---|
| [Database runbook](./runbooks/database.md) | DB lifecycle, reset, shell access, backup/restore, schema management. |
| [Run pipeline runbook](./runbooks/run-pipeline.md) | Running the ETL pipeline, CLI flags, `make` targets, verification. |
| [Database schemas README](../src/database/schemas/README.md) | JSON schema definitions used for validation. |
| [Training README](../src/training/README.md) | Fine-tuning the embedding model on MTG data. |
| [Project README](../README.md) | Setup, prerequisites, quick start. |

## Repository structure

```
mtg-similarcards/
├── src/
│   ├── app/
│   │   ├── main.py                     # CLI entry point + argparse (pipeline launcher)
│   │   ├── config/
│   │   │   ├── api_endpoints.py        # External API endpoint configuration (Scryfall)
│   │   │   └── logging_config.py       # Logger setup
│   │   └── services/
│   │       └── vector_service.py       # Vector similarity / embedding query logic
│   ├── database/
│   │   ├── db.py                       # PostgreSQL connection helpers (psycopg 3)
│   │   ├── etl/
│   │   │   ├── pipeline.py             # DataPipeline.run — ETL orchestration
│   │   │   ├── embedding_pipeline.py   # Card text → embeddings pipeline
│   │   │   ├── schema_validation.py    # JSON schema validation of API payloads
│   │   │   ├── session_manager.py      # HTTP session / retry handling
│   │   │   ├── cards/
│   │   │   │   ├── cards_etl.py         # Cards ETL load
│   │   │   │   └── cards_retrieval_svc.py  # Card data retrieval service
│   │   │   └── sets/
│   │   │       ├── sets_etl.py          # Sets ETL load (release-year filter)
│   │   │       └── sets_retrieval_svc.py   # Set data retrieval service
│   │   ├── schemas/                    # JSON schema definitions (cards_*, sets)
│   │   └── sql/
│   │       ├── create_tables/          # Table DDL, numerically ordered by FK dependency
│   │       ├── queries/                # similar_cards.sql and other read queries
│   │       └── upsert/                 # cards_upsert.sql, sets_upsert.sql
│   ├── training/
│   │   └── generate_training_data.py   # Build fine-tuning training pairs
│   └── utils/
│       └── etl_helper.py               # Shared ETL helper functions
├── analytics/
│   └── sets.sql                        # Ad-hoc analytics query
├── scripts/                            # Standalone test/preview scripts
├── tests/                              # pytest suite
├── docs/
│   ├── index.md                        # This file
│   └── runbooks/                       # Operational runbooks (database, run-pipeline)
├── Dockerfile                          # Application container image
├── docker-compose.yml                  # PostgreSQL container configuration
├── Makefile                            # db-up, run-main, test-connection, etc.
├── pyproject.toml                      # Project metadata and dependencies (uv)
└── .pylintrc                           # Lint configuration
```

## Key entry points

- **Start here:** `src/app/main.py` — CLI entry point and argument parser.
- **Pipeline orchestration:** `src/database/etl/pipeline.py` — `DataPipeline.run`.
- **Database access:** `src/database/db.py` — connection helpers (`get_cursor`, `get_db_connection`, `test_connection`).
- **Similarity query:** `src/database/sql/queries/similar_cards.sql` + `src/app/services/vector_service.py`.

## Related

- [Project README](../README.md) — setup and quick start.
- [Database runbook](./runbooks/database.md) — DB lifecycle and shell access.
- [Run pipeline runbook](./runbooks/run-pipeline.md) — running the ETL.

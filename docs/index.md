# Documentation Index

A Python application for finding similar Magic: The Gathering cards. This page is the
entry point to the project's documentation and an annotated map of the repository.

## Documentation

| Doc | What it covers |
|---|---|
| [Database runbook](./runbooks/database.md) | DB lifecycle, reset, shell access, backup/restore, schema management. |
| [BFF API design](./superpowers/specs/2026-10-31-bff-api-design.md) | Endpoints, response shapes and rules of the backend-for-frontend API. |
| [Frontend design](./superpowers/specs/2026-10-31-frontend-design.md) | The five screens, search behaviour, Docker/nginx setup ([mockups](./superpowers/specs/2026-10-31-frontend-mockups.html)). |
| [Advanced search design](./superpowers/specs/2026-11-01-advanced-search-design.md) | `POST /cards/search` and the `/search` filter-builder page: fields, operators, URL format, rules for cards without rules text ([mockup](./superpowers/specs/2026-11-01-advanced-search-mockup.html)). |
| [Open follow-ups](./api-database-wiring.md) | Known gaps and deferred work: embeddings, vector index, pooling, credentials, API and frontend rough edges. |
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
│   │   ├── backend/
│   │   │   ├── backend.py              # FastAPI app: create_app, CORS, DB-error → 503
│   │   │   ├── db.py                   # get_db_cursor — request-scoped dict_row cursor
│   │   │   ├── models.py               # Pydantic response models (the public API contract)
│   │   │   ├── queries.py              # All read SQL behind the routes
│   │   │   └── routers/                # cards.py (/cards/...), sets.py (/sets/...)
│   │   ├── config/
│   │   │   ├── api_endpoints.py        # External API endpoint configuration (Scryfall)
│   │   │   └── logging_config.py       # Logger setup
│   │   └── services/
│   │       └── vector_service.py       # Sentence-transformer model + embedding generation
│   ├── database/
│   │   ├── db.py                       # PostgreSQL connection helpers (psycopg 3)
│   │   ├── etl/
│   │   │   ├── pipeline.py             # DataPipeline.run — ETL orchestration
│   │   │   ├── embedding_pipeline.py   # Card text → embeddings pipeline
│   │   │   ├── image_pipeline.py       # Downloads card images into card_images
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
│   │       └── upsert/                 # cards_upsert.sql, sets_upsert.sql
│   ├── training/
│   │   └── generate_training_data.py   # Build fine-tuning training pairs
│   └── utils/
│       └── etl_helper.py               # Shared ETL helper functions
├── frontend/                           # React + Vite + TypeScript web UI
│   ├── src/
│   │   ├── App.tsx                     # Route table: /, /search, /card/:id, /set/:code, /color/:c
│   │   ├── api.ts, types.ts            # Typed API client (relative /cards, /sets URLs, POST /cards/search) + response types
│   │   ├── lib/                        # colors, set matching, searchFilters (filter model + URL format), useAsync (stale-safe data hook)
│   │   ├── components/                 # Layout, SearchBar, CardGrid/CardTile, FilterRow, ErrorState, Loading
│   │   ├── pages/                      # HomePage, AdvancedSearchPage, ColorPage, CardPage, SetPage, NotFoundPage
│   │   └── styles.css                  # Design tokens (light/dark) and layout
│   ├── vite.config.ts                  # Dev proxy for /cards and /sets → :8000, Vitest config
│   ├── Dockerfile                      # node build stage → nginx runtime stage
│   └── nginx.conf.template             # Serves the SPA, proxies /cards and /sets to the app container
├── analytics/
│   └── sets.sql                        # Ad-hoc analytics query
├── scripts/                            # Standalone test/preview scripts
├── tests/                              # unittest suite (make run-all-tests); DB tests skip without Postgres
├── docs/
│   ├── index.md                        # This file
│   ├── api-database-wiring.md          # Open follow-ups (known gaps, deferred work)
│   ├── superpowers/                    # Design specs and implementation plans
│   └── runbooks/                       # Operational runbooks (database, run-pipeline)
├── Dockerfile                          # Application container image
├── docker-compose.yml                  # App, frontend and PostgreSQL containers (ports on 127.0.0.1)
├── Makefile                            # db-up, dev, run-main, docker-run, frontend-dev, frontend-test, etc.
├── pyproject.toml                      # Project metadata and dependencies (uv)
└── .pylintrc                           # Lint configuration
```

## Key entry points

- **Start here:** `src/app/main.py` — CLI entry point and argument parser.
- **API:** `src/app/backend/backend.py` — the FastAPI app; `make dev` serves it with hot-reload, `/docs` lists every route.
- **Frontend:** `frontend/` — `make frontend-dev` serves it with hot-reload on :5173; `make docker-run` serves it via nginx on :8080 (proxies `/cards` and `/sets` to the API).
- **Advanced search:** `POST /cards/search` (`src/app/backend/routers/cards.py`) and the `/search` page (`frontend/src/pages/AdvancedSearchPage.tsx`); filters are AND-combined and live in the URL (`?f=field.operator.value`).
- **Pipeline orchestration:** `src/database/etl/pipeline.py` — `DataPipeline.run`.
- **Database access:** `src/database/db.py` — connection helpers (`get_cursor`, `get_db_connection`, `test_connection`).
- **Similarity query:** `similar_cards()` in `src/app/backend/queries.py` (optionally narrowed by the advanced-search filters).
- **Embeddings:** `src/database/etl/embedding_pipeline.py` + `src/app/services/vector_service.py`.

## Related

- [Project README](../README.md) — setup and quick start.
- [Database runbook](./runbooks/database.md) — DB lifecycle and shell access.
- [Run pipeline runbook](./runbooks/run-pipeline.md) — running the ETL.

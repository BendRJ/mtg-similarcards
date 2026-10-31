# MTG Similar Cards

A card discovery app for Magic: The Gathering players. Search a card, see its printings and
cards similar to it (vector similarity over rules text), browse a set by color, or pull 100 random
cards of a color.

- **Backend:** Python 3.13, FastAPI backend-for-frontend over PostgreSQL 16 + `pgvector`
  (psycopg 3), fed by an ETL pipeline from the Scryfall API.
- **Frontend:** React + Vite + TypeScript in `frontend/`, served by nginx in Docker.

## Prerequisites

- Python 3.13+ and [uv](https://github.com/astral-sh/uv)
- Node.js 26 and npm (frontend development only)
- Docker with Docker Compose

## Quick start (Docker)

```bash
make db-up                               # postgres only
make run-main SETS="FIN"                 # load some card data (see the run-pipeline runbook)
make run-embeddings                      # embeddings for similar cards (sets released 2025+ only, for now)
make docker-run                          # API on :8000 + frontend on :8080 (Ctrl-C to stop)
```

Open <http://127.0.0.1:8080>. All ports are published on `127.0.0.1` only: frontend 8080,
API 8000, postgres 5432.

## Local development

```bash
uv sync                                  # Python dependencies
make frontend-install                    # frontend dependencies (npm ci)

make db-up                               # postgres in Docker
make dev                                 # API with hot-reload on :8000 (/docs lists every route)
make frontend-dev                        # frontend with hot-reload on :5173, proxies /cards and /sets to :8000
```

Frontend routes are singular (`/card/:id`, `/set/:code`, `/color/:c`); API paths are plural
(`/cards…`, `/sets…`). Only the API prefixes are proxied, in Vite and in nginx.

## Tests

```bash
make run-all-tests                       # backend unittest suite; DB tests skip without Postgres
make frontend-test                       # frontend unit tests (Vitest)
npm --prefix frontend run typecheck
```

CI (`.github/workflows/tests.yml`) runs the backend suite and a frontend job (typecheck, tests, build).

## Configuration

The Python code reads `DATABASE_URL`. Compose injects it inside the containers; on the host,
`.env` (not tracked) or the fallback in `src/database/db.py` applies. Database user, name and
password come from `docker-compose.yml` / `.env` — don't put real values in docs or commits.
The open issue around the hardcoded fallback is tracked in
[docs/api-database-wiring.md](docs/api-database-wiring.md).

## Documentation

Start at **[docs/index.md](docs/index.md)**. It maps the repository and links:

- [Database runbook](docs/runbooks/database.md): DB lifecycle, reset, shell access, backups.
- [Run pipeline runbook](docs/runbooks/run-pipeline.md): loading card data, `make` targets, Docker.
- [BFF API design](docs/superpowers/specs/2026-10-31-bff-api-design.md) and
  [frontend design](docs/superpowers/specs/2026-10-31-frontend-design.md).
- [Open follow-ups](docs/api-database-wiring.md): known gaps and deferred work.

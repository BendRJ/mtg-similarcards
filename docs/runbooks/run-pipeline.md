# Run Pipeline Runbook

## Overview

The MTG data pipeline is launched from `src/app/main.py`. It connects to PostgreSQL, then optionally runs the ETL via `DataPipeline.run(...)`. You can launch it two ways:

- **`uv run`** — direct, accepts any CLI flag.
- **`make`** — wraps `uv run` with `PYTHONPATH` set; convenient for the default flow.

Prerequisite for both: the database must be up.

```bash
make db-up
```

## CLI Flags (from `src/app/main.py`)

| Flag | Type | Purpose |
|---|---|---|
| `--sets MH3 DMU BLB` | list[str] | Process only these set codes; skips the sets ETL step. |
| `--run-pipeline` | flag | Run the ETL. Omitted, the app only tests the DB connection and serves the API. |
| `--force` | flag | Force pipeline rerun (ignore freshness checks). |
| `--release-year 2024` | int | Filter sets to a single release year during sets ETL. |

## Option 1: Run with `uv` (recommended for custom args)

`uv run` activates the project venv and runs the command. `PYTHONPATH` must include the repo root so `from app.config…` and `from database.…` resolve.

```bash
# From the repo root
PYTHONPATH=$(pwd) uv run python src/app/main.py --release-year 2024

# Combine flags
PYTHONPATH=$(pwd) uv run python src/app/main.py --release-year 2024 --force

# Specific sets only (release-year is ignored when --sets is provided —
# the sets ETL step is skipped entirely in that case)
PYTHONPATH=$(pwd) uv run python src/app/main.py --sets MH3 DMU

# DB connection check + API only, no ETL (omit --run-pipeline)
PYTHONPATH=$(pwd) uv run python src/app/main.py
```

Expected log evidence of a successful year filter:
```
INFO ✓ Database connection successful!
INFO Starting DataPipeline...
INFO Running sets ETL...
INFO Processing set: Bloomburrow (BLB)
INFO Set skipped due to release year of set being before or after 2024.
INFO Processing set: Modern Horizons 3 (MH3)
INFO Raw API response for set: 24 fields
...
```

## Option 2: Run with `make`

`run-main` forwards optional variables to the underlying `uv run` call using GNU Make's `$(if …)` conditional. Unset variables emit nothing; set variables become flags.

```bash
# Default — no filters, runs full pipeline
make run-main

# Filter by release year
make run-main RELEASE_YEAR=2024

# Force a rerun limited to specific sets
make run-main SETS="MH3 DMU" FORCE=1

# Combine all three
make run-main RELEASE_YEAR=2024 SETS="MH3 DMU" FORCE=1
```

Supported variables (see `Makefile` → `run-main` target):

| Make var | Forwarded as | Notes |
|---|---|---|
| `SETS` | `--sets MH3 DMU` | Skips sets ETL; `RELEASE_YEAR` has no effect when `SETS` is set. |
| `FORCE` | `--force` | Any non-empty value (e.g. `FORCE=1`) triggers the flag. |
| `RELEASE_YEAR` | `--release-year 2024` | Must be a 4-digit integer (enforced by argparse `type=int`). |

## Option 3: Run in Docker with `make docker-run`

`make docker-run` serves the FastAPI backend on <http://127.0.0.1:8000> and runs in the **foreground** —
stop it with Ctrl-C. It optionally runs the ETL first, before the API starts accepting requests.

```bash
# Serve the API only
make docker-run

# Run the pipeline for two sets first, then serve
make docker-run PIPE=1 SETS="MH3 DMU"
```

Because `docker-compose up` cannot append positional CLI args the way `docker-compose run` could,
configuration travels as **environment variables** instead. `src/app/main.py` reads them as argparse
*defaults*, so an explicit CLI flag still wins for the `uv run` and `make run-main` paths above.

| Env var | CLI equivalent | Notes |
|---|---|---|
| `SETS` | `--sets MH3 DMU` | Space-separated in one string. Empty means "discover all sets". |
| `RUN_PIPELINE` | `--run-pipeline` | Truthy values: `1`, `true`, `yes`, `on`. Anything else (incl. `0`) is off. Set via `PIPE=1` on the make target. |
| `FORCE` | `--force` | Same truthy rules as `RUN_PIPELINE`. |
| `RELEASE_YEAR` | `--release-year 2024` | Malformed values are ignored rather than fatal. |
| `API_HOST` | — | Uvicorn bind address. Defaults to `127.0.0.1`; compose sets `0.0.0.0`. |
| `API_PORT` | — | Port uvicorn listens on *inside* the container, default `8000`. Also sets the container side of the port mapping, so the two cannot disagree. |
| `HOST_PORT` | — | Port published on your machine, default `8000`. Only moves the host side — e.g. `HOST_PORT=9000` gives `9000->8000`. |

Both are settable on the make target: `make docker-run HOST_PORT=7000 API_PORT=9000` publishes `7000->9000`
with uvicorn bound to `0.0.0.0:9000`.

`API_HOST` defaults to loopback so a local `make run-main` is not exposed on your network. Inside a
container that default would make the API unreachable, which is why `docker-compose.yml` overrides it
to `0.0.0.0`.

## Verification

Confirm the API is reachable (in a second terminal, while `make docker-run` is up):

```bash
curl -s http://127.0.0.1:8000        # {"hello":"World!"}
curl -s http://127.0.0.1:8000/cards
docker ps --format '{{.Names}}\t{{.Ports}}' | grep app   # 0.0.0.0:8000->8000/tcp
```

The startup banner must read `Uvicorn running on http://0.0.0.0:8000`. If it says `127.0.0.1`, the
container is binding its own loopback and nothing on the host can reach it.

After a run with `--release-year 2024`, confirm only 2024 sets landed in the DB:

```bash
make db-shell
```
```sql
SELECT code, name, released_at
FROM sets
WHERE EXTRACT(YEAR FROM released_at) = 2024
ORDER BY released_at DESC;
```

To compare against what was skipped, drop the `WHERE` clause and check the log output for `Set skipped due to release year…` lines.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'app'`** — `PYTHONPATH` not set. Use `make run-main` or prefix manually: `PYTHONPATH=$(pwd) uv run …`.
- **`argparse.ArgumentTypeError: invalid int value: 'abc'`** — `--release-year` is typed `int`; pass a 4-digit year.
- **No sets processed at all** — check that the year you passed matches `released_at` years actually returned by the Scryfall sets endpoint (some sets release months ahead of their "official" year).
- **DB connection failed** — run `make db-up` and then `make test-connection`.

## Related

- [Database runbook](./database.md) — DB lifecycle, reset, and shell access.
- `src/app/main.py` — CLI entry point and arg parser.
- `src/database/etl/pipeline.py` — `DataPipeline.run` orchestration.
- `src/database/etl/sets/sets_etl.py` — year filter is applied here.

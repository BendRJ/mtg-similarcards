# Open follow-ups: API and frontend

The API reads from Postgres and the React frontend runs on top of it. This doc started on 2026-08-25
as a plan for replacing the hardcoded card fixture; that work landed in PR #23 (see the
[BFF API design](./superpowers/specs/2026-10-31-bff-api-design.md)), and the frontend followed (see the
[frontend design](./superpowers/specs/2026-10-31-frontend-design.md)). What is left here is the
connectivity reference and the items that are still open. Updated 2026-10-31; check it still
matches the code before acting on it.

## Where things stand

- Routes live in `src/app/backend/routers/`, all SQL in `src/app/backend/queries.py` plus
  `src/database/sql/queries/similar_cards.sql`, response models in `src/app/backend/models.py`.
- Each request gets one connection via `get_db_cursor()` (`src/app/backend/db.py`), a `dict_row`
  cursor over `database.db.get_db_connection()`.
- psycopg errors map to **503** with a generic message; details are logged server-side only.
- `image_url` is the stored image (`/cards/{id}/image`) if there is one, else Scryfall's `normal`
  link from `image_uris`. The card detail also returns `image_url_large` (Scryfall's `large` link),
  which the card page uses.
- `GET /cards/random?colors=&limit=` (max 100) backs the frontend's color pages; it shares the
  any-of color rule (`COLOR_FILTER`) with `/sets/{code}/cards`.
- Route tests use a fake cursor; SQL tests run against real Postgres in a rolled-back
  `bff_test` schema and skip when no DB is reachable (CI has none).

## Connectivity

`get_database_url()` (`src/database/db.py`) falls back to a localhost DSN, and
`docker-compose.yml` publishes postgres on `127.0.0.1:5432`. So:

```
make db-up     # postgres only
make dev       # host FastAPI, hot-reload, reaches the DB on localhost
```

**Why `.env` and Compose don't fight each other:** `db.py` calls `load_dotenv()`, which by default
does **not** override variables already present in the environment. Inside the container, Compose has
already injected `DATABASE_URL` with the `postgres` bridge hostname, so it wins. On the host, `.env`
(or the localhost fallback) applies. Keep any `DATABASE_URL` in `.env` pointed at `localhost` — the
`postgres` hostname only resolves inside the Compose network.

## Open items

### 1. Embeddings only cover sets from 2025 on

`src/database/etl/embedding_pipeline.py` selects cards with
`sets.released_at >= '2025-01-01'`. Cards from older sets have no embedding, so
`/cards/{id}/similar` returns 404 for them and never suggests them. Removing the filter means one
long embedding run over every loaded card (~117k today).

### 2. No index on `embedding`

Every similarity query is a sequential scan computing exact distance over all embedded rows
(~120–170 ms at 12k embedded cards). The fix is an `hnsw` or `ivfflat` index on
`embedding vector_cosine_ops`, but `src/database/sql/migrations/` is **empty and there is no
migration tooling**, so it has to be applied by hand per the database runbook, and re-applied on
any volume reset. Becomes pressing together with item 1.

### 3. One connection per request

`get_connection()` calls `psycopg.connect()` per request: a fresh TCP connection and auth
handshake every time. Fine for local dev, wrong under any real concurrency. The fix is a pool via
`psycopg_pool` — **a separate package that is not currently a dependency**, so adding it needs a
deliberate decision (name + version stated, then added to `pyproject.toml` and `uv.lock`).

Keep the route handlers **`def`, not `async def`**: psycopg here is the synchronous driver, and
FastAPI runs sync handlers in a threadpool.

### 4. Hardcoded fallback credentials, no `.env.example`

`get_database_url()` falls back to a DSN with **credentials hardcoded in tracked source**, so a
misconfigured deployment silently connects to a default-credentialed localhost DB instead of
failing loudly. Make the fallback raise on missing config, and commit a `.env.example` (variable
names and placeholders only, never real values). `DATABASE_URL` — the only DB variable the Python
code reads — is currently documented nowhere outside `docker-compose.yml`. If those default
credentials are used anywhere real, rotate them.

### 5. Faces of multi-part cards are not stored

Scryfall keeps rules text, colors and images of transform, modal double-faced, adventure and split
cards on their faces, and the ETL stores only the top-level card. So ~980 real cards have NULL
`oracle_text`, and double-faced cards also lack `colors` and image links (the same cause behind
missing colors/images on those cards). In advanced search, "Rules text contains X" falls back to
the card's `keywords` for them, "does not contain" never shows them, and they never match a color
row (see the [advanced search design](./superpowers/specs/2026-11-01-advanced-search-design.md)).
Fix: store the faces and search them.

### Smaller API rough edges

From the final reviews of the API and frontend work, deferred:

- `?colors=` with an empty value returns 422 instead of "no filter"; a repeated `colors=` keeps
  only the last value.
- Every `psycopg.Error` becomes 503, including client input psycopg rejects (NUL bytes in `q`) and
  SQL bugs, which then look like an outage.
- The collector-number sort strips all non-digits, so `M21-10` sorts as 2110.
- For ~265 cards the "most recent printing" shown is a non-English promo.
- `/cards/random` sorts every matching card by `random()` per request — fine at current size.
- The card page always uses Scryfall's `large` image, even when a local image is stored.

### Frontend rough edges

Deferred from the frontend reviews; none blocks use:

- **Search bar:** Esc, blur or an outside click doesn't cancel an Enter pressed while results were
  still loading (it navigates once they arrive). The dropdown stays open after Tab-away and doesn't
  reopen on click after Esc. Missing accessible label on the combobox.
- **Tab titles** go stale on Home, the not-found pages and the set page's code-only fallback.
- **Empty states:** a color filter or random pick with no cards shows an empty grid, no message.
- **Card page:** with the API down it shows three separate error boxes; printing chips show only
  `SET YEAR` (no collector number); a failed `large` image goes straight to the placeholder instead
  of trying the `normal` one; long unbreakable words could overflow the text column at 860–1000 px.
- **Accessibility polish:** color chips are named by bare letters, the loading placeholder has no
  `role="status"`.
- **nginx** (`frontend/nginx.conf.template`): `Host $host` drops the port on API redirects (use
  `$http_host`); `index.html` has no `Cache-Control: no-cache`; `app` is resolved once at startup, so
  recreating only the app container needs a frontend restart.
- **CI:** no `timeout-minutes` on the jobs.

### Docker image size

The API image is ~9.7 GB, mostly PyTorch with CUDA libraries pulled in by `sentence-transformers`.
A CPU-only PyTorch build would likely shrink it to a few GB; that changes where a dependency is
installed from, so it needs a deliberate decision.

## Related

- [BFF API design](./superpowers/specs/2026-10-31-bff-api-design.md) — endpoints and rules.
- [Frontend design](./superpowers/specs/2026-10-31-frontend-design.md) — screens and Docker setup.
- [Database runbook](./runbooks/database.md) — DB lifecycle, reset, shell access.
- [Run pipeline runbook](./runbooks/run-pipeline.md) — getting card data into the table.

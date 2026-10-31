# Backend-for-Frontend API: Design

Status: draft, written 2026-10-31. Generated, not yet reviewed.

## Intent

A FastAPI backend-for-frontend (BFF) for a card discovery UI for Magic: The Gathering players. The
frontend doesn't exist yet. This API defines what it can fetch, shaped around the two things a
player does:

1. **"More like this card."** Type a card name, pick it from autocomplete, land on a card page
   that shows the card, its other printings, and similar cards.
2. **"Show me this set."** Pick a set from a list (newest first), see its cards, filter by color.

The BFF serves the frontend only. It returns exactly what the screens need, in shapes the screens
can render directly. It is not a general-purpose MTG API.

## Core rule: one card, many printings

The `cards` table holds one row per **printing** (`id`). Reprints share an `oracle_id`. Players
think in cards, not printings, so:

- **Autocomplete** and **similar cards** show each card (`oracle_id`) **once**, represented by its
  **most recent printing**.
- **Most recent** = latest `released_at`, ties broken by collector number.
- **Similar cards** never include the reference card itself or any of its reprints.
- The **card page** offers a list of all printings. Choosing one switches the page to that `id`.
- Rows with a NULL `oracle_id` (Scryfall omits it on some layouts, e.g. `reversible_card`) are
  treated as their own card, keyed by `id`.

## Endpoints

All read-only `GET`. JSON unless noted. Every route declares a `response_model`.

### Shared shapes

**`CardSummary`**: one tile or dropdown row. Used everywhere a list of cards appears.

| Field | Notes |
|---|---|
| `id` | printing id; the link target for the card page |
| `name` | |
| `mana_cost` | nullable |
| `type_line` | |
| `colors` | list, nullable |
| `rarity` | |
| `set_code` | |
| `image_url` | `/cards/{id}/image` if a stored image exists, else `null` |

**`CardDetail`**: `CardSummary` plus `oracle_id`, `cmc`, `oracle_text`, `flavor_text`, `power`,
`toughness`, `loyalty`, `keywords`, `color_identity`, `set_name`, `collector_number`,
`released_at`, `artist`, `legalities`. Not exposed: `embedding`, `prices`, `all_parts`, and the
remaining print/frame flags. Add them deliberately later, if a screen needs them.

**`Printing`**: `id`, `set_code`, `set_name`, `collector_number`, `released_at`, `rarity`,
`image_url`.

**`SimilarCard`**: `CardSummary` plus `distance` (cosine distance, lower = more similar).

**`SetSummary`**: `code`, `name`, `released_at`, `set_type`, `card_count`, `icon_svg_uri`.

### Card flow

| Route | Returns | Behaviour |
|---|---|---|
| `GET /cards/autocomplete?q=&limit=` | `list[CardSummary]` | Case-insensitive name match. Prefix matches rank before substring matches ("bol" → "Bolt…" before "Firebolt"), then alphabetical. One entry per card (most recent printing). `q` is required, min length 2. `limit` defaults to 10, max 25. User input `%` and `_` are escaped, so they match literally. |
| `GET /cards/{card_id}` | `CardDetail` | Unknown id → 404. |
| `GET /cards/{card_id}/printings` | `list[Printing]` | All printings sharing the card's `oracle_id`, including the requested one. Newest first. Unknown id → 404. |
| `GET /cards/{card_id}/similar?limit=` | `list[SimilarCard]` | Vector similarity on `embedding`, ascending distance. Deduplicated by `oracle_id`, each shown as its most recent printing. Excludes every printing of the reference card. `limit` defaults to 12, max 50. Unknown id → **404** (not random cards, see Constraints). The reference vector is taken from **any embedded printing of the same `oracle_id`**, not only the requested `id`, so an older printing still finds similar cards *(builder-check call)*. No printing of the card has an embedding → 404 with a distinct message. |
| `GET /cards/{card_id}/image` | image bytes | Served from `card_images` with its stored `content_type` and a long-lived `Cache-Control` (printing images don't change). No stored image → 404. |

### Set flow

| Route | Returns | Behaviour |
|---|---|---|
| `GET /sets` | `list[SetSummary]` | Only sets that have at least one row in `cards`. Newest first by `released_at`. No pagination; the list is bounded by what the pipeline loaded. |
| `GET /sets/{set_code}/cards?colors=` | `list[CardSummary]` | The set's cards ordered by collector number (numeric part first, so "2" < "10"). One entry per card within the set: when a set prints a card more than once (showcase, borderless…), keep the lowest collector number. The other versions still show up under `/printings`. No pagination; a set is bounded at a few hundred cards. `set_code` is case-insensitive. Unknown set → 404. |

**Color filter** (`colors`, comma-separated, any of `W U B R G C`):
- Matches cards that have **any** of the given colors (`R,G` → mono-red, mono-green, and red-green).
- Uses printed `colors`, not `color_identity`.
- `C` = colorless = `colors` is an empty array.
- Invalid letters → 422.
- Omitted → no filtering.

### Removed

The current `GET /cards` (returns the whole fixture) is **removed**. No screen needs "all cards",
and it would be the one unbounded endpoint. The hardcoded fixture in
`src/app/backend/utils/database.py` goes with it.

## Constraints

Most of these come from `docs/api-database-wiring.md`, which remains the reference for the
plumbing.

- **Postgres via existing `src/database/db.py` helpers**, psycopg 3 sync driver. Route handlers are
  `def`, not `async def`.
- **Never `SELECT *`**: explicit column lists, so `embedding` never leaks into a response.
- **SQL values are always parameterised.** Column names only come from constants.
- **Fix `find_similar_cards()` before exposing it**: 404 on unknown id, return `id`, clamp `limit`.
  Without the first fix, an unknown id silently returns arbitrary cards with `distance: null`.
- **Fix the broken `build_card_text` import** in `src/database/etl/embedding_pipeline.py`,
  otherwise no embeddings exist to test against.
- **DB errors → 503** with a generic message. Exception text never reaches the client (it can echo
  connection details). Log it server-side.
- **Raise `HTTPException` outside DB `with` blocks** (wiring doc, Step 2).
- **No new dependencies.** `TestClient` works through `httpx`, already installed via
  `fastapi[standard]`. A connection pool (`psycopg_pool`) is explicitly deferred.
- **Route tests** with `fastapi.testclient.TestClient`, in the existing `unittest` style, runnable
  without Docker (`make run-all-tests` assumes that).
- **SQL integration tests against a real Postgres** *(builder-check call)*: the dedup, ranking,
  escaping, ordering and color-filter rules live in SQL, and a fake cursor can't check them. These
  tests seed a small fixture and **skip when no DB is reachable**. CI (`.github/workflows/tests.yml`)
  has no Postgres today, so they run locally only.

## Goals

- The frontend can build both flows using only these endpoints.
- Every response shape is pinned and visible in `/docs`.
- Unknown ids and set codes return 404, never plausible-looking garbage.

## Non-goals

- The frontend itself.
- Accounts, auth, favourites, decks, or any write endpoint.
- Free-text or rules-text search, or filters beyond color on set pages.
- Prices, legality filtering, and format-aware results.
- Performance work: connection pooling, a vector index (HNSW/ivfflat), trigram name index. Fine at
  the current data size; revisit when it isn't.
- The hardcoded fallback credentials in `get_database_url()` (`src/database/db.py`) and a
  `.env.example`. Known risk, deferred to a separate change.
- Changes to the embedding pipeline.

## Anti-goals: failure even if it "works"

- Similar-cards lists full of reprints of the card you started from.
- Autocomplete showing the same card name many times.
- Results for an id that doesn't exist.
- Database or connection details in an error response.

## Deployment context

- **Caller:** a frontend that will be built afterwards, in this same repo. For now the API runs
  locally and is **not internet-facing**. Rate limiting and auth are out of scope until that
  changes.
- **CORS** *(my call)*: the frontend dev server will most likely run on a different local port, so
  add `CORSMiddleware` with an explicit allow-list read from an env var (e.g. `CORS_ORIGINS`),
  defaulting to empty. Never `*`. GET only.
- **No path prefix.** Routes sit at the root, so `image_url` stays relative (`/cards/{id}/image`).

## Known data limitations

- **Assume every card is embedded.** The embedding pipeline currently only embeds sets released
  from 2025 on (`embedding_pipeline.py:23`). Fixing that is a separate, later task and out of scope
  here. The "no embedding" 404 stays as a safety net, but it isn't the main path.

- `card_faces` is not stored. For double-faced cards, Scryfall puts `colors`, `mana_cost` and
  `image_uris` on the faces, so these can be NULL at top level. Such cards won't match any color
  filter (they still appear unfiltered) and may have no image. Accepted for now.
- Images exist only where `make run-image` has run, and only in the `normal` size.

## Left to the builder

- Module layout (routers vs one file, where SQL and response models live), following existing
  repo conventions.
- Whether to extend `get_cursor()` with a `row_factory` or use `get_db_connection()` directly.
- How tests isolate the DB (dependency override with a fake vs patching).
- Exact SQL for dedup and ranking (e.g. `DISTINCT ON (oracle_id)`).
- Exact 404/422 message wording.

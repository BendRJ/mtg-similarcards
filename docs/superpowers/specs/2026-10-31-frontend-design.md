# Card Discovery Frontend: Design

Status: draft, written 2026-10-31. Generated, not yet reviewed.

Builds on the backend-for-frontend API in
[2026-10-31-bff-api-design.md](./2026-10-31-bff-api-design.md), which is merged.

## Intent

A web UI for Magic: The Gathering players to discover cards, in the spirit of Scryfall's search-first
start page. A player comes in one of three ways:

1. **Find a card**, then explore similar cards and its other printings.
2. **Find a set**, then browse its cards, filtered by color.
3. **Pick a color**, then browse 100 random cards of that color.

The user approved the wireframes as "exactly how I imagined it". They are in
[2026-10-31-frontend-mockups.html](./2026-10-31-frontend-mockups.html) (open it in a browser). Its
layout, palette tokens (light and dark) and pip colors are the visual reference; the screens below
describe the same five pages in words.

## Screens

Every page except Home has a top bar with the logo (link to Home) and the same search bar.

### 1. Home `/`
- Centered logo and a large search bar ("Search cards or sets…").
- Six round color buttons below it: W, U, B, R, G, and C (colorless), each linking to `/color/:c`.

### 2. Search dropdown (inside the search bar, on every page)
- Opens once the text reaches 2 characters.
- One dropdown with two groups: **Cards** first, then **Sets**.
  - Cards come from `GET /cards/autocomplete?q=` (up to 10). Each row shows a small image, the name,
    and "type · set code".
  - Sets are matched in the browser against the `/sets` list, which is loaded once per page load:
    case-insensitive substring match on the name, or prefix match on the code ("mh3" finds Modern
    Horizons 3). Up to 5, newest first. Each row shows the set icon, the name, and "CODE · year".
  - Sets of type `token`, `memorabilia` and `minigame` never appear here.
- Keyboard: ↑/↓ move through both groups, Enter opens the highlighted row, Esc closes the dropdown.
  Mouse click opens a row too.
- Picking a card goes to `/card/:id`; picking a set goes to `/set/:code`.
- Typing is debounced (~150 ms). A slow, older response must never overwrite a newer one.
- Nothing matches → the dropdown shows "No cards or sets found".

### 3. Color page `/color/:c`
- `:c` is one of `W U B R G C` (case-insensitive in the URL). Anything else shows a "not found" page.
- Header: the color's button, the title ("Random red cards", "Random colorless cards"…), and a
  **Shuffle** button that loads a fresh 100.
- Grid of 100 card images. Clicking one goes to `/card/:id`.
- "Red" uses the same any-of rule as the set filter: red, including multicolor red cards.

### 4. Card page `/card/:id`
- Left: large card image. Right: name and mana cost, type line, set name, collector number,
  rarity, artist, and oracle text (with power/toughness or loyalty when present).
- **Printings strip**: a horizontal scrolling row of all printings (`/cards/:id/printings`), newest
  first, with the current one highlighted. Clicking one navigates to `/card/<that id>`, so the URL
  always names the printing shown.
- **Similar cards**: a grid of the 12 results from `/cards/:id/similar`.
  - If the API returns the "no embedding" 404, this section reads "Similar cards aren't available
    for this card yet" instead of failing the page.
- Unknown id → a "card not found" page.

### 5. Set page `/set/:code`
- Header: set icon, name, code and release month/year, and color chips W U B R G C on the right.
- Chips toggle on and off, combined as any-of. No chips selected means the whole set. The chip
  state lives in the URL (`?colors=R,G`), so it survives a reload and can be shared.
- Grid of the set's cards (`/sets/:code/cards`) in collector order.
- Unknown set → a "set not found" page.

### Shared behaviour
- **Card tiles** use the card image at card proportions (63:88), with the name as alt text. A card
  without any image shows a neutral placeholder with the name on it.
- **Loading** shows lightweight placeholders. **API errors** (503, network) show a short "Couldn't
  reach the card database. Try again." with a retry button. Never a blank page.
- **Look**: follows the system's light or dark setting, like the mockups (my call). Colored pips
  use soft MTG-like tones. Plain CSS, no UI library.
- **Responsive**: works at phone width. Grids reflow, and the card page stacks image above details.
- The browser tab title names the page (card name, set name, "Random red cards").
- A small footer on every page credits the data and images (my call; Scryfall asks apps to keep
  artist and copyright visible): "Card data and images via Scryfall. Magic: The Gathering is ©
  Wizards of the Coast." The card page already shows the artist.

## API changes (in the existing backend)

### `GET /cards/random?colors=&limit=`
- Returns `list[CardSummary]`: random real game cards, each card (`oracle_id`) once, shown as its
  most recent printing.
- Same `colors` parameter, pattern and any-of rule as `/sets/{code}/cards`, including `C`. Unlike
  the set endpoint, `colors` is **required** here (a color page always has one).
- Uses the same filter as autocomplete and similar cards (`PLAYABLE`: no tokens, emblems, art
  cards, or cards from token/memorabilia/minigame sets).
- `limit` defaults to 100, max 100. Every call returns a fresh random pick.
- Must be declared above `/cards/{card_id}` in the router, like `/cards/autocomplete`.

### Image fallback in `image_url`
- Today `image_url` is `/cards/{id}/image` when a stored image exists, else `null`.
- New: when no image is stored, fall back to Scryfall's link `image_uris->>'normal'` from the
  `cards` row. Still `null` when neither exists (e.g. double-faced cards, whose images live on the
  faces, which aren't stored).
- Applies everywhere `image_url` appears: summaries, detail, printings, similar, set cards, random.
- The browser then loads those images directly from Scryfall's CDN (`cards.scryfall.io`). The user
  approved this.

## How it gets built and run

- **Stack** (user's choice): React + Vite + TypeScript, in `frontend/` at the repo root.
- **Routing**: React Router (my call).
- **Approved packages** (user confirmed 2026-10-31, pinned exactly). Anything beyond this list
  needs a new confirmation (org rule: name + version, then the user's OK):
  - runtime: `react` 19.3.1, `react-dom` 19.3.1, `react-router` 8.5.1
  - dev: `vite` 8.3.5, `@vitejs/plugin-react` 6.1.2, `typescript` 7.0.2, `@types/react` 19.3.0,
    `@types/react-dom` 19.3.0, `vitest` 5.0.5, `jsdom` 30.1.3, `@testing-library/react` 16.3.3,
    `@testing-library/user-event` 14.6.8
- **API calls** go to relative paths (`/cards/...`, `/sets/...`), so the frontend never needs to
  know where the API lives.
- **Local dev**: `npm run dev` in `frontend/`, with Vite's dev-server proxy forwarding `/cards` and
  `/sets` to `http://127.0.0.1:8000` (the API from `make dev`). No CORS needed. A `make` target
  for it, in the style of the existing ones.
  - Node works on the user's Mac (v26.13.0, fixed 2026-10-31), so npm commands run locally.
- **Docker**: a new `frontend` service in `docker-compose.yml`:
  - Multi-stage `frontend/Dockerfile`: a Node stage builds the static files, an nginx stage serves
    them.
  - nginx forwards `/cards` and `/sets` to the `app` service over the Compose network, and serves
    `index.html` for every other path so client-side routes survive a reload.
  - Published on `127.0.0.1:8080` (my call), loopback only like postgres. `depends_on: app`.
  - Base images pinned to exact versions (the existing Dockerfile pins by digest).
  - `make docker-run` should bring up the frontend too, or there's a documented make target that
    does.
- **Tests**:
  - Backend changes: TDD in the existing unittest style. That means route tests plus real-Postgres
    SQL tests for `/cards/random` and for the image fallback.
  - Frontend: unit tests for the logic that has rules: matching sets in the browser, the color
    param and chips, keyboard navigation in the dropdown, and ignoring stale responses. The test
    runner is a dependency too, so Vitest needs the user's OK.
  - A manual end-to-end check through Docker at the end.
- **CI** (builder-check call): add a Node job to `.github/workflows/tests.yml` running the
  type-check, the frontend unit tests and `vite build`, with the same pinned Node version as the
  Dockerfile. Python jobs stay as they are.
- **Loopback only** (user decision): change the `app` service's published port to
  `"127.0.0.1:${HOST_PORT:-8000}:${API_PORT:-8000}"`, so it matches postgres and the frontend
  and nothing is reachable from the local network. The frontend reaches the API over the Compose
  network, so this doesn't affect it.

## Goals

- All five screens work against the real API and data, in Docker and in local dev.
- The search bar finds both cards and sets, as fast as typing.
- Every API failure mode the UI can hit (404, 422, 503, network) shows a human message.

## Non-goals

- Accounts, favourites, decks, collections, prices.
- Advanced Scryfall-style search syntax (`t:creature c:r`). Name search only.
- Server-side rendering, SEO, analytics.
- Production hosting, TLS, auth, rate limiting. The app is local and not internet-facing (as
  agreed for the API). Internet publishing is a separate later project: single public reverse
  proxy with TLS, no published `app`/`postgres` ports, credential fix, rate limiting, indexes.
- Fixing the deferred API minors (see `docs/api-database-wiring.md`).

## Anti-goals

- A blank page or a raw error/stack trace on any failure.
- The same card name repeated in the search dropdown or a grid.
- A slow, older search response overwriting what the player now sees.
- Loading the whole 384-number embedding, or any heavy payload, into the browser.

## Left to the builder

- Component and file layout inside `frontend/`, CSS organisation, and exact spacing and colors
  (within the wireframes).
- The debounce value within roughly 100–250 ms.
- nginx config details, and the Node and nginx base image versions (pinned, recent).
- Whether TypeScript types for API responses are hand-written or generated from `/openapi.json`.
  Hand-written is fine; adding a generator is a new dependency.

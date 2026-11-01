# Advanced Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `/search` page where players build AND-combined filter rows on rules text, name,
keyword, type and color, sort by name or mana value, and see each matching card once (latest
matching printing), backed by `POST /cards/search`.

**Architecture:**
- **Backend:**
  - Pydantic validates the request: field, op and value per filter.
  - A small builder in `queries.py` turns each filter into a fixed SQL fragment with bound parameters (`p0`, `p1`, …).
  - One query does filter → `DISTINCT ON (CARD_KEY)` → sort → limit 200, plus `count(*) OVER ()` for the total.
- **Frontend:**
  - A pure `lib/searchFilters.ts` module holds the filter model, URL round-trip and request building.
  - A `FilterRow` component renders one row.
  - An `AdvancedSearchPage` holds the rows in local state and keeps the last searched state in the URL.

**Tech Stack:** FastAPI + psycopg 3 (sync), Pydantic 2, unittest. React 19, react-router 8.5.1, Vitest 5 + Testing Library.

**Spec:** `docs/superpowers/specs/2026-11-01-advanced-search-design.md`. The visual reference is `docs/superpowers/specs/2026-11-01-advanced-search-mockup.html`.

## Global Constraints

- **Branch** `feature/advanced-search`. Commit messages carry no AI attribution.
- **No new packages**, npm or Python.
- **SQL safety:** user text only ever reaches SQL as a bound parameter. Only fixed fragments chosen from the validated (field, op) are interpolated. Text values go through `escape_like` and are matched with `ILIKE`.
- **Unknown values never match.** A NULL field never matches a positive or a negative filter on it. The one exception is the rules-text fallback: `oracle_text IS NULL` cards match "contains" through any `keywords` element `ILIKE` the text, and never match "does not contain".
- **Limits:**
  - 1–20 filters
  - text values 1–100 characters after trimming
  - color values 1–6 distinct letters from `W U B R G C`
  - `sort` ∈ `name` (default), `cmc_asc`, `cmc_desc`
  - at most 200 cards returned, with `total` = the full count
- **Type list** (for `is`/`is_not`): Artifact, Battle, Creature, Enchantment, Instant, Kindred, Land, Planeswalker, Sorcery. Matching is by whole word, case-insensitive. Kindred matches `Kindred|Tribal`.
- **Sorting:** ties are broken by name, and NULL `cmc` sorts last in both directions.
- **Results** are filtered with `PLAYABLE`. Each card (`CARD_KEY`) appears once, as its latest printing matching every filter (`released_at DESC NULLS LAST, COLLECTOR_ORDER`, as in autocomplete).
- **Copy, exactly:**
  - "Advanced search" (page title, top-bar link, tab title)
  - "+ Add filter"
  - "Search"
  - "Sort by"
  - "No cards match these filters."
  - "N cards" (N = total)
  - "showing the first 200" (only when total > 200)
  - "Remove filter" (aria-label of ✕)
- **Frontend URL format** (`/search?…`):
  - Repeated `f=<field>.<op>.<value>`, with the value split off after the second `.`. Colors are written as letters, e.g. `f=colors.any.WRC`.
  - Optional `sort=cmc_asc|cmc_desc`.
  - Invalid parts are dropped silently, never an error page.
- **Accessibility:**
  - every select and input has a label
  - chips are toggle buttons with `aria-pressed`
  - rows wrap at 375 px with no horizontal scroll
- **Tests:** `make run-all-tests` (backend) and `make frontend-test` plus `npm --prefix frontend run typecheck` (frontend).

## Review Focus

1. **`%`, `_` or `\` in any text box** match literally. Pinned in Task 1.
2. **A "does not contain" or "is not" row never returns cards whose field is NULL.** This includes rules text on multi-part cards and the type line on reversible cards. Pinned in Task 1.
3. **"Color has all of C + R"** returns nothing; **"has none of C"** excludes only colorless cards. Pinned in Task 1.
4. **A hand-edited `/search?f=garbage&f=colors.any.XYZ&sort=bogus` URL** gives a clean page with the invalid parts dropped. Pinned in Task 3.
5. **Incomplete rows** (empty text, no chips) are left out of the request. All rows empty → no request at all. Pinned in Task 3.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/app/backend/models.py` (modify) | `SearchFilter`, `SearchRequest`, `SearchResponse`, `TYPES`. |
| `src/app/backend/queries.py` (modify) | `filter_clause(f, i)`, `search_cards(cur, filters, sort, limit=200)`. |
| `src/app/backend/routers/cards.py` (modify) | `POST /cards/search`. |
| `frontend/src/lib/searchFilters.ts` (create) | Filter model, defaults per field, URL parse/serialize, `toRequest`. |
| `frontend/src/components/FilterRow.tsx` (create) | One row: field, op, value, remove. |
| `frontend/src/pages/AdvancedSearchPage.tsx` (create) | Rows state, sort, Search, URL sync, results. |
| `frontend/src/api.ts`, `types.ts`, `App.tsx`, `components/Layout.tsx`, `styles.css` (modify) | `api.search` (POST), types, `/search` route, top-bar link, row styles. |

---

### Task 1: Backend search query

**Files:**
- Modify: `src/app/backend/queries.py`
- Test: `tests/test_queries_search.py`

**Interfaces:**
- Produces:
  - `queries.SEARCH_TYPES: tuple[str, ...]` (the nine types).
  - `queries.search_cards(cur, filters: list[dict[str, Any]], sort: str, limit: int = 200) -> dict[str, Any]`. It returns `{"total": int, "cards": list[dict]}`, where card dicts have the `CardSummary` keys. Each filter dict is `{"field", "op", "value"}`, already validated: `value` is a trimmed `str`, or a `list[str]` for colors.
- Inner query: `SELECT DISTINCT ON (CARD_KEY) <SUMMARY_COLUMNS>, c.cmc FROM cards c WHERE PLAYABLE AND <clause_0> AND <clause_1> … ORDER BY CARD_KEY, c.released_at DESC NULLS LAST, <COLLECTOR_ORDER>`.
- Outer query: it selects the summary columns explicitly plus `count(*) OVER () AS total`, orders by the sort, and applies `LIMIT %(limit)s`. With zero rows, `total` is 0.
- Clause fragments (`pN` = the bound parameter for filter N; text parameters are `%` + `escape_like(value)` + `%`):

| field.op | fragment |
|---|---|
| oracle_text.contains | `(c.oracle_text ILIKE %(pN)s OR (c.oracle_text IS NULL AND EXISTS (SELECT 1 FROM unnest(c.keywords) k WHERE k ILIKE %(pN)s)))` |
| oracle_text.not_contains | `(c.oracle_text IS NOT NULL AND c.oracle_text NOT ILIKE %(pN)s)` |
| name.contains / not_contains | `c.name ILIKE %(pN)s` / `c.name NOT ILIKE %(pN)s` |
| keywords.contains | `EXISTS (SELECT 1 FROM unnest(c.keywords) k WHERE k ILIKE %(pN)s)` |
| keywords.not_contains | `(c.keywords IS NOT NULL AND NOT EXISTS (SELECT 1 FROM unnest(c.keywords) k WHERE k ILIKE %(pN)s))` |
| type.is / is_not | `c.type_line ~* %(pN)s` / `(c.type_line IS NOT NULL AND c.type_line !~* %(pN)s)`, with pN = `\m(Land)\M`, and Kindred → `\m(Kindred\|Tribal)\M` (built only from `SEARCH_TYPES`) |
| type.contains / not_contains | `c.type_line ILIKE %(pN)s` / `(c.type_line IS NOT NULL AND c.type_line NOT ILIKE %(pN)s)` |
| colors.any | `(c.colors && %(pN_c)s::text[] OR (%(pN_cl)s AND c.colors = '{}'))` |
| colors.all | C plus other colors → `FALSE`. Only C → `c.colors = '{}'`. Else → `c.colors @> %(pN_c)s::text[]` |
| colors.none | `(c.colors IS NOT NULL AND NOT (c.colors && %(pN_c)s::text[]) AND NOT (%(pN_cl)s AND c.colors = '{}'))` |

- Sort: `name` → `t.name`; `cmc_asc` → `t.cmc ASC NULLS LAST, t.name`; `cmc_desc` → `t.cmc DESC NULLS LAST, t.name`. An unknown (field, op) raises `ValueError`, which is a programming error, because validation happens upstream.

- [ ] **Step 1:** `git checkout -b feature/advanced-search`. Commit the spec and plan (`docs: add advanced search design and plan`).
- [ ] **Step 2: Failing DB tests.** `tests/test_queries_search.py`, class `TestSearchQuery(DBTestCase)`, with one test per row of the table, plus:
  - `test_user_example`: artifact + token + not clue + type is Land. It returns an "Artifact Land" card and a "Land" card, excludes a Clue-mentioning one, excludes a "Landfall" creature, and returns each card once even with two printings.
  - `test_oracle_contains_falls_back_to_keywords`: a NULL-oracle card with `keywords=["Flying","Transform"]` matches "contains fly". It doesn't match "does not contain zzz".
  - `test_null_never_matches_negative`: NULL `type_line` doesn't match `type.is_not Land`, and NULL `colors` doesn't match `colors.none ["G"]`.
  - `test_wildcards_literal`: "50%" matches only a name containing "50%". "a_c" doesn't match "abc".
  - `test_colors_all_with_c_is_empty`, `test_colors_none_c_excludes_only_colorless`.
  - `test_kindred_matches_tribal`.
  - `test_latest_matching_printing_shown`.
  - `test_sort_cmc_asc_desc_nulls_last`.
  - `test_limit_and_total`: with 5 matches and `limit=2`, it returns 2 cards and `total == 5`.
  - `test_excludes_tokens`: `PLAYABLE` applies.
- [ ] **Step 3:** `make run-all-tests`. Expected: the new tests FAIL (`search_cards` doesn't exist).
- [ ] **Step 4:** Implement `filter_clause` and `search_cards`.
- [ ] **Step 5:** `make run-all-tests`. Expected: PASS, with the DB tests actually run.
- [ ] **Step 6:** Commit `feat: add advanced card search query`.

---

### Task 2: Backend request models and route

**Files:**
- Modify: `src/app/backend/models.py`, `src/app/backend/routers/cards.py`
- Test: `tests/test_api_cards.py`

**Interfaces:**
- Consumes: `queries.search_cards`, `queries.SEARCH_TYPES` (Task 1).
- Produces:
  - `SearchFilter(BaseModel)`: `field`, `op`, `value: str | list[str]`. A model validator enforces the (field, op) pairs and the value rules from the Global Constraints. It trims text, and it uppercases and dedupes color letters, keeping WUBRGC order.
  - `SearchRequest`: `filters: list[SearchFilter]` (1–20), `sort: Literal["name","cmc_asc","cmc_desc"] = "name"`.
  - `SearchResponse`: `total: int`, `cards: list[CardSummary]`.
  - Route `POST /cards/search` → `SearchResponse`, calling `queries.search_cards(cur, [f.model_dump() for f in req.filters], req.sort)`. Declare it above `/{card_id}`.
- [ ] **Step 1: Failing route tests.** `search_cards` is patched.
  - A valid body gives 200, and the patched function receives the trimmed and normalised filters (`"  artifact "` → `"artifact"`, `["r","W","r"]` → `["W","R"]`).
  - These give 422, each its own case: unknown field; op not valid for the field (`colors.contains`); empty text after trimming; 101 characters; a type not in the list for `is`; color "X"; empty color list; 0 filters; 21 filters; `sort="bogus"`.
  - `type.contains "Elf"` passes free text.
- [ ] **Step 2:** `make run-all-tests`. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** `make run-all-tests`. Expected: PASS.
- [ ] **Step 5:** Commit `feat: add POST /cards/search with validated filters`.

---

### Task 3: Frontend filter model and URL round-trip

**Files:**
- Create: `frontend/src/lib/searchFilters.ts`, `frontend/src/lib/searchFilters.test.ts`
- Modify: `frontend/src/types.ts` (`SearchResponse { total: number; cards: CardSummary[] }`), `frontend/src/api.ts` (a `post` helper; `api.search(req, signal?)` → `SearchResponse`)

**Interfaces:**
- Produces:
  - `type Field = "oracle_text" | "name" | "keywords" | "type" | "colors"`
  - `type Op = "contains" | "not_contains" | "is" | "is_not" | "any" | "all" | "none"`
  - `type Filter = { field: Field; op: Op; value: string | Color[] }`
  - `type Sort = "name" | "cmc_asc" | "cmc_desc"`
  - `FIELDS`: label, ops with labels, default op and value kind per field. Labels: "Rules text", "Name", "Keyword", "Type", "Color". Op labels: "contains", "does not contain", "is", "is not", "has any of", "has all of", "has none of".
  - `TYPES`: the nine types.
  - `defaultFilter(field = "oracle_text"): Filter`
  - `isComplete(f): boolean`
  - `parseSearchParams(params: URLSearchParams): { filters: Filter[]; sort: Sort }`: drops invalid parts and returns `[defaultFilter()]` when nothing valid is left.
  - `toSearchParams(filters, sort): URLSearchParams`: complete filters only, and no `sort` when it's `name`.
  - `toRequest(filters, sort): SearchRequest | null`: complete filters only, trimmed; `null` when none are complete.
  - `api.search(req, signal?)` POSTs JSON with `Content-Type: application/json`. Errors are mapped exactly like `get` (`ApiError`, abort passthrough).
- [ ] **Step 1: Failing tests:**
  - A round-trip of the user's example plus `sort=cmc_asc` through `toSearchParams` and then `parseSearchParams` returns an equal result.
  - A value containing `.` and `&` survives.
  - `parseSearchParams("f=garbage&f=colors.any.XYZ&f=type.is.Goblin&sort=bogus")` → `[defaultFilter()]`, `name` (Review Focus 4).
  - `f=colors.any.wrc` → `["W","R","C"]`.
  - `toRequest` with one empty text row and one chip-less color row → `null` (Review Focus 5). A mix keeps only the complete rows.
  - `api.search` POSTs to `/cards/search` with the JSON body. A 422 rejects with `ApiError(422)`.
- [ ] **Step 2:** `make frontend-test`. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** `make frontend-test` PASS; typecheck clean.
- [ ] **Step 5:** Commit `feat: add advanced search filter model, URL format and API client`.

---

### Task 4: Advanced search page

**Files:**
- Create: `frontend/src/components/FilterRow.tsx`, `frontend/src/pages/AdvancedSearchPage.tsx`, `frontend/src/pages/AdvancedSearchPage.test.tsx`
- Modify: `frontend/src/App.tsx` (route `/search`), `frontend/src/components/Layout.tsx` (an "Advanced search" link to `/search` in the top bar, next to the search box), `frontend/src/styles.css` (row layout per the mockup, wrapping at phone width)

**Interfaces:**
- Consumes: Task 3 exports, `api.search`, `useAsync`, `CardGrid`, `ErrorState`, `Loading`, `Layout`.
- `FilterRow({ filter, index, onChange, onRemove })` renders:
  - a field select (label "Field")
  - an op select (label "Condition")
  - the value: a text input (label "Value"), the type select for `is`/`is_not`, or W U B R G C chips with `aria-pressed`
  - a ✕ button with aria-label "Remove filter"

  Changing the field resets the row to `defaultFilter(field)`. Rows after the first show a muted "and".
- `AdvancedSearchPage`:
  - Its initial rows and sort come from `parseSearchParams(useSearchParams())`.
  - Search, or Enter in a text input, writes `toSearchParams` into the URL (push, not replace).
  - Results come from `useAsync` on `toRequest(parsed URL state)`. No request runs when that's `null`; a short hint shows instead.
  - Above the grid: "N cards", plus " · showing the first 200" when total > 200. Zero results → "No cards match these filters." Errors use `ErrorState`.
  - "+ Add filter" appends `defaultFilter()`. The Sort select (label "Sort by") offers Name, Mana value ↑, Mana value ↓.
  - `document.title` = "Advanced search", set in an effect.
- [ ] **Step 1: Failing tests** (`api` mocked with a factory that keeps the real `ApiError`; `vi.clearAllMocks()` in `beforeEach`):
  - **The user's example built through the UI:** set row 1 to "artifact"; add rows; switch row 3 to "does not contain" "clue"; set a Type row to "is Land"; set a Color row with W R C and one with U B G; choose Mana value ↑; press Search.
    - `api.search` is called once with exactly the expected request.
    - The URL search equals `toSearchParams` of the same state.
  - **Opening `/search?f=oracle_text.contains.artifact`** runs the search on load and renders the returned cards and "N cards".
  - **Opening `/search`** makes no `api.search` call and shows the hint.
  - **Removing a row** with "Remove filter" drops it from the next request.
  - **Changing a row's field to Color** shows the chips and resets the value.
  - **`total: 250` with 200 cards** shows "250 cards · showing the first 200".
  - **Empty results** show "No cards match these filters."
  - **`ApiError(503)`** shows the error copy.
  - **The top bar** in `Layout` has a link "Advanced search" to `/search`.
- [ ] **Step 2:** `make frontend-test`. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** `make frontend-test` PASS; typecheck and `npm --prefix frontend run build` clean.
- [ ] **Step 5:** Commit `feat: add advanced search page with filter builder`.

---

### Task 5: Docs and end-to-end check

**Files:**
- Modify: `docs/index.md` (design link, plus `/search` in the entry points), `README.md` (one line on Advanced search), `docs/api-database-wiring.md` (the "Cards without rules text" note under the follow-ups, linked to the faces follow-up)

- [ ] **Step 1:** Update the docs.
- [ ] **Step 2:** `docker-compose up -d --build app frontend`, then POST the user's example to `127.0.0.1:8080/cards/search`. Expected: 200, `total > 0`, card names all with "Land" in the type line, no duplicate names from the same card. Then a 422 for `{"filters": []}`. Then `GET 127.0.0.1:8080/search?f=oracle_text.contains.flying` → 200 HTML.
- [ ] **Step 3:** `make run-all-tests`, `make frontend-test`, typecheck. All pass.
- [ ] **Step 4:** Commit `docs: document advanced search`.

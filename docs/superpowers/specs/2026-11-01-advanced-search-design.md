# Advanced Search: Design

Status: draft, written 2026-11-01. Generated, not yet reviewed.

Builds on the merged BFF API ([2026-10-31-bff-api-design.md](./2026-10-31-bff-api-design.md)) and
frontend ([2026-10-31-frontend-design.md](./2026-10-31-frontend-design.md)).

## Intent

Players want to find cards by what they *do*, e.g. "lands whose rules text mentions artifacts and
tokens but not Clues, using only white, red or no color". The user has been running SQL like this
by hand:

```sql
… where lower(oracle_text) like '%artifact%'
  and lower(oracle_text) like '%token%'
  and not lower(oracle_text) like '%clue%'
  and type_line = 'Land'
  -- and ('W' = any(colors) or 'R' = any(colors) or cardinality(colors) = 0)
  --     and not 'B' = any(colors) and not 'G' = any(colors) and not 'U' = any(colors)
order by cmc   -- one row per card (latest printing)
```

Scryfall's query syntax (`o:artifact -o:clue t:land`) can express this, but the user finds it
not friendly enough. This feature is a **visual filter builder**: rows of field + operator + value,
any number of them, combined with AND.

The user approved the mockup as "perfect":
[2026-11-01-advanced-search-mockup.html](./2026-11-01-advanced-search-mockup.html) (open in a browser).

## The page

- Route `/search`, titled "Advanced search", linked from the top bar on every page ("Advanced
  search", next to the search box). The home search bar and its dropdown stay unchanged.
- Starts with one empty "Rules text contains" row.

### Filter rows

Each row: **field** dropdown, **operator** dropdown, **value**, and a ✕ to remove the row.
"+ Add filter" appends a new row (default: Rules text · contains). Every row must match (AND).
Rows after the first are prefixed with a muted "and".

| Field | Operators | Value | Matches when |
|---|---|---|---|
| Rules text | contains / does not contain | text box | `oracle_text` contains the text, case-insensitive. **Fallback for cards without rules text** (see below): "contains" matches when one of the card's `keywords` contains the text; "does not contain" never matches them. |
| Name | contains / does not contain | text box | same rule on `name` |
| Keyword | contains / does not contain | text box | contains: one of the card's `keywords` contains the text, case-insensitive ("first" matches "First strike"). does not contain: no keyword contains it; cards with an empty keyword list match. |
| Type | is / is not | dropdown: Artifact, Battle, Creature, Enchantment, Instant, Kindred, Land, Planeswalker, Sorcery | the type line contains that type as a word, case-insensitive. "Is Land" also matches "Artifact Land". **Kindred** also matches the older word **Tribal**. |
| Type | contains / does not contain | text box (free text, e.g. "Elf", "Legendary", "Equipment") | `type_line` contains the text, case-insensitive (substring, like rules text). |
| Color | has any of / has all of / has none of | W U B R G C chips (multi-select) | any of: card has at least one chosen color (C = colorless, i.e. `colors = '{}'`). all of: card has every chosen color; if C is among them, the card must be colorless and nothing else is allowed (so "all of C + R" matches nothing). none of: card has none of the chosen colors (C = not colorless). |

- **Unknown values never match.** A card whose field is NULL never matches a filter on that field,
  positive or negative, so a "does not contain" or "is not" row never shows a card just because the
  value is missing. The one exception is the rules-text keyword fallback above.
- **Cards without rules text.** Scryfall stores the rules text of multi-part cards (transform,
  modal double-faced, adventure, split, …) on their faces, which the ETL doesn't store, so
  `oracle_text` is NULL for ~980 real cards. User decision (2026-11-01): "Rules text contains X"
  falls back to their `keywords` array (every such card has one, often non-empty, e.g. Delver of
  Secrets → Flying, Transform); "Rules text does not contain X" never shows them. Storing the faces
  is a separate follow-up.
- Text values are matched literally: `%`, `_` and `\` don't act as wildcards (same escaping as
  autocomplete).
- Cards with NULL `colors` (double-faced cards, whose colors live on the faces) never match a color
  row, consistent with the set page (the "unknown values never match" rule).
- Rows that are incomplete (empty text, no chips selected) are ignored when searching; they're not an
  error.
- Changing a field resets that row's operator and value to the field's defaults.

The user's commented query becomes: Color · has any of · W R C, and Color · has none of · U B G.

### Sorting

A "Sort by" dropdown: **Name** (default), **Mana value ↑**, **Mana value ↓**. Ties are broken by name.
Cards with no mana value (NULL `cmc`) sort last in both directions.

### Running a search and results

- A **Search** button runs it; pressing Enter in a text box does too. No search-as-you-type.
- The filters and sort live in the URL query string, so a search survives reload, can be
  bookmarked and shared, and the browser's back button returns to the previous search. Opening a
  `/search?…` URL runs that search directly.
- Results: the same card grid and tiles as the other pages. **Each card once, as its latest
  printing** (the same "most recent printing" rule as autocomplete), only real game cards (the
  existing `PLAYABLE` filter: no tokens, emblems, art cards, or token/memorabilia/minigame sets).
- At most **200** results are shown. Above the grid: "N cards" (the total count, even when only 200
  are shown), and "showing the first 200" when it was capped.
- No filters (all rows empty) → no request; the page shows a short hint instead of results.
- Zero results → "No cards match these filters."
- Errors: the existing `ErrorState` ("Couldn't reach the card database. Try again.").
- Tab title: "Advanced search".

## API

`POST /cards/search` with a JSON body. POST rather than GET because the filter list is structured
and variable-length; the frontend's own URL encoding is separate from the API call.

```json
{
  "filters": [
    {"field": "oracle_text", "op": "contains",     "value": "artifact"},
    {"field": "oracle_text", "op": "not_contains", "value": "clue"},
    {"field": "type",        "op": "is",           "value": "Land"},
    {"field": "colors",      "op": "any",          "value": ["W", "R", "C"]},
    {"field": "colors",      "op": "none",         "value": ["U", "B", "G"]}
  ],
  "sort": "cmc_asc"
}
```

Response: `{"total": 37, "cards": [CardSummary, …]}`. `total` is the full match count, and `cards`
holds at most 200.

**Validation (Pydantic; anything else → 422):**
- `field` ∈ {`oracle_text`, `name`, `keywords`, `type`, `colors`}; `op` must fit the field
  (oracle_text, name, keywords: `contains`, `not_contains`; type: `is`, `is_not`, `contains`,
  `not_contains`; colors: `any`, `all`, `none`).
- Text values (every `contains`/`not_contains`): 1–100 characters after trimming. Type `is`/`is_not`
  values: one of the nine types. Color values: 1–6 distinct letters from `W U B R G C`.
- At most **20** filters; at least **1**.
- `sort` ∈ {`name`, `cmc_asc`, `cmc_desc`}, default `name`.

**Query building:**
- Every value is a bound parameter. Only fixed SQL fragments chosen from the validated field/op
  are interpolated, never user text.
- Each filter becomes one `AND (…)` clause on the inner query.
- Dedupe with `DISTINCT ON (CARD_KEY)` ordered by latest printing, exactly as `autocomplete_cards`.
  Sort and limit happen on the outer query.
- `total` comes from `count(*) OVER ()` on the outer query, or a second query (builder's call).
- Type "is X" uses a word match on `type_line` (e.g. `~* '\mX\M'`), so "Land" doesn't match
  "Landfall" in a type line. Kindred → `(Kindred|Tribal)`.

## Constraints

- Backend rules as before: sync `def` handlers; no `SELECT *` on tables; values parameterised;
  real-Postgres SQL tests via `tests/db_fixtures.py`; route tests with a fake cursor.
- Frontend: no new npm packages. React Router search params for the URL state. Reuse `CardGrid`,
  `ErrorState`, `Loading`, `useAsync`, and the API client patterns.
- Accessibility: every select and input has a label (visually hidden is fine); chips are toggle
  buttons with `aria-pressed`; the ✕ button has an accessible name ("Remove filter").
- Responsive: rows wrap at phone width, with no horizontal scroll at 375 px.
- Performance: no new indexes. A full scan with `ILIKE` over ~117k rows is acceptable at this size.

## Goals

- The user's example query can be built in the UI with the same structure. Results differ from the
  hand-written SQL only where the spec deliberately differs: "Type is Land" is a word match (so
  "Artifact Land" counts, unlike `type_line = 'Land'`), and cards without rules text follow the
  keyword fallback.
- Any number of filters (up to 20), any mix of fields, AND-combined.
- Shareable, reload-safe URLs.

## Non-goals

- OR between rows, or nested groups. Color "has any of" covers the common OR case.
- Other fields (mana value ranges, rarity, set, power/toughness, format legality).
- Search-as-you-type, saved searches, Scryfall query syntax.
- Changing the home search bar or the set page's color chips.

## Anti-goals

- User text ever reaching SQL as anything but a bound parameter.
- The same card appearing more than once in the results.
- `%` or `_` in a text box acting as a wildcard.
- A filter silently doing something different from what its row says.

## Decided after the builder check

- **Which printing is tested:** the filters apply per printing; a card is shown once, as its latest
  printing that matches every filter (filter in the inner query, then `DISTINCT ON`). Rules text,
  type and colors rarely differ between printings, so this matters only at the edges.
- **Spec vs mockup:** this document wins on behaviour; the mockup wins on visuals (layout, spacing,
  colors). The mockup predates the Keyword field and the Type contains operators; they use the same
  row layout.

## Left to the builder

- Component split for the builder UI, URL query-string format (it must round-trip every filter and
  survive hand-editing: invalid parts are dropped, not an error page), CSS details within the mockup.
- `total` via window function or a separate count.
- Exact hint and copy for the empty-filter state (short and plain).

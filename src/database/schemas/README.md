# Card Schema Documentation

This directory contains example JSON responses from the [Scryfall API](https://scryfall.com/docs/api)
for different MTG card types. These schemas serve as the source of truth for the
`cards` database table definition.

## Schema Files

| File | Card Type | Example Card |
|------|-----------|-------------|
| `cards_artifacts.json` | Artifact | Mox Jasper |
| `cards_creatures.json` | Creature | Ureni of the Unwritten |
| `cards_enchanment.json` | Enchantment | Dracogenesis |
| `cards_instants.json` | Instant | Swan Song |
| `cards_lands.json` | Land | Haven of the Spirit Dragon |
| `cards_planeswalker.json` | Planeswalker | Sarkhan Unbroken |
| `cards_sorcery.json` | Sorcery | Cultivate |
| `sets.json` | Set | Tarkir: Dragonstorm |

## Column Presence by Card Type

The table below documents which columns from the combined `cards` table are present
in each card type's JSON schema. Columns marked with ✓ are present; empty cells
indicate the field is absent for that card type.

| Column | SQL Type | Artifact | Creature | Enchantment | Instant | Land | Planeswalker | Sorcery |
|--------|----------|:--------:|:--------:|:-----------:|:-------:|:----:|:------------:|:-------:|
| `id` | `TEXT PK` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `oracle_id` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `name` | `TEXT NOT NULL` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `lang` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `released_at` | `DATE` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `layout` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `mana_cost` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `cmc` | `REAL` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `type_line` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `oracle_text` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `flavor_text` | `TEXT` | ✓ | | ✓ | ✓ | | | ✓ |
| `power` | `TEXT` | | ✓ | | | | | |
| `toughness` | `TEXT` | | ✓ | | | | | |
| `loyalty` | `TEXT` | | | | | | ✓ | |
| `colors` | `TEXT[]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `color_identity` | `TEXT[]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `keywords` | `TEXT[]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `produced_mana` | `TEXT[]` | ✓ | | | | ✓ | ✓ | |
| `all_parts` | `JSONB` | | | | ✓ | | ✓ | |
| `legalities` | `JSONB` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `games` | `TEXT[]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `reserved` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `foil` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `nonfoil` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `finishes` | `TEXT[]` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `set_code` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `set_name` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `set_type` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `collector_number` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `digital` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `rarity` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `oversized` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `promo` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `promo_types` | `TEXT[]` | | | | | | | ✓ |
| `reprint` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `variation` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `booster` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `full_art` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `textless` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `story_spotlight` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `border_color` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `frame` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `frame_effects` | `TEXT[]` | ✓ | ✓ | ✓ | | | | |
| `security_stamp` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| `highres_image` | `BOOLEAN` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `image_status` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `image_uris` | `JSONB` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `artist` | `TEXT` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `edhrec_rank` | `INTEGER` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `penny_rank` | `INTEGER` | | | ✓ | ✓ | ✓ | ✓ | ✓ |
| `prices` | `JSONB` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Omitted Scryfall Fields

The following fields from the Scryfall API are intentionally **not** stored in the
database because they are either API metadata, internal identifiers, or transient
data not relevant to card similarity search:

| Omitted Field | Reason |
|---------------|--------|
| `object` | Always `"card"` — no information value |
| `multiverse_ids`, `mtgo_id`, `mtgo_foil_id`, `arena_id` | External platform IDs |
| `tcgplayer_id`, `cardmarket_id` | Marketplace IDs |
| `resource_id` | Internal Scryfall identifier |
| `uri`, `scryfall_uri` | API self-links |
| `set_id`, `set_uri`, `set_search_uri`, `scryfall_set_uri` | Set API metadata |
| `rulings_uri`, `prints_search_uri` | API navigation links |
| `card_back_id` | Internal card back reference |
| `artist_ids`, `illustration_id` | Internal artist/illustration IDs |
| `game_changer` | Scryfall-specific flag |
| `preview` | Transient preview/spoiler metadata |
| `related_uris`, `purchase_uris` | External shopping/reference links |

## JSON-to-SQL Field Mapping

Some Scryfall JSON field names differ from the SQL column names:

| Scryfall JSON Field | SQL Column | Reason |
|---------------------|-----------|--------|
| `set` | `set_code` | `SET` is a SQL reserved word |

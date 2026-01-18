from database.db import get_cursor

with get_cursor() as cur:
    cur.execute("""
    INSERT INTO cards (id, name, mana_cost, cmc, colors, ...)
    VALUES ($1, $2, $3, $4, $5, ...)
    ON CONFLICT (id) DO UPDATE SET ...
""", (
    "2c6d7ee7-b635-584f-b96f-59979998134f",  # $1 - id
    "Lumra, Bellow of the Woods",             # $2 - name
    "{4}{G}{G}",                               # $3 - mana_cost
    6.0,                                       # $4 - cmc
    ["G"],                                     # $5 - colors (array)
    ["G"],                                     # $6 - color_identity
    "Legendary Creature — Elemental Bear",    # $7 - type
    ["Legendary"],                             # $8 - supertypes
    ["Creature"],                              # $9 - types
    ["Elemental", "Bear"],                     # $10 - subtypes
    "Mythic",                                  # $11 - rarity
    "BLB",                                     # $12 - set_code
    "Bloomburrow",                             # $13 - set_name
    "Vigilance, reach\n...",                   # $14 - text
    "Matt Stewart",                            # $15 - artist
    "183",                                     # $16 - number
    "*",                                       # $17 - power
    "*",                                       # $18 - toughness
    "normal",                                  # $19 - layout
    ["f4816114...", "7d95bac2..."],           # $20 - variations
    ["BLB"]                                    # $21 - printings
))
    print(f"Inserted/Updated card Lumra, Bellow of the Woods")
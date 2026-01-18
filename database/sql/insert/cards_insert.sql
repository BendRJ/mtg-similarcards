INSERT INTO cards (
    id,
    name,
    mana_cost,
    cmc,
    colors,
    color_identity,
    type,
    supertypes,
    types,
    subtypes,
    rarity,
    set_code,
    set_name,
    text,
    artist,
    number,
    power,
    toughness,
    layout,
    variations,
    printings
) VALUES (
    $1,  -- id
    $2,  -- name
    $3,  -- mana_cost
    $4,  -- cmc
    $5,  -- colors
    $6,  -- color_identity
    $7,  -- type
    $8,  -- supertypes
    $9,  -- types
    $10, -- subtypes
    $11, -- rarity
    $12, -- set_code
    $13, -- set_name
    $14, -- text
    $15, -- artist
    $16, -- number
    $17, -- power
    $18, -- toughness
    $19, -- layout
    $20, -- variations
    $21  -- printings
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    mana_cost = EXCLUDED.mana_cost,
    cmc = EXCLUDED.cmc,
    colors = EXCLUDED.colors,
    color_identity = EXCLUDED.color_identity,
    type = EXCLUDED.type,
    supertypes = EXCLUDED.supertypes,
    types = EXCLUDED.types,
    subtypes = EXCLUDED.subtypes,
    rarity = EXCLUDED.rarity,
    set_code = EXCLUDED.set_code,
    set_name = EXCLUDED.set_name,
    text = EXCLUDED.text,
    artist = EXCLUDED.artist,
    number = EXCLUDED.number,
    power = EXCLUDED.power,
    toughness = EXCLUDED.toughness,
    layout = EXCLUDED.layout,
    variations = EXCLUDED.variations,
    printings = EXCLUDED.printings;
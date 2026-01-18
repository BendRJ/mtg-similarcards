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
    %s,  -- id
    %s,  -- name
    %s,  -- mana_cost
    %s,  -- cmc
    %s,  -- colors
    %s,  -- color_identity
    %s,  -- type
    %s,  -- supertypes
    %s,  -- types
    %s,  -- subtypes
    %s,  -- rarity
    %s,  -- set_code
    %s,  -- set_name
    %s,  -- text
    %s,  -- artist
    %s,  -- number
    %s,  -- power
    %s,  -- toughness
    %s,  -- layout
    %s,  -- variations
    %s   -- printings
)
ON CONFLICT (id) DO UPDATE SET --prevents duplicate entries based on primary key 'id'
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

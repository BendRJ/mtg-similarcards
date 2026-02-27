INSERT INTO cards (
    id,
    oracle_id,
    name,
    lang,
    released_at,
    layout,
    mana_cost,
    cmc,
    type_line,
    oracle_text,
    flavor_text,
    power,
    toughness,
    loyalty,
    colors,
    color_identity,
    keywords,
    produced_mana,
    all_parts,
    legalities,
    games,
    reserved,
    foil,
    nonfoil,
    finishes,
    set_code,
    set_name,
    set_type,
    collector_number,
    digital,
    rarity,
    oversized,
    promo,
    promo_types,
    reprint,
    variation,
    booster,
    full_art,
    textless,
    story_spotlight,
    border_color,
    frame,
    frame_effects,
    security_stamp,
    highres_image,
    image_status,
    image_uris,
    artist,
    edhrec_rank,
    penny_rank,
    prices
) VALUES (
    %s,  -- id
    %s,  -- oracle_id
    %s,  -- name
    %s,  -- lang
    %s,  -- released_at
    %s,  -- layout
    %s,  -- mana_cost
    %s,  -- cmc
    %s,  -- type_line
    %s,  -- oracle_text
    %s,  -- flavor_text
    %s,  -- power
    %s,  -- toughness
    %s,  -- loyalty
    %s,  -- colors
    %s,  -- color_identity
    %s,  -- keywords
    %s,  -- produced_mana
    %s,  -- all_parts
    %s,  -- legalities
    %s,  -- games
    %s,  -- reserved
    %s,  -- foil
    %s,  -- nonfoil
    %s,  -- finishes
    %s,  -- set_code
    %s,  -- set_name
    %s,  -- set_type
    %s,  -- collector_number
    %s,  -- digital
    %s,  -- rarity
    %s,  -- oversized
    %s,  -- promo
    %s,  -- promo_types
    %s,  -- reprint
    %s,  -- variation
    %s,  -- booster
    %s,  -- full_art
    %s,  -- textless
    %s,  -- story_spotlight
    %s,  -- border_color
    %s,  -- frame
    %s,  -- frame_effects
    %s,  -- security_stamp
    %s,  -- highres_image
    %s,  -- image_status
    %s,  -- image_uris
    %s,  -- artist
    %s,  -- edhrec_rank
    %s,  -- penny_rank
    %s   -- prices
)
ON CONFLICT (id) DO UPDATE SET
    oracle_id = EXCLUDED.oracle_id,
    name = EXCLUDED.name,
    lang = EXCLUDED.lang,
    released_at = EXCLUDED.released_at,
    layout = EXCLUDED.layout,
    mana_cost = EXCLUDED.mana_cost,
    cmc = EXCLUDED.cmc,
    type_line = EXCLUDED.type_line,
    oracle_text = EXCLUDED.oracle_text,
    flavor_text = EXCLUDED.flavor_text,
    power = EXCLUDED.power,
    toughness = EXCLUDED.toughness,
    loyalty = EXCLUDED.loyalty,
    colors = EXCLUDED.colors,
    color_identity = EXCLUDED.color_identity,
    keywords = EXCLUDED.keywords,
    produced_mana = EXCLUDED.produced_mana,
    all_parts = EXCLUDED.all_parts,
    legalities = EXCLUDED.legalities,
    games = EXCLUDED.games,
    reserved = EXCLUDED.reserved,
    foil = EXCLUDED.foil,
    nonfoil = EXCLUDED.nonfoil,
    finishes = EXCLUDED.finishes,
    set_code = EXCLUDED.set_code,
    set_name = EXCLUDED.set_name,
    set_type = EXCLUDED.set_type,
    collector_number = EXCLUDED.collector_number,
    digital = EXCLUDED.digital,
    rarity = EXCLUDED.rarity,
    oversized = EXCLUDED.oversized,
    promo = EXCLUDED.promo,
    promo_types = EXCLUDED.promo_types,
    reprint = EXCLUDED.reprint,
    variation = EXCLUDED.variation,
    booster = EXCLUDED.booster,
    full_art = EXCLUDED.full_art,
    textless = EXCLUDED.textless,
    story_spotlight = EXCLUDED.story_spotlight,
    border_color = EXCLUDED.border_color,
    frame = EXCLUDED.frame,
    frame_effects = EXCLUDED.frame_effects,
    security_stamp = EXCLUDED.security_stamp,
    highres_image = EXCLUDED.highres_image,
    image_status = EXCLUDED.image_status,
    image_uris = EXCLUDED.image_uris,
    artist = EXCLUDED.artist,
    edhrec_rank = EXCLUDED.edhrec_rank,
    penny_rank = EXCLUDED.penny_rank,
    prices = EXCLUDED.prices;

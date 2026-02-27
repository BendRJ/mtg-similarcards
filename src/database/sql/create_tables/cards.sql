CREATE TABLE IF NOT EXISTS cards (
    -- Identity
    id TEXT PRIMARY KEY,
    oracle_id TEXT,
    name TEXT NOT NULL,
    lang TEXT,
    released_at DATE,
    layout TEXT,

    -- Mana & Cost
    mana_cost TEXT,
    cmc REAL,

    -- Type & Rules
    type_line TEXT,
    oracle_text TEXT,
    flavor_text TEXT,

    -- Combat Stats (creatures)
    power TEXT,
    toughness TEXT,

    -- Planeswalker
    loyalty TEXT,

    -- Colors & Keywords
    colors TEXT[],
    color_identity TEXT[],
    keywords TEXT[],
    produced_mana TEXT[],

    -- Related Cards (tokens, combo pieces)
    all_parts JSONB,

    -- Legality & Availability
    legalities JSONB,
    games TEXT[],
    reserved BOOLEAN NOT NULL DEFAULT FALSE,
    foil BOOLEAN NOT NULL DEFAULT FALSE,
    nonfoil BOOLEAN NOT NULL DEFAULT FALSE,
    finishes TEXT[],

    -- Set Info
    set_code TEXT,
    set_name TEXT,
    set_type TEXT,
    collector_number TEXT,
    digital BOOLEAN NOT NULL DEFAULT FALSE,
    rarity TEXT,

    -- Card Properties
    oversized BOOLEAN NOT NULL DEFAULT FALSE,
    promo BOOLEAN NOT NULL DEFAULT FALSE,
    promo_types TEXT[],
    reprint BOOLEAN NOT NULL DEFAULT FALSE,
    variation BOOLEAN NOT NULL DEFAULT FALSE,
    booster BOOLEAN NOT NULL DEFAULT FALSE,
    full_art BOOLEAN NOT NULL DEFAULT FALSE,
    textless BOOLEAN NOT NULL DEFAULT FALSE,
    story_spotlight BOOLEAN NOT NULL DEFAULT FALSE,

    -- Visual & Frame
    border_color TEXT,
    frame TEXT,
    frame_effects TEXT[],
    security_stamp TEXT,
    highres_image BOOLEAN NOT NULL DEFAULT FALSE,
    image_status TEXT,
    image_uris JSONB,

    -- Artist
    artist TEXT,

    -- Rankings
    edhrec_rank INTEGER,
    penny_rank INTEGER,

    -- Pricing
    prices JSONB
);

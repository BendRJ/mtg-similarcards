CREATE TABLE IF NOT EXISTS sets (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    set_type TEXT,
    released_at DATE,
    card_count INTEGER,
    digital BOOLEAN NOT NULL DEFAULT FALSE,
    foil_only BOOLEAN NOT NULL DEFAULT FALSE,
    nonfoil_only BOOLEAN NOT NULL DEFAULT FALSE,
    icon_svg_uri TEXT
);
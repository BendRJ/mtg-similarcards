CREATE TABLE IF NOT EXISTS card_images (
    card_id      TEXT PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
    size         TEXT NOT NULL DEFAULT 'normal',   -- which Scryfall image_uris variant
    content_type TEXT,                             -- e.g. 'image/jpeg'
    source_url   TEXT,                             -- the image_uris entry that was fetched
    byte_size    INTEGER,                          -- length(image), for observability
    image        BYTEA NOT NULL,
    fetched_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

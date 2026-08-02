INSERT INTO card_images (
    card_id,
    size,
    content_type,
    source_url,
    byte_size,
    image
) VALUES (
    %s,  -- card_id
    %s,  -- size
    %s,  -- content_type
    %s,  -- source_url
    %s,  -- byte_size
    %s   -- image (bytes -> bytea)
)
ON CONFLICT (card_id) DO UPDATE SET
    size = EXCLUDED.size,
    content_type = EXCLUDED.content_type,
    source_url = EXCLUDED.source_url,
    byte_size = EXCLUDED.byte_size,
    image = EXCLUDED.image,
    fetched_at = now();

-- Cards most similar to %(card_id)s by cosine distance, one row per card (oracle_id),
-- each shown as its most recent embedded printing. The reference card and all its
-- reprints are excluded. The reference vector comes from any embedded printing of
-- the card, so an older printing without an embedding still works.
-- Column lists mirror SUMMARY_COLUMNS / COLLECTOR_ORDER / PLAYABLE in app/backend/queries.py.
WITH ref AS (
    SELECT COALESCE(oracle_id, id) AS card_key, embedding
    FROM cards
    WHERE COALESCE(oracle_id, id) = (SELECT COALESCE(oracle_id, id) FROM cards WHERE id = %(card_id)s)
      AND embedding IS NOT NULL
    ORDER BY released_at DESC NULLS LAST
    LIMIT 1
),
candidates AS (
    SELECT DISTINCT ON (COALESCE(c.oracle_id, c.id))
           c.id, c.name, c.mana_cost, c.type_line, c.colors, c.rarity, c.set_code,
           CASE WHEN EXISTS (SELECT 1 FROM card_images ci WHERE ci.card_id = c.id)
                THEN '/cards/' || c.id || '/image'
                ELSE c.image_uris->>'normal' END AS image_url,
           c.embedding <=> ref.embedding AS distance
    FROM cards c
    CROSS JOIN ref
    WHERE c.embedding IS NOT NULL
      AND COALESCE(c.oracle_id, c.id) <> ref.card_key
      AND COALESCE(c.layout, '') NOT IN ('token', 'double_faced_token', 'emblem', 'art_series')
      AND COALESCE(c.set_type, '') NOT IN ('token', 'memorabilia', 'minigame')
    ORDER BY COALESCE(c.oracle_id, c.id),
             c.released_at DESC NULLS LAST,
             NULLIF(regexp_replace(c.collector_number, '\D', '', 'g'), '')::numeric NULLS LAST,
             c.collector_number
)
SELECT * FROM candidates
ORDER BY distance
LIMIT %(limit)s;

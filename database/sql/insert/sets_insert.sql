INSERT INTO sets (
    code,
    name,
    type,
    release_date,
    online_only
) VALUES (
    $1,  -- code
    $2,  -- name
    $3,  -- type
    $4,  -- release_date
    $5   -- online_only
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name, -- Use the NEW name from INSERT
    type = EXCLUDED.type,
    release_date = EXCLUDED.release_date,
    online_only = EXCLUDED.online_only;
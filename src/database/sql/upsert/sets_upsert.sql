INSERT INTO sets (
    code,
    name,
    set_type,
    released_at,
    card_count,
    digital,
    foil_only,
    nonfoil_only,
    icon_svg_uri
) VALUES (
    %s,  -- code
    %s,  -- name
    %s,  -- set_type
    %s,  -- released_at
    %s,  -- card_count
    %s,  -- digital
    %s,  -- foil_only
    %s,  -- nonfoil_only
    %s   -- icon_svg_uri
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    set_type = EXCLUDED.set_type,
    released_at = EXCLUDED.released_at,
    card_count = EXCLUDED.card_count,
    digital = EXCLUDED.digital,
    foil_only = EXCLUDED.foil_only,
    nonfoil_only = EXCLUDED.nonfoil_only,
    icon_svg_uri = EXCLUDED.icon_svg_uri;

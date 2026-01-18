CREATE TABLE IF NOT EXISTS sets (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    release_date DATE,
    online_only BOOLEAN NOT NULL DEFAULT FALSE
);
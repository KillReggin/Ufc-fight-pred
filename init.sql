CREATE TABLE IF NOT EXISTS fighters (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    nickname TEXT,
    height TEXT,
    weight TEXT,
    reach TEXT,
    stance TEXT,
    wins INT,
    losses INT,
    draws INT,
    belt TEXT
);
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    points INTEGER DEFAULT 0
);

-- Outlets table
CREATE TABLE outlets (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    favicon_url TEXT,
    bias INTEGER CHECK (bias BETWEEN 1 AND 5),
    establishment INTEGER CHECK (establishment BETWEEN 1 AND 5)
);

-- Guesses table
CREATE TABLE guesses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    outlet_id INTEGER REFERENCES outlets(id) ON DELETE CASCADE,
    guessed_name TEXT,
    guessed_bias INTEGER,
    guessed_establishment INTEGER,
    correct BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Disputes table
CREATE TABLE disputes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    outlet_id INTEGER REFERENCES outlets(id) ON DELETE CASCADE,
    proposed_bias INTEGER CHECK (proposed_bias BETWEEN 1 AND 5),
    proposed_establishment INTEGER CHECK (proposed_establishment BETWEEN 1 AND 5),
    comment TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Article Submissions table
CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

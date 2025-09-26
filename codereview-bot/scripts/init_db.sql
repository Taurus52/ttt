-- Create database if not exists
-- Note: Run this with superuser privileges

-- Create database
CREATE DATABASE codereview_bot;

-- Connect to the database
\c codereview_bot;

-- Create tables (this will be handled by SQLAlchemy, but here's the schema for reference)

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT UNIQUE NOT NULL,
    tg_username VARCHAR(32),
    is_active BOOLEAN DEFAULT TRUE
);

-- Teams table  
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL
);

-- User-Team relationship
CREATE TABLE IF NOT EXISTS user_teams (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    UNIQUE(user_id, team_id)
);

-- Team leaders
CREATE TABLE IF NOT EXISTS team_leaders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER UNIQUE REFERENCES teams(id) ON DELETE CASCADE
);

-- Review cycles
CREATE TABLE IF NOT EXISTS review_cycles (
    id SERIAL PRIMARY KEY,
    team_id INTEGER UNIQUE REFERENCES teams(id) ON DELETE CASCADE,
    current_cycle JSONB NOT NULL DEFAULT '[]'::jsonb,
    current_index INTEGER DEFAULT 0 NOT NULL
);

-- Review requests
CREATE TABLE IF NOT EXISTS review_requests (
    id SERIAL PRIMARY KEY,
    author_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    reviewer_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    mr_links JSONB NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('assigned', 'approved', 'rework', 'escalated')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX idx_users_tg_id ON users(tg_id);
CREATE INDEX idx_review_requests_author ON review_requests(author_id);
CREATE INDEX idx_review_requests_reviewer ON review_requests(reviewer_id);
CREATE INDEX idx_review_requests_team ON review_requests(team_id);
CREATE INDEX idx_review_requests_status ON review_requests(status);
CREATE INDEX idx_review_requests_created ON review_requests(created_at);
-- Initialize rattgollama database with demo user
-- This file is automatically executed when PostgreSQL container starts

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles VARCHAR(100) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    s3_key VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    vector_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Valid bcrypt hash for password 'admin'
INSERT INTO users (username, password_hash, roles, created_at) 
VALUES ('admin', '$2b$12$qtE5ssRlmMBWvQi3Z3Jf4unO8MgLzKjNilSXOxZCuI9NIlWrYFIve', 'admin', NOW())
ON CONFLICT (username) DO NOTHING;

-- Ensure sequence is set correctly (in case of manual IDs)
SELECT setval(pg_get_serial_sequence('users','id'), COALESCE(MAX(id), 1)) FROM users;

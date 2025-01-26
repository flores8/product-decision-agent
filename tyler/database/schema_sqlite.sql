-- Tyler database schema for SQLite
-- Run this script to create the required tables in your SQLite database

CREATE TABLE threads (
    id VARCHAR(255) PRIMARY KEY,
    data JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- SQLite trigger for updated_at
CREATE TRIGGER update_threads_updated_at
    AFTER UPDATE ON threads
    FOR EACH ROW
    BEGIN
        UPDATE threads SET updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.id;
    END; 
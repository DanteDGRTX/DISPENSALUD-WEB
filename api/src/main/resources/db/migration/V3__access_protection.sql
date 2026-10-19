ALTER TABLE auth_sessions ADD COLUMN last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP;
CREATE TABLE login_attempts (
    identity_hash VARCHAR(64) PRIMARY KEY,
    attempts INTEGER NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX login_attempts_expiry_idx ON login_attempts(expires_at);
